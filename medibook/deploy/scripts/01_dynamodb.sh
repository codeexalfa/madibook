#!/bin/bash
# Phase 1: Create DynamoDB Tables for MediBook in us-east-1
# Region: us-east-1
# Billing: PAY_PER_REQUEST (On-Demand)

REGION="us-east-1"

echo "=== Phase 1: Creating DynamoDB Tables ==="

# 1. Create Appointments Table (PK: doctorId [S], SK: slotTime [S])
if aws dynamodb describe-table --table-name Appointments --region "$REGION" >/dev/null 2>&1; then
    echo "Table 'Appointments' already exists. Skipping."
else
    echo "Creating table 'Appointments'..."
    aws dynamodb create-table \
        --table-name Appointments \
        --attribute-definitions \
            AttributeName=doctorId,AttributeType=S \
            AttributeName=slotTime,AttributeType=S \
        --key-schema \
            AttributeName=doctorId,KeyType=HASH \
            AttributeName=slotTime,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION"
fi

# 2. Create Doctors Table (PK: doctorId [S])
if aws dynamodb describe-table --table-name Doctors --region "$REGION" >/dev/null 2>&1; then
    echo "Table 'Doctors' already exists. Skipping."
else
    echo "Creating table 'Doctors'..."
    aws dynamodb create-table \
        --table-name Doctors \
        --attribute-definitions \
            AttributeName=doctorId,AttributeType=S \
        --key-schema \
            AttributeName=doctorId,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION"
fi

# 3. Create Patients Table (PK: patientId [S])
if aws dynamodb describe-table --table-name Patients --region "$REGION" >/dev/null 2>&1; then
    echo "Table 'Patients' already exists. Skipping."
else
    echo "Creating table 'Patients'..."
    aws dynamodb create-table \
        --table-name Patients \
        --attribute-definitions \
            AttributeName=patientId,AttributeType=S \
        --key-schema \
            AttributeName=patientId,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION"
fi

echo "Waiting for tables to be ACTIVE..."
aws dynamodb wait table-exists --table-name Appointments --region "$REGION"
aws dynamodb wait table-exists --table-name Doctors --region "$REGION"
aws dynamodb wait table-exists --table-name Patients --region "$REGION"

echo "=== DynamoDB Tables Created Successfully ==="
aws dynamodb list-tables --region "$REGION"
