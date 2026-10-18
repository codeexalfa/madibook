#!/bin/bash
# Phase 3: Create SQS Queue for MediBook in us-east-1
# Queue: medibook-booking-events (Standard Queue)

REGION="us-east-1"
QUEUE_NAME="medibook-booking-events"

echo "=== Phase 3: Creating SQS Queue ==="

# Check if queue already exists
QUEUE_URL=$(aws sqs get-queue-url --queue-name "$QUEUE_NAME" --region "$REGION" --query "QueueUrl" --output text 2>/dev/null)

if [ -n "$QUEUE_URL" ]; then
    echo "Queue '$QUEUE_NAME' already exists: $QUEUE_URL"
else
    echo "Creating queue '$QUEUE_NAME'..."
    QUEUE_URL=$(aws sqs create-queue \
        --queue-name "$QUEUE_NAME" \
        --attributes VisibilityTimeout=30,MessageRetentionPeriod=345600 \
        --region "$REGION" \
        --query "QueueUrl" \
        --output text)
    echo "Queue created: $QUEUE_URL"
fi

echo "=== SQS Queue Details ==="
aws sqs get-queue-attributes \
    --queue-url "$QUEUE_URL" \
    --attribute-names QueueArn ApproximateNumberOfMessages \
    --region "$REGION"
