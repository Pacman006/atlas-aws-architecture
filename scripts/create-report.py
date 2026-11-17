#!/usr/bin/env python3
"""Author a deployer-readable PDF. Genuine AWS screenshots remain user-owned evidence."""
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, Preformatted
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'docs' / 'Atlas_Architecture_Implementation_Report.pdf'
NAVY=colors.HexColor('#14253d'); TEAL=colors.HexColor('#157b70'); PALE=colors.HexColor('#e9f4f3'); GREY=colors.HexColor('#5e6f80'); BORDER=colors.HexColor('#d2dce6')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Deck', fontName='Helvetica', fontSize=14, leading=21, textColor=GREY, spaceAfter=18))
styles.add(ParagraphStyle(name='TitleBig', fontName='Helvetica-Bold', fontSize=29, leading=34, textColor=NAVY, spaceAfter=15))
styles.add(ParagraphStyle(name='SectionA', fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=NAVY, spaceBefore=15, spaceAfter=8, keepWithNext=1))
styles.add(ParagraphStyle(name='SubA', fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=TEAL, spaceBefore=10, spaceAfter=5, keepWithNext=1))
styles.add(ParagraphStyle(name='BodyA', fontName='Helvetica', fontSize=9.1, leading=13.1, textColor=NAVY, spaceAfter=8))
styles.add(ParagraphStyle(name='TinyA', fontName='Helvetica', fontSize=7.2, leading=10.0, textColor=NAVY, spaceAfter=5))
styles.add(ParagraphStyle(name='SmallA', fontName='Helvetica', fontSize=8.1, leading=11.3, textColor=NAVY, spaceAfter=5))
styles.add(ParagraphStyle(name='NoteA', fontName='Helvetica-Oblique', fontSize=8.7, leading=12.3, textColor=GREY, spaceBefore=6, spaceAfter=7))
PAGE_W,PAGE_H=A4
WIDTH=PAGE_W-42*mm
story=[]
P=lambda x,style='BodyA':Paragraph(x,styles[style])

def add(text,style='BodyA'): story.append(P(text,style))
def sect(text): add(text,'SectionA')
def sub(text):add(text,'SubA')
def bullet(text): add('&#8226;  '+text)
def page():story.append(PageBreak())
def tbl(headers,rows,widths=None):
    data=[[P(escape(str(h)),'SmallA') for h in headers]]+[[P(str(v),'SmallA') for v in row] for row in rows]
    t=Table(data,colWidths=widths or [WIDTH/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([
      ('BACKGROUND',(0,0),(-1,0),PALE),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7fafd')]),
      ('LINEBELOW',(0,0),(-1,0),.7,TEAL),('LINEBELOW',(0,1),(-1,-1),.2,BORDER),
      ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),7),
      ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),7),
    ]))
    story.append(t);story.append(Spacer(1,7))

def img(fname,max_height=250):
    path=ROOT/'diagrams'/fname
    from PIL import Image as PILImage
    with PILImage.open(path) as im: w,h=im.size
    ratio=min(WIDTH/w,max_height/h)
    story.append(Image(str(path),width=w*ratio,height=h*ratio,hAlign='CENTER'))

def caption(text):add(text,'NoteA')

def footer(canvas,doc):
    canvas.saveState()
    canvas.setStrokeColor(BORDER);canvas.setLineWidth(.4)
    canvas.line(21*mm,18*mm,PAGE_W-21*mm,18*mm)
    canvas.setFont('Helvetica',7.3);canvas.setFillColor(GREY)
    canvas.drawString(21*mm,13.7*mm,'PROJECT ATLAS  /  ARCHITECTURE & IMPLEMENTATION')
    canvas.drawRightString(PAGE_W-21*mm,13.7*mm,f'Page {doc.page}')
    canvas.restoreState()

# Cover
story.append(Spacer(1,30*mm))
add('PROJECT ATLAS','TitleBig')
add('AWS Solutions Architect Project 2','Deck')
add('Secure networking  |  React + Python  |  Immutable delivery  |  Streamed analytics','BodyA')
story.append(Spacer(1,14*mm))
img('network.png',max_height=245)
story.append(Spacer(1,15*mm))
add('<b>Design baseline:</b> 17 November 2026  &nbsp;&nbsp; <b>Reference Region:</b> ap-south-1','BodyA')
add('<b>Status:</b> Code, architecture diagrams and runbooks generated and statically checked. AWS services are not deployed; real console screenshots and S3 links are pending account execution.','NoteA')
page()

