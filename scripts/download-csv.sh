#!/usr/bin/env bash
set -euo pipefail
: "${REGION:?Set REGION}"
STACK_NAME="${STACK_NAME:-atlas-demo}"
BUCKET="$(aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK_NAME" \
 --query 'Stacks[0].Outputs[?OutputKey==`AnalyticsBucketName`].OutputValue | [0]' --output text)"
mkdir -p analytics/downloads
aws s3 sync "s3://${BUCKET}/activity/" analytics/downloads/ \
  --region "$REGION" --exclude '*' --include '*.csv'
find analytics/downloads -name '*.csv' -type f -print
