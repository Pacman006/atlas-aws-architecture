#!/usr/bin/env bash
set -euo pipefail
: "${REGION:?Set REGION}"
STACK_NAME="${STACK_NAME:-atlas-demo}"
BUCKET="$(aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK_NAME" \
 --query 'Stacks[0].Outputs[?OutputKey==`ImageBucketName`].OutputValue | [0]' --output text)"
CDN="$(aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK_NAME" \
 --query 'Stacks[0].Outputs[?OutputKey==`WebsiteURL`].OutputValue | [0]' --output text)"
aws s3 cp assets/ui/atlas-banner.png "s3://${BUCKET}/images/atlas-banner.png" \
 --region "$REGION" --content-type image/png --cache-control 'public,max-age=604800'
echo "Private bucket: s3://${BUCKET}/images/atlas-banner.png"
echo "Public CloudFront URL: ${CDN}/images/atlas-banner.png"
