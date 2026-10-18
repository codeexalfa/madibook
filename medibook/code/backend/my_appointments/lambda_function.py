import json
import os
import boto3
from boto3.dynamodb.conditions import Attr

# Get table name from environment variables
APPOINTMENTS_TABLE = os.environ.get("APPOINTMENTS_TABLE", "Appointments")

# Connect to DynamoDB
dynamodb_resource = boto3.resource("dynamodb")
appointments_table = dynamodb_resource.Table(APPOINTMENTS_TABLE)

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
    patient_id = claims.get("sub", "")
    patient_email = claims.get("email", "")

    # For testing or query overrides
    query_params = event.get("queryStringParameters") or {}
    if not patient_id:
        patient_id = query_params.get("patientId", "")

    if not patient_id and not patient_email:
        # Default fallback for testing
        patient_id = "demo-patient-1"

    try:
        # Scan appointments for this patient
        if patient_id and patient_email:
            response = appointments_table.scan(
                FilterExpression=Attr("patientId").eq(patient_id) | Attr("patientEmail").eq(patient_email)
            )
        elif patient_id:
            response = appointments_table.scan(
                FilterExpression=Attr("patientId").eq(patient_id)
            )
        else:
            response = appointments_table.scan(
                FilterExpression=Attr("patientEmail").eq(patient_email)
            )

        items = response.get("Items", [])

        # Sort appointments by slotTime
        items.sort(key=lambda x: x.get("slotTime", ""), reverse=False)

        return build_response(200, {"appointments": items})

    except Exception as error:
        return build_response(500, {"message": f"Error fetching appointments: {str(error)}"})
