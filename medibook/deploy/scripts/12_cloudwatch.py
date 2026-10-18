import boto3
import json
import os

AWS_REGION = "us-east-1"
ALARM_EMAIL = "rabbiraz123@gmail.com"
TOPIC_NAME = "medibook-alarms-topic"
ALARM_NAME = "MediBook-Lambda-Error-Alarm"
FUNCTION_NAME = "medibook-book-appointment"

def setup_cloudwatch_and_sns():
    print("=" * 60)
    print(" === Phase 12: Setting up SNS Topic & CloudWatch Alarm ===")
    print("=" * 60)
    
    sns = boto3.client("sns", region_name=AWS_REGION)
    cw = boto3.client("cloudwatch", region_name=AWS_REGION)
    logs = boto3.client("logs", region_name=AWS_REGION)
    
    # 1. Create or get SNS Topic
    print(f"Creating SNS topic '{TOPIC_NAME}'...")
    res = sns.create_topic(Name=TOPIC_NAME)
    topic_arn = res["TopicArn"]
    print(f"  [OK] SNS Topic ARN: {topic_arn}")
    
    # Subscribe email
    print(f"Subscribing email '{ALARM_EMAIL}' to SNS topic...")
    sns.subscribe(
        TopicArn=topic_arn,
        Protocol="email",
        Endpoint=ALARM_EMAIL
    )
    print(f"  [OK] Subscription created (pending confirmation in inbox if not confirmed)")
    
    # 2. Create CloudWatch Metric Alarm
    print(f"Creating CloudWatch alarm '{ALARM_NAME}' for Lambda '{FUNCTION_NAME}'...")
    cw.put_metric_alarm(
        AlarmName=ALARM_NAME,
        AlarmDescription="Alarm if medibook-book-appointment errors >= 1 in 5 minutes",
        ActionsEnabled=True,
        AlarmActions=[topic_arn],
        MetricName="Errors",
        Namespace="AWS/Lambda",
        Statistic="Sum",
        Dimensions=[
            {
                "Name": "FunctionName",
                "Value": FUNCTION_NAME
            }
        ],
        Period=300,
        EvaluationPeriods=1,
        Threshold=1.0,
        ComparisonOperator="GreaterThanOrEqualToThreshold"
    )
    print(f"  [OK] CloudWatch alarm '{ALARM_NAME}' created successfully.")
    
    # 3. List recent Log Groups for medibook
    print("Verifying CloudWatch Log Groups for MediBook Lambdas...")
    log_groups = logs.describe_log_groups(logGroupNamePrefix="/aws/lambda/medibook-")
    count = len(log_groups.get("logGroups", []))
    print(f"  [OK] Found {count} MediBook Lambda log groups.")
    for lg in log_groups.get("logGroups", []):
        print(f"    - {lg['logGroupName']}")
        
    info = {
        "TopicArn": topic_arn,
        "AlarmName": ALARM_NAME,
        "AlarmEmail": ALARM_EMAIL,
        "MonitoredFunction": FUNCTION_NAME
    }
    with open(os.path.join(os.path.dirname(__file__), "cloudwatch_info.json"), "w") as f:
        json.dump(info, f, indent=2)
        
    print("\nPhase 12 completed successfully!")
    return info

if __name__ == "__main__":
    setup_cloudwatch_and_sns()
