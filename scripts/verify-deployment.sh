#!/usr/bin/env bash
set -euo pipefail
: "${REGION:?Set REGION}"
STACK_NAME="${STACK_NAME:-atlas-demo}"
lookup() { aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK_NAME" \
 --query "Stacks[0].Outputs[?OutputKey==\`$1\`].OutputValue | [0]" --output text; }
URL="$(lookup WebsiteURL)"
ENV="$(lookup ElasticBeanstalkEnvironment)"
echo "Checking ${URL}"
curl --fail --show-error --silent --location "${URL}/health"; echo
curl --fail --show-error --silent --location "${URL}/api/status"; echo
curl --fail --show-error --silent --location -I "${URL}/images/atlas-banner.png" | head -12
aws elasticbeanstalk describe-environments --region "$REGION" --environment-names "$ENV" \
 --query 'Environments[0].[EnvironmentName,Status,Health,VersionLabel]' --output table
