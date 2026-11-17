# Architecture Decision Record (ADR)

## ADR-001 — Combined React/Flask deployment

**Decision:** Build the React SPA and package static assets beside a Python Flask API in one Elastic Beanstalk Python environment.  
**Reason:** At startup scale this avoids a second load balancer/instance fleet, gives a single origin and common health/scaling controls, and satisfies the assignment's React-on-Beanstalk requirement. The React JavaScript itself runs in the visitor's browser.  
**Trade-off:** Frontend and backend share deployment and scaling cycles; a future service boundary may be preferable when workloads or teams diverge.

## ADR-002 — Private instances and private RDS

**Decision:** Public ALB across two public subnets; private EB EC2 fleet in two app subnets; isolated RDS subnet pair with no default internet route and SG 5432 only from app SG.  
**Reason:** Public reachability exists only through CloudFront → load balancer; database and instances are never directly exposed.  
**Trade-off:** NAT costs money; the demo's single NAT is an AZ-level egress dependency. Use dual NAT for production and consider VPC endpoints if API traffic justifies them.

## ADR-003 — Dynamic versus cacheable paths

**Decision:** CloudFront caching disabled for HTML and API. Only hashed `/assets/*` and private `/images/*` receive long-lived caching.  
**Reason:** It prevents stale personalized/dynamic responses while still improving global asset performance.  
**Trade-off:** HTML/API remain Region-bound and pay round-trip origin latency; add safe response-specific caching later with measured requirements.

## ADR-004 — Immutable web recovery and data snapshots

**Decision:** Keep application releases as versioned S3 zips; recreate EB/EC2 from source and CFN. Use RDS automated backups and deletion snapshots for stateful recovery.  
**Reason:** Web nodes are disposable; backups of mutable instance disks do not align with an Auto Scaling architecture.  
**Trade-off:** Application redeploy is automatable; RDS restore and cutover are runbook-driven, not seamless or instantaneous. Cross-Region disaster recovery is a future extension.

## ADR-005 — Gzip activity stream to CSV

**Decision:** CloudWatch JSON request events → Kinesis Data Streams → Firehose Lambda transform → batched S3 CSV → Athena, with direct CloudWatch metrics/dashboard.  
**Reason:** Satisfies stream, CSV export, SQL analysis and visual display independently. Ingestion and delivery are buffered and recoverable within service retention.  
**Trade-off:** Multiple managed services increase steady-state cost; a light alternative is CloudWatch Logs Insights with periodic export for smaller workloads. This reference prioritizes the assignment's explicit streaming requirement.

## ADR-006 — GitHub OIDC with scoped `master` trust

**Decision:** AWS IAM role trusts GitHub OIDC tokens only for the named owner/repo on the `master` branch; no GitHub-held AWS access keys.  
**Reason:** Short-lived credentials and scoped trust are safer than long-lived keys in CI.  
**Trade-off:** The account-wide GitHub OIDC provider must be created once, and branch protection/approvals need to be configured in GitHub.

## ADR-007 — Certificate-dependent production security

**Decision:** Demonstration supports CloudFront's managed viewer HTTPS hostname with an HTTP ALB origin; production parameters require custom origin domain and ACM TLS certificate, plus a custom site domain and us-east-1 viewer certificate.  
**Reason:** An ALB-generated hostname does not carry an ACM certificate for a domain you own.  
**Trade-off:** TLS termination at the ALB still leaves HTTP on the trusted ALB→EC2 link; stronger control families require TLS targets as well. Production WAF, detailed audit trails and a verified security baseline are follow-on gates.