sect('01 / Executive architecture')
add('The startup needs a globally reachable React application backed by Python, while protecting the database, keeping two instances online, scaling to four, and providing backup and operational evidence. Project Atlas packages the React build in one Python Elastic Beanstalk environment. The public entry path is CloudFront, followed by an Application Load Balancer and private EC2 nodes; PostgreSQL RDS is in isolated database subnets.')
add('The combined environment is a deliberate startup cost and maintenance choice. It removes a second application fleet and extra public API origin. The compiled React code executes in the browser; Elastic Beanstalk hosts and distributes the files and runs the Python API.')
sub('Requirement-to-resource mapping')
tbl(['Need','Implementation'],[
('Network isolation','Custom VPC, 6 subnets, restrictive security groups, no DB public route'),
('Automated React deployment','GitHub master → OIDC → S3 artifact → Beanstalk release'),
('Private image storage','S3 Block Public Access + CloudFront OAC for /images/*'),
('Backup and recovery','RDS 7-day backups and deletion snapshot; versioned web artifacts'),
('2–4 instances and failover','Beanstalk ASG, two Availability Zones, ALB health target'),
('CSV stream and reporting','CloudWatch Logs → Kinesis → Firehose/Lambda → S3 CSV → Athena'),
('Global cache','CloudFront caches /assets/* and /images/*; bypasses HTML/API')], [51*mm,WIDTH-51*mm])
add('The appendix repository includes working source files, template parameters, operations scripts, editable SVG and Python-rendered diagrams and a screenshot collection checklist.','NoteA')
page()

sect('02 / Request flow and system topology')
img('architecture.png',max_height=180)
caption('Detailed editable diagram also supplied as architecture.svg, render_blueprints.py and high-resolution PNG. Open the PNG for full-size annotations.')
sub('How a visitor request travels')
for t in [
'1. Browser connects to CloudFront using TLS 1.2 or later; the site enforces HTTPS redirects.',
'2. Path /images/* uses a separate S3 origin. CloudFront signs requests with Origin Access Control and S3 validates the distribution identity.',
'3. All other content goes to the Elastic Beanstalk ALB. The ALB SG accepts the regional CloudFront origin-facing prefix list, not unrestricted clients.',
'4. ALB chooses a healthy EC2 target. Nginx passes HTTP on the private instance to Gunicorn (port 8000), serving React assets and Flask endpoints.',
'5. Flask connects to RDS PostgreSQL on port 5432 using TLS and a password read at runtime from an RDS-managed Secrets Manager secret.'
]:bullet(t)
sub('Cache profiles')
tbl(['Path','Origin','Policy'],[
('/', 'Beanstalk ALB','Caching disabled; SPA HTML must stay fresh'),
('/api/*','Beanstalk ALB','Caching disabled; preserve request headers/cookies and query strings'),
('/assets/*','Beanstalk ALB','Managed optimized cache; hashed Vite assets'),
('/images/*','Private S3','OAC signed read with optimized caching')],[29*mm,45*mm,WIDTH-74*mm])
page()

sect('03 / Network placement and trust boundaries')
img('network.png',max_height=230)
sub('Connection details')
tbl(['Source → target','Protocol / port','Access rule'],[
('Viewer → CloudFront','HTTPS / TCP 443','CloudFront viewer certificate'),
('CloudFront → ALB','HTTPS 443 production; HTTP 80 demo','Origin-facing managed prefix list on ALB SG'),
('ALB → Beanstalk node','HTTP / TCP 80','App SG permits only ALB SG'),
('Nginx → Gunicorn','HTTP / TCP 8000','Local EC2 loopback / host'),
('Flask → RDS','PostgreSQL TLS / TCP 5432','DB SG permits only app SG; CA verified'),
('App → AWS APIs','HTTPS / TCP 443','Private subnets through NAT, IAM instance role')],[55*mm,40*mm,WIDTH-95*mm])
add('<b>Subnet scheme:</b> Public A/B: 10.42.0.0/24 and 10.42.1.0/24; App A/B: 10.42.10.0/24 and 10.42.11.0/24; Database A/B: 10.42.20.0/24 and 10.42.21.0/24. Database subnets have no 0.0.0.0/0 route.','TinyA')
page()

