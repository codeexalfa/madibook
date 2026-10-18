import json
import os
import boto3
from datetime import datetime, timezone

# Get S3 bucket name from environment variables
REFERRAL_BUCKET = os.environ.get("REFERRAL_BUCKET", "medibook-referrals-bucket")

# Connect to S3
s3_client = boto3.client("s3")

# Helper function to send simple CORS headers
def build_response(status_code, body_data):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET,DELETE"
        },
        "body": json.dumps(body_data)
    }

def lambda_handler(event, context):
    # Check if this is an OPTIONS pre-flight request for CORS
    http_method = event.get("httpMethod", "")
    if http_method == "OPTIONS":
        return build_response(200, {"message": "OK"})

    # Get patient identity from Cognito JWT claims
    request_context = event.get("requestContext", {})
    authorizer = request_context.get("authorizer", {})
    claims = authorizer.get("claims", {})
    patient_id = claims.get("sub", "demo-patient-1")

    # Read body
    body_text = event.get("body", "{}")
    if not body_text:
        body_text = "{}"
    try:
        body_data = json.loads(body_text)
    except Exception:
        body_data = {}

    file_name = body_data.get("fileName", "referral_document.pdf")
    content_type = body_data.get("contentType", "application/pdf")

    # Sanitize file name to avoid weird characters
    safe_file_name = file_name.replace(" ", "_")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    s3_key = f"referrals/{patient_id}/{timestamp}_{safe_file_name}"

    try:
        # Generate presigned upload URL (valid for 5 minutes / 300 seconds)
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": REFERRAL_BUCKET,
                "Key": s3_key,
                "ContentType": content_type
            },
            ExpiresIn=300
        )

        return build_response(200, {
            "message": "Presigned upload URL generated",
            "uploadUrl": presigned_url,
            "fileKey": s3_key,
            "expiresInSeconds": 300
        })

    except Exception as error:
        return build_response(500, {"message": f"Error creating upload URL: {str(error)}"})
