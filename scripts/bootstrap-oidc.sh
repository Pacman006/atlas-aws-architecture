#!/usr/bin/env bash
set -euo pipefail
# One-time AWS-account bootstrap: do not create duplicate GitHub OIDC providers.
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
PARTITION="$(aws sts get-caller-identity --query Arn --output text | cut -d: -f2)"
PROVIDER_ARN="arn:${PARTITION}:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
if aws iam get-open-id-connect-provider --open-id-connect-provider-arn "$PROVIDER_ARN" >/dev/null 2>&1; then
  echo "Existing provider: ${PROVIDER_ARN}"
else
  aws iam create-open-id-connect-provider \
    --url 'https://token.actions.githubusercontent.com' \
    --client-id-list sts.amazonaws.com >/dev/null
  echo "Created provider: ${PROVIDER_ARN}"
fi
printf '\nSet GitHubOIDCProviderArn=%s in the stack parameters.\n' "$PROVIDER_ARN"
