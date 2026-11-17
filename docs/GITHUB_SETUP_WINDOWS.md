# Publish Project Atlas to GitHub (Windows)

This guide uploads the **complete folder**, including the React UI, Flask API, CloudFormation, GitHub Actions workflow, vector/PNG diagrams and evidence checklist. It does not deploy AWS automatically until you configure the AWS environment.

## Step 1 — Download and unzip

Extract `Atlas_Project2_Full_Implementation_REBUILT.zip` into a convenient location, e.g. `C:\Users\YOUR_NAME\Documents\`. Open the directory named `atlas-aws-architecture` and verify you see `README.md`, `infra`, `frontend`, `backend`, `diagrams`, `docs` and `.github` (the last folder may be hidden in Explorer).

## Step 2 — Create an **empty** repository

Log into github.com, use **+ → New repository**, set the repository name to `atlas-aws-architecture`, enter a description such as "AWS startup reference architecture: React + Python API on Elastic Beanstalk", choose Public or Private, and click **Create repository**. Do **not** generate a README, .gitignore, or license (the source already contains a README and .gitignore). Copy the HTTPS remote URL from the Quick setup screen.

## Step 3 — Open Git Bash inside the extracted project root

In File Explorer, right-click in the `atlas-aws-architecture` folder → **Open Git Bash here** (or open Git Bash and `cd` to that folder). Check that Git is installed:

```bash
git --version
git status
```

If the folder has not been initialized as a Git repo, `git status` will say it is not a repository. That is expected.

## Step 4 — Optional recommended: create a reproducible frontend lockfile

With Node.js 22 and npm installed:

```bash
cd frontend
npm install
npm run build
cd ..
```

Commit the resulting `frontend/package-lock.json`. `node_modules` and `frontend/dist` are ignored. If you do not have Node yet, skip this step: the GitHub workflow can run `npm install` during its build, though a committed lockfile is preferable.

## Step 5 — Initialize and commit

Run in the root directory:

```bash
git init -b master
git add .
git status
git commit -m "Initial AWS Project Atlas architecture"
```

**Why `master`?** The project brief and `.github/workflows/deploy.yml` explicitly use `master`. Both the GitHub workflow trigger and AWS IAM trust are scoped to `refs/heads/master`.

If Git requests your identity, configure it using your own actual GitHub details:

```bash
git config --global user.name "YOUR DISPLAY NAME"
git config --global user.email "YOUR VERIFIED GITHUB EMAIL"
```

Then retry `git commit`. Avoid committing AWS credentials or `.env` files.

## Step 6 — Link GitHub and push

Replace `<YOUR_GITHUB_USERNAME>` with the actual owner of your repository:

```bash
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/atlas-aws-architecture.git
git remote -v
git push -u origin master
```

Git Credential Manager should open a browser sign-in if needed. If credentials fail, run `gh auth login` with GitHub CLI, choose GitHub.com → HTTPS → authenticate in browser → allow Git access; then retry the push. If `origin` already exists, use `git remote set-url origin <URL>` rather than adding a duplicate.

## Step 7 — Verify the files on GitHub

Refresh your repository page. Select the **master** branch. Verify:

- README renders the new system architecture diagram at the top.
- The three PNG files open under `diagrams/`; SVG files open too.
- `.github/workflows/deploy.yml` is present (Github hides folders beginning with a dot only in some local file browsers, not in repository listings).
- `infra/main.yaml`, application source and runbooks are available.
- Under **Actions**, the build/test job runs on pushes to `master`. If AWS repo variables are not configured, **AWS deployment is skipped**, rather than attempting to use non-existent credentials.

## Step 8 — Subsequent edits

```bash
git status
git add .
git commit -m "Update architecture documentation"
git push origin master
```

## Optional — Enable AWS deployment (this creates billable AWS resources)

Do **not** confuse publishing the repository with deploying the stack. The production deployment path requires a verified TLS domain/certificates and a review of costs and IAM permissions; demo mode has an **unencrypted CloudFront → ALB hop**, so treat it as a learning environment.

Using Git Bash + AWS CLI v2 configured for an AWS account with sufficient deployment permissions:

```bash
aws sts get-caller-identity
export REGION=ap-south-1
export REPOSITORY_FULL_NAME=<YOUR_GITHUB_USERNAME>/atlas-aws-architecture
bash scripts/bootstrap-oidc.sh
export PROJECT_NAME=atlas
export STAGE=demo
bash scripts/deploy-stack.sh
```

The stack outputs provide five values for GitHub, plus `AWS_REGION=ap-south-1`. In your GitHub repository navigate to **Settings → Secrets and variables → Actions → Variables → New repository variable** and add:

| Name | Source |
|---|---|
| `AWS_REGION` | Your chosen AWS region, e.g. `ap-south-1` |
| `AWS_ROLE_ARN` | `GithubDeployRoleArn` |
| `EB_APP` | `ElasticBeanstalkApplication` |
| `EB_ENV` | `ElasticBeanstalkEnvironment` |
| `ARTIFACT_BUCKET` | `ArtifactBucketName` |
| `CDN_DISTRIBUTION_ID` | `CDNDistributionId` |

Then go to **Actions → Build, test and deploy Atlas → Run workflow** and select `master`, or push another commit. The action uses OIDC to acquire **temporary AWS credentials**; no AWS access key or secret is needed in GitHub.

The initial CloudFormation stack and Elastic Beanstalk deployment must be validated in your own account. The local bundle does not contain real AWS screenshots, live DNS URLs, or proof of a successful AWS deployment.
