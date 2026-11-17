# LMS Evidence Capture Guide

The original project asks for **configured-service screenshots**, a **PNG architecture image**, the **S3 bucket path for uploaded images**, and a document uploaded to LMS. This package contains the PNG diagrams and a private S3 upload script. **Actual service screenshots and URL values cannot be generated without deploying into the AWS account**; collect them after following the README.

## Capture sequence (use real AWS console screenshots)

| No. | Screenshot to take | What must be visible | Suggested file name |
|---|---|---|---|
| 01 | CloudFormation stack `atlas-demo` Resources | Stack status, resource IDs, timestamp | `01-cloudformation.png` |
| 02 | VPC > Subnets | Six subnets and AZ placement (hide account details) | `02-subnets.png` |
| 03 | VPC > Route tables | Public IGW route, app NAT route, isolated DB routes | `03-route-tables.png` |
| 04 | EC2 > Security Groups | ALB CloudFront prefix list and DB ingress from app SG | `04-security-groups.png` |
| 05 | Elastic Beanstalk > Environment | Green enhanced health and deployed version | `05-beanstalk.png` |
| 06 | EC2 Auto Scaling group | Min 2, desired 2, max 4 | `06-autoscaling.png` |
| 07 | EC2 > Load Balancers/Target Groups | Target health and `/health` check | `07-alb-health.png` |
| 08 | RDS > Databases | No public access, encryption, Multi-AZ and backups | `08-rds-security.png` |
| 09 | S3 > image bucket | Object `images/atlas-banner.png`, Block Public Access | `09-private-images.png` |
| 10 | CloudFront > Distribution | `/images/*` OAC S3 behavior, app origin and cache rules | `10-cloudfront.png` |
| 11 | GitHub Actions | `master` commit deployed successfully through OIDC | `11-cicd.png` |
| 12 | CloudWatch Logs and Kinesis | JSON activity events and Kinesis stream | `12-activity-stream.png` |
| 13 | Amazon Data Firehose and S3 | Delivery stream and `.csv` objects in activity/ | `13-csv-s3.png` |
| 14 | CloudWatch dashboard | Traffic, 5xx and p95 latency charts | `14-dashboard.png` |
| 15 | Athena query | Hourly requests/5xx/latency from CSV dataset | `15-athena.png` |
| 16 | Backup/recovery | RDS automated backups or snapshot and EB app versions | `16-backups.png` |

### URLs and identifiers to put in the final document

```text
AWS Region: ______________
CloudFormation stack: ______________
CloudFront website URL: ______________
S3 bucket name (images): ______________
Private S3 URI: s3://<BUCKET>/images/atlas-banner.png
Public image delivery URL: https://<CLOUDFRONT_DOMAIN>/images/atlas-banner.png
Elastic Beanstalk environment: ______________
RDS DB instance / engine: ______________
Kinesis stream: ______________
Analytics S3 URI: s3://<ANALYTICS_BUCKET>/activity/
CloudWatch dashboard: ______________
Source commit SHA / deployed EB version: ______________
Recovery exercise date/results: ______________
```

### Evidence standards

- Preserve the service, date, resource status and relevant configuration in each screenshot.
- Mask account numbers, names, internal identifiers and any sensitive data that the LMS does not require. **Never screenshot secrets, passwords, session tokens or access keys.**
- Demonstrate success by conducting tests, not merely showing that the resource exists.
- Do not insert illustrative diagrams where the assignment specifically asks for actual deployment evidence.
- Archive the report and screenshots in the evidence folder outside the public GitHub repository if they contain operational metadata.