sect('04 / Secure delivery and CI/CD')
sub('Source-to-production lifecycle')
for t in [
'GitHub Actions triggers when a commit is pushed to the master branch. Repository access should be protected through review and branch protection.',
'GitHub OIDC issues short-lived credentials for a role whose trust policy restricts its subject to repo:OWNER/REPO:ref:refs/heads/master.',
'The pipeline runs syntax tests, installs dependencies, compiles React with Vite, downloads the official AWS RDS CA bundle, and builds an immutable ZIP.',
'It uploads the archive to a versioned S3 release bucket, creates an Elastic Beanstalk Application Version and deploys it.',
'On green health, it invalidates only / and /index.html in CloudFront. Long-lived hashed assets do not need per-release invalidation.'
]:bullet(t)
sub('TLS, credentials, and access protections')
add('Visitor TLS terminates at CloudFront; production origin TLS terminates at the ALB using a regional ACM certificate matching a dedicated public origin DNS name. A second ACM certificate issued in us-east-1 covers the site name at CloudFront. DB connections verify TLS certificates using an AWS RDS CA bundle included with the release. Secrets stay in Secrets Manager; instance and pipeline roles have separated permissions.')
add('<b>Deployment caveat:</b> The no-domain demo necessarily uses HTTP between CloudFront and the ALB. This is not an acceptable substitute where end-to-end TLS is mandated. WAF, incident alerts, CloudTrail trail and centralized organization governance are recommended production additions.','NoteA')
page()

sect('05 / Activity log stream and analytics')
img('telemetry.png',max_height=180)
for t in [
'Flask emits JSON for HTTP requests with timestamp, method, route, HTTP status, elapsed milliseconds and a request ID. Bodies, tokens and IP addresses are not included.',
'CloudWatch retains events for 30 days and pushes matching JSON event records to the encrypted Kinesis Data Stream.',
'Firehose reads Kinesis, invokes a Python Lambda to expand gzip CloudWatch envelopes and serialize clean CSV rows, then batches files to a private S3 bucket.',
'S3 CSV objects can be downloaded with the supplied script and queried by Athena using analytics/athena.sql.',
'The CloudWatch dashboard uses metric filters and a Logs Insights widget for requests, HTTP 5xx, latency and recent events.'
]:bullet(t)
sub('CSV output schema')
add('event_ts_utc, method, route, status, latency_ms, request_id, event_type. Files are headerless and can contain multiple rows; the schema file defines their order.')
sub('Data governance')
add('Application HTTP activity is not the same as every possible AWS infrastructure audit event. For wider incident and compliance investigations, configure CloudTrail, ALB access logs, database audit logs and retained security logs separately. This reference does not falsely claim those collectors are live.')
page()

sect('06 / Availability, recovery and costs')
tbl(['Failure','System response','Action'],[
('EC2 target unhealthy','ALB removes from healthy target set; ASG replaces nodes','Verify green targets and desired capacity'),
('Traffic increases','CPU-triggered step scaling from 2 up to 4','Inspect scaling activity, load-test and tune policy'),
('Bad application version','Immutable app releases and versioned source ZIP','Deploy known-good EB application version'),
('RDS data issue','7-day native backups and snapshot-on-delete','Restore to new instance; validate and plan DB endpoint cutover'),
('Single AZ loss','App fleet spans two AZs; optional dual NAT; RDS Multi-AZ','Test recovery duration and scale-up in remaining AZ'),
('Region loss','Not covered by single-Region design','Add and test cross-Region recovery before advertising it')],[37*mm,67*mm,WIDTH-104*mm])
add('<b>Cost drivers:</b> Running two EC2 nodes, RDS Multi-AZ, NAT gateways, CloudFront traffic, CloudWatch ingestion, Kinesis shards and Firehose/Lambda processing all bill independently. This design is not Free Tier. A budget and cost-anomaly alert should be added before production rollout.')
add('<b>Data recovery:</b> RDS deletion-protection for production, RDS automated backup/PITR plus deletion snapshot, versioned image and artifact buckets. The test RPO/RTO values in the runbook are objectives only until demonstrated by a dated restore exercise.','NoteA')
page()

