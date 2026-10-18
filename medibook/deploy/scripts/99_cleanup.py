import boto3
import json
import os

AWS_REGION = "us-east-1"
ACCOUNT_ID = "355628740179"
CLOUDFRONT_INFO_PATH = os.path.join(os.path.dirname(__file__), "cloudfront_info.json")
API_INFO_PATH = os.path.join(os.path.dirname(__file__), "api_info.json")
COGNITO_INFO_PATH = os.path.join(os.path.dirname(__file__), "cognito_ids.json")

def empty_and_delete_s3_bucket(s3_client, bucket_name):
    print(f"Emptying S3 bucket '{bucket_name}'...")
    try:
        # Delete all object versions and objects
        paginator = s3_client.get_paginator("list_object_versions")
        for page in paginator.paginate(Bucket=bucket_name):
            delete_items = []
            for v in page.get("Versions", []):
                delete_items.append({"Key": v["Key"], "VersionId": v["VersionId"]})
            for m in page.get("DeleteMarkers", []):
                delete_items.append({"Key": m["Key"], "VersionId": m["VersionId"]})
            if delete_items:
                s3_client.delete_objects(Bucket=bucket_name, Delete={"Objects": delete_items})
                
        # Also plain objects if unversioned
        paginator_obj = s3_client.get_paginator("list_objects_v2")
        for page in paginator_obj.paginate(Bucket=bucket_name):
            delete_items = [{"Key": o["Key"]} for o in page.get("Contents", [])]
            if delete_items:
                s3_client.delete_objects(Bucket=bucket_name, Delete={"Objects": delete_items})
                
        s3_client.delete_bucket(Bucket=bucket_name)
        print(f"  [OK] Deleted S3 bucket '{bucket_name}'")
    except Exception as e:
        print(f"  [WARN] Bucket {bucket_name}: {e}")

