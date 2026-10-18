import json
import os
import boto3
from botocore.exceptions import ClientError

# Get table names and queue url from environment variables
APPOINTMENTS_TABLE = os.environ.get("APPOINTMENTS_TABLE", "Appointments")
QUEUE_URL = os.environ.get("QUEUE_URL", "")

# Connect to DynamoDB and SQS
dynamodb_resource = boto3.resource("dynamodb")
appointments_table = dynamodb_resource.Table(APPOINTMENTS_TABLE)
sqs_client = boto3.client("sqs")

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

    # Check who is logged in from Cognito claims
    request_context = event.get("requestContext", {})
    authorizer = request_context.get("authorizer", {})
    claims = authorizer.get("claims", {})
    
    # Get user information
    patient_id = claims.get("sub", "")
    patient_email = claims.get("email", "")
    user_groups = claims.get("cognito:groups", "")

    # Read the request body
    body_text = event.get("body", "{}")
    if not body_text:
        body_text = "{}"
    
    try:
        body_data = json.loads(body_text)
    except Exception:
        return build_response(400, {"message": "Invalid JSON in request body"})

    # If testing without Cognito, read from body
    if not patient_id:
        patient_id = body_data.get("patientId", "demo-patient-1")
    if not patient_email:
        patient_email = body_data.get("patientEmail", "patient@example.com")

    doctor_id = body_data.get("doctorId", "")
    doctor_name = body_data.get("doctorName", "Doctor")
    slot_time = body_data.get("slotTime", "")
    department = body_data.get("department", "General")
    notes = body_data.get("notes", "")

    # Check required fields
    if not doctor_id or not slot_time:
        return build_response(400, {"message": "Missing doctorId or slotTime"})

    # Prepare appointment item
    # Partition key: doctorId, Sort key: slotTime
    appointment_id = f"{doctor_id}_{slot_time}".replace(" ", "_")
    appointment_item = {
        "doctorId": doctor_id,
        "slotTime": slot_time,
        "appointmentId": appointment_id,
        "doctorName": doctor_name,
        "patientId": patient_id,
        "patientEmail": patient_email,
        "department": department,
        "notes": notes,
        "status": "CONFIRMED",
        "createdAt": slot_time[:10]
    }

    # Save to DynamoDB with condition to PREVENT DOUBLE BOOKING
    # If the doctor already has an appointment at this slotTime, fail!
    try:
        appointments_table.put_item(
            Item=appointment_item,
            ConditionExpression="attribute_not_exists(doctorId) AND attribute_not_exists(slotTime)"
        )
    except ClientError as error:
        error_code = error.response.get("Error", {}).get("Code", "")
        if error_code == "ConditionalCheckFailedException":
            return build_response(409, {"message": "This slot is already taken"})
        else:
            return build_response(500, {"message": f"Database error: {str(error)}"})

    # Send message to SQS queue for the email notifier
    # Booking must not wait for email sending
    if QUEUE_URL:
        try:
            sqs_payload = {
                "eventType": "BOOKING_CONFIRMED",
                "patientEmail": patient_email,
                "doctorName": doctor_name,
                "slotTime": slot_time,
                "department": department,
                "appointmentId": appointment_id
            }
            sqs_client.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=json.dumps(sqs_payload)
            )
        except Exception as sqs_error:
            # We do not fail the booking if SQS fails; log the error
            print(f"Warning: Failed to send SQS message: {str(sqs_error)}")

    return build_response(201, {
        "message": "Booked!",
        "appointment": appointment_item
    })