sect('07 / Deployment and acceptance gates')
for t in [
'Install AWS CLI v2, configure an approved AWS identity, and create a GitHub repository using master as the deployment branch.',
'Run scripts/bootstrap-oidc.sh once per AWS account. The infrastructure deploy script locates the prefix list and supported Python 3.13 solution stack.',
'For a production profile, provision verified origin and site ACM certificates, Route53 records, dual NAT and DB deletion protection before deploying.',
'Run scripts/deploy-stack.sh. Save CloudFormation outputs for the six GitHub Actions repository variables.',
'Run npm install in frontend to create package-lock.json; commit and push master. Verify GitHub Actions and Beanstalk green health.',
'Run scripts/upload-images.sh, scripts/verify-deployment.sh, then scripts/download-csv.sh after traffic has been generated.',
'Use the screenshot checklist and capture actual service states, S3 URI, CloudFront image URL, Auto Scaling group capacity and analytics output.'
]:bullet(t)
sub('Acceptance evidence')
tbl(['Test','Expected result'],[
('curl https://CLOUDFRONT/health','200 OK from healthy Beanstalk app'),
('curl https://CLOUDFRONT/api/status','JSON showing API healthy and database reachable'),
('curl https://CLOUDFRONT/images/atlas-banner.png','200 image delivered by CloudFront; private S3 raw URL denied'),
('RDS / SG review','No public access; Postgres 5432 from app SG only'),
('Autoscaling check','Min 2 / Max 4 instances; two AZ subnets'),
('Data pipeline','Actual .csv objects in S3 with valid seven-column rows'),
('Failover exercise','ALB traffic continues on healthy target; ASG replaces missing target')],[65*mm,WIDTH-65*mm])
page()

sect('08 / LMS screenshot evidence worksheet')
add('The project brief requires screenshots of configured AWS resources. The diagrams here are design artifacts, not screenshots of a deployed account. Add real images with timestamps and redacted account metadata after successful deployment.','NoteA')
for label,desc in [
('01 - CloudFormation','Stack COMPLETE and Resources list'),
('02 - VPC','6 subnets, IGW/NAT routes and restrictive security groups'),
('03 - Beanstalk and EC2','Health Green, ASG min=2 / max=4, ALB target status'),
('04 - RDS','Private access, backups, encryption, Multi-AZ'),
('05 - S3 + CloudFront','Private image bucket, OAC and actual CloudFront PNG response'),
('06 - GitHub Actions','Successful master deployment, commit and release label'),
('07 - Logging and reporting','Kinesis/Firehose, real CSV in S3, Athena result, dashboard'),
('08 - Recovery evidence','Snapshot/backup and rollback or restore rehearsal')]:
    story.append(KeepTogether([P('<b>'+label+'</b>: '+desc,'SmallA'), Spacer(1,12)]))
add('<b>Actual image bucket URI:</b> s3://____________________/images/atlas-banner.png')
add('<b>Actual CloudFront PNG URL:</b> https://____________________/images/atlas-banner.png')
add('<b>Actual deployed EB version:</b> ____________________')
add('<b>Validation date / Region:</b> ____________________')
page()

sect('09 / Source map and engineering references')
for x in [
'CloudFormation: infra/main.yaml (all AWS resources, input parameters and output references)',
'Application: backend/application.py; backend/Procfile; backend/requirements.txt; frontend/src/main.jsx',
'CI/CD: .github/workflows/deploy.yml and scripts/bootstrap-oidc.sh',
'Operations: scripts/deploy-stack.sh, scripts/verify-deployment.sh and scripts/download-csv.sh',
'Analytics: analytics/athena.sql and the inline Firehose CSV transformer in infra/main.yaml',
'Diagrams: diagrams/render_blueprints.py and architecture/network/telemetry SVG + PNG exports',
'Recovery: docs/recovery-runbook.md and docs/architecture-decisions.md',
'Instruction and live evidence: README.md and docs/evidence-checklist.md',
]:bullet(x)
sub('AWS documentation used for technical verification')
for url in [
'https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/command-options-general.html',
'https://docs.aws.amazon.com/elasticbeanstalk/latest/platforms/platforms-supported.html',
'https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/python-configuration-procfile.html',
'https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html',
'https://docs.aws.amazon.com/vpc/latest/userguide/working-with-aws-managed-prefix-lists.html',
'https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/SubscriptionFilters.html',
'https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-kinesisfirehose-deliverystream.html',
]:add(escape(url),'TinyA')
add('Scope qualification: This dossier is a candidate technical implementation and validation guide. A successfully parsed CloudFormation file is not proof of API acceptance, live high availability, security approval or recoverability.','NoteA')

doc=SimpleDocTemplate(str(DEST),pagesize=A4,rightMargin=21*mm,leftMargin=21*mm,topMargin=19*mm,bottomMargin=23*mm,title='Project Atlas - AWS Architecture and Implementation',author='Project Atlas Engineering',subject='AWS Solutions Architect Project 2')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('Report saved:',DEST)
