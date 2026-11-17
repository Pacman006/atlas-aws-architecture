#!/usr/bin/env bash
set -euo pipefail
# Required inputs: REGION REPOSITORY_FULL_NAME. Optional PROJECT_NAME, STAGE and TLS parameters.
: "${REGION:?Set REGION (for example ap-south-1)}"
: "${REPOSITORY_FULL_NAME:?Set REPOSITORY_FULL_NAME owner/repo}"
PROJECT_NAME="${PROJECT_NAME:-atlas}"
STAGE="${STAGE:-demo}"
STACK_NAME="${PROJECT_NAME}-${STAGE}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
PARTITION="$(aws sts get-caller-identity --query Arn --output text | cut -d: -f2)"
OIDC_ARN="arn:${PARTITION}:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
aws iam get-open-id-connect-provider --open-id-connect-provider-arn "$OIDC_ARN" >/dev/null || {
  echo "Run scripts/bootstrap-oidc.sh first." >&2; exit 1;
}
PREFIX_LIST="$(aws ec2 describe-managed-prefix-lists --region "$REGION" \
  --filters Name=prefix-list-name,Values=com.amazonaws.global.cloudfront.origin-facing \
  --query 'PrefixLists[0].PrefixListId' --output text)"
[[ "$PREFIX_LIST" == pl-* ]] || { echo 'CloudFront prefix list not found in this Region' >&2; exit 1; }
STACK="$(aws elasticbeanstalk list-available-solution-stacks --region "$REGION" \
  --query "SolutionStacks[?contains(@, 'Python 3.13') && contains(@, 'Amazon Linux 2023')] | [0]" --output text)"
[[ "$STACK" != 'None' && -n "$STACK" ]] || { echo 'No Python 3.13 AL2023 solution stack in this Region' >&2; exit 1; }

if [[ -n "${ORIGIN_DOMAIN_NAME:-}" && -z "${ORIGIN_ACM_CERT_ARN:-}" ]] || \
   [[ -n "${SITE_DOMAIN_NAME:-}" && -z "${CLOUDFRONT_ACM_CERT_ARN:-}" ]]; then
  echo 'Origin/site domain requires the corresponding validated ACM certificate ARN.' >&2; exit 1
fi
if [[ "$STAGE" == production ]]; then
  DUAL_NAT=true
  DB_MULTI_AZ=true
  DB_DELETION_PROTECTION=true
  : "${ORIGIN_DOMAIN_NAME:?Production requires ORIGIN_DOMAIN_NAME}"
  : "${ORIGIN_ACM_CERT_ARN:?Production requires ORIGIN_ACM_CERT_ARN}"
  : "${SITE_DOMAIN_NAME:?Production requires SITE_DOMAIN_NAME}"
  : "${CLOUDFRONT_ACM_CERT_ARN:?Production requires CLOUDFRONT_ACM_CERT_ARN}"
fi
ARGS=(
  "ProjectName=$PROJECT_NAME" "Stage=$STAGE" "RepositoryFullName=$REPOSITORY_FULL_NAME"
  "SolutionStackName=$STACK" "GitHubOIDCProviderArn=$OIDC_ARN" "CloudFrontPrefixListId=$PREFIX_LIST"
  "DualNAT=${DUAL_NAT:-false}" "DBMultiAZ=${DB_MULTI_AZ:-true}"
  "DBDeletionProtection=${DB_DELETION_PROTECTION:-false}"
  "OriginDomainName=${ORIGIN_DOMAIN_NAME:-}" "OriginAcmCertificateArn=${ORIGIN_ACM_CERT_ARN:-}"
  "SiteDomainName=${SITE_DOMAIN_NAME:-}" "CloudFrontAcmCertificateArn=${CLOUDFRONT_ACM_CERT_ARN:-}"
  "PublicHostedZoneId=${PUBLIC_HOSTED_ZONE_ID:-}"
)
aws cloudformation deploy --region "$REGION" \
  --stack-name "$STACK_NAME" --template-file infra/main.yaml \
  --capabilities CAPABILITY_IAM --parameter-overrides "${ARGS[@]}" \
  --tags Project="$PROJECT_NAME" Stage="$STAGE" Owner=CloudFormation

echo
aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' --output table
