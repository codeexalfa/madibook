#!/usr/bin/env bash
set -e
echo "Executing Phase 12: CloudWatch & SNS Setup..."
python "$(dirname "$0")/12_cloudwatch.py"
