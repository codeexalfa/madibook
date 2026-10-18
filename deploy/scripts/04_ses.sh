#!/bin/bash
# Phase 4: Configure Amazon SES Email Verification in us-east-1
# Email: freelancerahim50@gmail.com

REGION="us-east-1"
EMAIL="freelancerahim50@gmail.com"

echo "=== Phase 4: Verifying Email Identity in Amazon SES ==="

# Trigger email verification
echo "Sending verification email to: $EMAIL..."
aws ses verify-email-identity --email-address "$EMAIL" --region "$REGION"

echo "Checking verification status..."
aws ses get-identity-verification-attributes \
    --identities "$EMAIL" \
    --region "$REGION"