def run_cleanup():
    print("=" * 60)
    print(" === MediBook Automated Resource Cleanup ===")
    print("=" * 60)
    print("WARNING: This will delete all MediBook AWS resources.")
    confirm = input("Type 'DELETE_ALL_MEDIBOOK' to confirm: ")
    if confirm != "DELETE_ALL_MEDIBOOK":
        print("Cleanup cancelled.")
        return

    # 1. CloudWatch Alarm & SNS
    print("\n1. Deleting CloudWatch Alarms & SNS...")
    cw = boto3.client("cloudwatch", region_name=AWS_REGION)
    try:
        cw.delete_alarms(AlarmNames=["MediBook-Lambda-Error-Alarm"])
        print("  [OK] Deleted CloudWatch Alarm")
    except Exception as e:
        print(f"  [WARN] {e}")

    sns = boto3.client("sns", region_name=AWS_REGION)
    try:
        sns.delete_topic(TopicArn=f"arn:aws:sns:{AWS_REGION}:{ACCOUNT_ID}:medibook-alarms-topic")
        print("  [OK] Deleted SNS Topic")
    except Exception as e:
        print(f"  [WARN] {e}")

    # 2. CloudFront Distribution (Disable first)
    print("\n2. CloudFront Distribution...")
    if os.path.exists(CLOUDFRONT_INFO_PATH):
        with open(CLOUDFRONT_INFO_PATH) as f:
            cf_info = json.load(f)
        cf_id = cf_info.get("DISTRIBUTION_ID")
        if cf_id:
            cf = boto3.client("cloudfront")
            try:
                res = cf.get_distribution_config(Id=cf_id)
                cfg = res["DistributionConfig"]
                etag = res["ETag"]
                if cfg["Enabled"]:
                    cfg["Enabled"] = False
                    cf.update_distribution(DistributionConfig=cfg, Id=cf_id, IfMatch=etag)
                    print(f"  [OK] CloudFront distribution {cf_id} disabled (deletion requires fully deployed disabled state).")
                else:
                    cf.delete_distribution(Id=cf_id, IfMatch=etag)
                    print(f"  [OK] Deleted CloudFront distribution {cf_id}")
            except Exception as e:
                print(f"  [WARN] CloudFront {cf_id}: {e}")

    # 3. S3 Buckets
    print("\n3. Deleting S3 Buckets...")
    s3 = boto3.client("s3", region_name=AWS_REGION)
    empty_and_delete_s3_bucket(s3, "medibook-website-40179-app")
    empty_and_delete_s3_bucket(s3, "medibook-referrals-40179-app")

    # 4. API Gateway
    print("\n4. Deleting API Gateway...")
    if os.path.exists(API_INFO_PATH):
        with open(API_INFO_PATH) as f:
            api_info = json.load(f)
        api_id = api_info.get("API_ID")
        if api_id:
            apigw = boto3.client("apigateway", region_name=AWS_REGION)
            try:
                apigw.delete_rest_api(restApiId=api_id)
                print(f"  [OK] Deleted API Gateway {api_id}")
            except Exception as e:
                print(f"  [WARN] API Gateway: {e}")

    # 5. Lambda Functions
    print("\n5. Deleting 11 Lambda Functions...")
    lambda_client = boto3.client("lambda", region_name=AWS_REGION)
    functions = [
        "medibook-get-doctors",
        "medibook-get-slots",
        "medibook-book-appointment",
        "medibook-my-appointments",
        "medibook-cancel-appointment",
        "medibook-doctor-availability",
        "medibook-doctor-today",
        "medibook-referral-upload-url",
        "medibook-admin-stats",
        "medibook-notifier",
        "medibook-post-confirmation"
    ]
    for fn in functions:
        try:
            lambda_client.delete_function(FunctionName=fn)
            print(f"  [OK] Deleted Lambda {fn}")
        except Exception as e:
            print(f"  [WARN] Lambda {fn}: {e}")

    # 6. SQS Queue
    print("\n6. Deleting SQS Queue...")
    sqs = boto3.client("sqs", region_name=AWS_REGION)
    try:
        sqs.delete_queue(QueueUrl=f"https://sqs.{AWS_REGION}.amazonaws.com/{ACCOUNT_ID}/medibook-booking-events")
        print("  [OK] Deleted SQS Queue")
    except Exception as e:
        print(f"  [WARN] SQS: {e}")

    # 7. DynamoDB Tables
    print("\n7. Deleting DynamoDB Tables...")
    ddb = boto3.client("dynamodb", region_name=AWS_REGION)
    for table in ["Appointments", "Doctors", "Patients"]:
        try:
            ddb.delete_table(TableName=table)
            print(f"  [OK] Deleted DynamoDB table {table}")
        except Exception as e:
            print(f"  [WARN] Table {table}: {e}")

    # 8. Cognito User Pool
    print("\n8. Deleting Cognito User Pool...")
    if os.path.exists(COGNITO_INFO_PATH):
        with open(COGNITO_INFO_PATH) as f:
            cog_info = json.load(f)
        pool_id = cog_info.get("USER_POOL_ID")
        if pool_id:
            cognito = boto3.client("cognito-idp", region_name=AWS_REGION)
            try:
                cognito.delete_user_pool(UserPoolId=pool_id)
                print(f"  [OK] Deleted Cognito User Pool {pool_id}")
            except Exception as e:
                print(f"  [WARN] Cognito: {e}")

    # 9. IAM Role
    print("\n9. Deleting IAM Role...")
    iam = boto3.client("iam")
    try:
        iam.delete_role_policy(RoleName="medibook-lambda-role", PolicyName="medibook-lambda-permissions")
        iam.detach_role_policy(RoleName="medibook-lambda-role", PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")
        iam.delete_role(RoleName="medibook-lambda-role")
        print("  [OK] Deleted IAM Role medibook-lambda-role")
    except Exception as e:
        print(f"  [WARN] IAM: {e}")

    print("\nCleanup completed.")

if __name__ == "__main__":
    run_cleanup()
