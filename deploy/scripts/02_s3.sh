#!/bin/bash
# Phase 2: Create S3 Buckets for MediBook in us-east-1
# Buckets:
# 1. medibook-referrals-40179-app (Private + CORS for presigned uploads)
# 2. medibook-website-40179-app (Private, Block Public Access ON)

REGION="us-east-1"
ACCOUNT_ID="355628740179"
SUFFIX="40179-app"

REFERRALS_BUCKET="medibook-referrals-${SUFFIX}"
WEBSITE_BUCKET="medibook-website-${SUFFIX}"

echo "=== Phase 2: Creating S3 Buckets ==="

# 1. Create Referral Bucket
if aws s3api head-bucket --bucket "$REFERRALS_BUCKET" 2>/dev/null; then
    echo "Bucket '$REFERRALS_BUCKET' already exists. Skipping creation."
else
    echo "Creating bucket '$REFERRALS_BUCKET'..."
    aws s3api create-bucket --bucket "$REFERRALS_BUCKET" --region "$REGION"
fi

# Enable Block Public Access on Referral Bucket
aws s3api put-public-access-block \
    --bucket "$REFERRALS_BUCKET" \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Set CORS on Referral Bucket
cat << 'EOF' > /tmp/referral-cors.json
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "HEAD"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag"]
    }
  ]
}
EOF

aws s3api put-bucket-cors --bucket "$REFERRALS_BUCKET" --cors-configuration file:///tmp/referral-cors.json
echo "Applied CORS configuration to '$REFERRALS_BUCKET'."

# 2. Create Website Bucket
if aws s3api head-bucket --bucket "$WEBSITE_BUCKET" 2>/dev/null; then
    echo "Bucket '$WEBSITE_BUCKET' already exists. Skipping creation."
else
    echo "Creating bucket '$WEBSITE_BUCKET'..."
    aws s3api create-bucket --bucket "$WEBSITE_BUCKET" --region "$REGION"
fi

# Enable Block Public Access on Website Bucket
aws s3api put-public-access-block \
    --bucket "$WEBSITE_BUCKET" \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

echo "=== S3 Buckets Configured Successfully ==="
aws s3 ls
