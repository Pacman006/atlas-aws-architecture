# Atlas Recovery Runbook

**Purpose.** Restore user access after app node failure, a bad release, an unavailable database, or wider regional failure. Service recovery is not considered proven until a dated restoration exercise completes.

## 1. Instance failure (expected automatic response)

1. Inspect Elastic Beanstalk **Health** and the ALB target group. The default process health endpoint is `/health`; a target that stops returning HTTP 200 becomes unhealthy.
2. Beanstalk/Auto Scaling should maintain a minimum desired size of two and replace an unhealthy EC2 instance. Do not manually terminate both instances.
3. Confirm that replacement node launches in a private application subnet, joins the target group and passes health checks. Check `GET /health`, `/api/status`, application events and recent CloudWatch request logs.
4. If a whole AZ fails, available app capacity may temporarily drop below two until nodes can launch in the remaining AZ. The two-AZ design reduces but does not eliminate interruption risk. A **single NAT demo** can also make app egress fail when its AZ disappears; production enables dual NAT.

## 2. Bad web release: restore prior immutable bundle

```bash
export REGION=ap-south-1
export EB_APP=atlas-demo
export EB_ENV=atlas-demo-web
aws elasticbeanstalk describe-application-versions --region "$REGION" \
  --application-name "$EB_APP" --query 'ApplicationVersions[*].[VersionLabel,DateCreated]' \
  --output table
# Choose a previously healthy VERSION_LABEL from recorded releases.
aws elasticbeanstalk update-environment --region "$REGION" \
  --environment-name "$EB_ENV" --version-label '<KNOWN_GOOD_VERSION_LABEL>'
```

After EB reports healthy, invalidate CloudFront `/` and `/index.html` and run the smoke tests. Record the incident, rollback commit and deployed version label. GitHub's next `master` push can redeploy; address the faulty commit before triggering it.

## 3. Database recovery

1. Determine failure type: connection/secret/SG error, storage issue, bad data change or RDS outage. The ALB health endpoint should continue serving frontend content even if DB readiness fails; `/api/status` will return 503.
2. For infrastructure/AZ faults, inspect RDS events and Multi-AZ state. RDS Multi-AZ failover manages standby promotion; clients may have brief connection errors and should retry idempotent reads.
3. For logical data corruption, choose a **point-in-time restore** (within available 7-day retention) or specific backup snapshot in RDS. A restore creates a new database instance and endpoint; it does not write over the original instance.
4. Validate the restored data in isolation and explicitly plan credentials, networking, DNS/application config cutover. CloudFormation owns `DB_HOST`, so do not make an undocumented manual setting change and leave infrastructure drift. A safe procedure is to deploy an approved updated CloudFormation version that references the restored DB, or rebuild the stack into a temporary environment with the restored DB reference.
5. Confirm `/api/catalog`, data consistency, application release version, logs, and request metrics before retiring the affected DB. Capture the recovery timestamps and screenshots.

**Note:** The provided main CloudFormation template provisions its own RDS instance. It does **not** contain an automated `RestoredDBInstanceIdentifier` switchover parameter. Database cutover after restore needs an additional reviewed change. Do not point the current stack at a replacement database without also updating the template and change records.

## 4. Region-wide disaster

Current design is **two-AZ within a single AWS Region**, not active-active or cross-Region DR. RDS backups and web bundles live in the primary Region by default. Cross-Region copy, key and bucket replication, secondary-region network, controlled DNS failover, and regular restore tests are required before claiming regional DR.

## 5. Recovery objectives (planning targets, not measured SLAs)

| Incident | Preliminary planning objective | Evidence required |
|---|---|---|
| Single instance failure | Typically minutes, subject to EC2/ASG launch time | ALB and ASG timestamps |
| Bad web release | Target under 30 minutes | EB release and CDN invalidation logs |
| RDS PITR | Target measured during rehearsal | Restore-to-new-DB timeline |
| Region failure | Not covered by deployed topology | Cross-Region DR design and tests |

## 6. Backup policy and immutable deployment

- **Web:** Git history + EB application versions and S3 artifact version history. Rebuild disposable EC2 nodes; do not treat per-node EBS snapshots as the primary web backup.
- **Database:** 7-day RDS automated backup with snapshot-on-delete and optional Multi-AZ. Set extended backup-retention, cross-Region copy and AWS Backup policies for regulated or more demanding RPO/RTO needs.
- **Assets:** S3 versioning, 90-day expiration of superseded versions in current template; add cross-Region replication for stronger recovery.
- **Analytics:** S3 data has a 90-day lifecycle for demonstrator economics; increase retention and secure governance before production adoption.
