#!/bin/bash
# Phase 5: Create IAM Execution Role for MediBook Lambdas
# Role Name: medibook-lambda-role

ROLE_NAME="medibook-lambda-role"
POLICY_NAME="medibook-lambda-permissions"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Phase 5: Creating IAM Role '$ROLE_NAME' ==="

# 1. Create Role if it doesn't exist
if aws iam get-role --role-name "$ROLE_NAME" 2>/dev/null; then
    echo "Role '$ROLE_NAME' already exists. Skipping role creation."
else
    echo "Creating IAM role '$ROLE_NAME'..."
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file://"$SCRIPT_DIR/lambda_trust_policy.json" \
        --description "Least-privilege role for MediBook Lambda functions"
fi

# 2. Attach AWSLambdaBasicExecutionRole managed policy
echo "Attaching AWSLambdaBasicExecutionRole..."
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

# 3. Attach Inline Least-Privilege Policy
echo "Putting inline policy '$POLICY_NAME'..."
aws iam put-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-name "$POLICY_NAME" \
    --policy-document file://"$SCRIPT_DIR/medibook_lambda_policy.json"

echo "Waiting 10 seconds for IAM role propagation..."
sleep 10

echo "=== IAM Role Created & Configured Successfully ==="
aws iam get-role --role-name "$ROLE_NAME" --query "Role.[RoleName,Arn]" --output table
