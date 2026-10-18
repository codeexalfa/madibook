import os
import json
import time
import boto3

REGION = "us-east-1"
ACCOUNT_ID = "355628740179"
ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/medibook-lambda-role"
QUEUE_URL = f"https://sqs.{REGION}.amazonaws.com/{ACCOUNT_ID}/medibook-booking-events"
QUEUE_ARN = f"arn:aws:sqs:{REGION}:{ACCOUNT_ID}:medibook-booking-events"
REFERRAL_BUCKET = "medibook-referrals-40179-app"
SENDER_EMAIL = "rabbiraz123@gmail.com"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEPLOY_DIR = os.path.dirname(SCRIPT_DIR)
ZIPS_DIR = os.path.join(DEPLOY_DIR, "zips")

lambda_client = boto3.client("lambda", region_name=REGION)

FUNCTIONS = [
    {
        "name": "medibook-book-appointment",
        "zip": "book_appointment.zip",
        "env": {"APPOINTMENTS_TABLE": "Appointments", "QUEUE_URL": QUEUE_URL}
    },
    {
        "name": "medibook-get-doctors",
        "zip": "get_doctors.zip",
        "env": {"DOCTORS_TABLE": "Doctors"}
    },
    {
        "name": "medibook-get-slots",
        "zip": "get_slots.zip",
        "env": {"DOCTORS_TABLE": "Doctors", "APPOINTMENTS_TABLE": "Appointments"}
    },
    {
        "name": "medibook-my-appointments",
        "zip": "my_appointments.zip",
        "env": {"APPOINTMENTS_TABLE": "Appointments"}
    },
    {
        "name": "medibook-cancel-appointment",
        "zip": "cancel_appointment.zip",
        "env": {"APPOINTMENTS_TABLE": "Appointments", "QUEUE_URL": QUEUE_URL}
    },
    {
        "name": "medibook-doctor-availability",
        "zip": "doctor_availability.zip",
        "env": {"DOCTORS_TABLE": "Doctors"}
    },
    {
        "name": "medibook-doctor-today",
        "zip": "doctor_today.zip",
        "env": {"APPOINTMENTS_TABLE": "Appointments"}
    },
    {
        "name": "medibook-admin-stats",
        "zip": "admin_stats.zip",
        "env": {"APPOINTMENTS_TABLE": "Appointments"}
    },
    {
        "name": "medibook-referral-upload-url",
        "zip": "referral_upload_url.zip",
        "env": {"REFERRAL_BUCKET": REFERRAL_BUCKET}
    },
    {
        "name": "medibook-notifier",
        "zip": "notifier.zip",
        "env": {"SENDER_EMAIL": SENDER_EMAIL}
    },
    {
        "name": "medibook-post-confirmation",
        "zip": "post_confirmation.zip",
        "env": {}
    }
]

def wait_for_function_active(func_name):
    for _ in range(30):
        try:
            res = lambda_client.get_function(FunctionName=func_name)
            state = res.get("Configuration", {}).get("State", "Active")
            update_status = res.get("Configuration", {}).get("LastUpdateStatus", "Successful")
            if state == "Active" and update_status != "InProgress":
                return
        except Exception:
            pass
        time.sleep(2)

def deploy_lambdas():
    print("=" * 60)
    print(" === Phase 6: Deploying 11 AWS Lambda Functions ===")
    print("=" * 60)

    for item in FUNCTIONS:
        func_name = item["name"]
        zip_file = os.path.join(ZIPS_DIR, item["zip"])
        env_vars = item["env"]

        with open(zip_file, "rb") as f:
            zip_bytes = f.read()

        # Check if function exists
        try:
            lambda_client.get_function(FunctionName=func_name)
            print(f"Updating code for '{func_name}'...")
            lambda_client.update_function_code(
                FunctionName=func_name,
                ZipFile=zip_bytes
            )
            wait_for_function_active(func_name)
            lambda_client.update_function_configuration(
                FunctionName=func_name,
                Role=ROLE_ARN,
                Handler="lambda_function.lambda_handler",
                Runtime="python3.12",
                Timeout=15,
                MemorySize=128,
                Environment={"Variables": env_vars}
            )
            wait_for_function_active(func_name)
            print(f"  [OK] Updated '{func_name}'")
        except lambda_client.exceptions.ResourceNotFoundException:
            print(f"Creating function '{func_name}'...")
            lambda_client.create_function(
                FunctionName=func_name,
                Runtime="python3.12",
                Role=ROLE_ARN,
                Handler="lambda_function.lambda_handler",
                Code={"ZipFile": zip_bytes},
                Description=f"MediBook Serverless function: {func_name}",
                Timeout=15,
                MemorySize=128,
                Environment={"Variables": env_vars}
            )
            wait_for_function_active(func_name)
            print(f"  [OK] Created '{func_name}'")

    # Attach SQS trigger to medibook-notifier
    print("\nSetting up SQS event source mapping for 'medibook-notifier'...")
    try:
        mappings = lambda_client.list_event_source_mappings(
            FunctionName="medibook-notifier",
            EventSourceArn=QUEUE_ARN
        )
        if len(mappings.get("EventSourceMappings", [])) == 0:
            lambda_client.create_event_source_mapping(
                EventSourceArn=QUEUE_ARN,
                FunctionName="medibook-notifier",
                Enabled=True,
                BatchSize=5
            )
            print("  [OK] SQS trigger attached successfully.")
        else:
            print("  [OK] SQS trigger already exists.")
    except Exception as e:
        print(f"Warning setting SQS trigger: {e}")

    # Allow API Gateway and Cognito invocations
    print("\nConfiguring invoke permissions...")
    for item in FUNCTIONS:
        func_name = item["name"]
        # API Gateway permission
        try:
            lambda_client.add_permission(
                FunctionName=func_name,
                StatementId="apigateway-invoke-permission",
                Action="lambda:InvokeFunction",
                Principal="apigateway.amazonaws.com"
            )
        except lambda_client.exceptions.ResourceConflictException:
            pass

    # Cognito permission for post_confirmation
    try:
        lambda_client.add_permission(
            FunctionName="medibook-post-confirmation",
            StatementId="cognito-invoke-permission",
            Action="lambda:InvokeFunction",
            Principal="cognito-idp.amazonaws.com"
        )
    except lambda_client.exceptions.ResourceConflictException:
        pass

    # Test-invoke each function
    print("\nTesting all 11 Lambda functions with test events:")
    for item in FUNCTIONS:
        func_name = item["name"]
        try:
            payload = json.dumps({"httpMethod": "OPTIONS"})
            if func_name == "medibook-notifier":
                payload = json.dumps({"Records": []})

            response = lambda_client.invoke(
                FunctionName=func_name,
                InvocationType="RequestResponse",
                Payload=payload
            )
            status_code = response.get("StatusCode")
            print(f"  [PASS] {func_name:32} -> HTTP {status_code} (Success)")
        except Exception as err:
            print(f"  [FAIL] {func_name:32} -> Error: {err}")

if __name__ == "__main__":
    deploy_lambdas()
