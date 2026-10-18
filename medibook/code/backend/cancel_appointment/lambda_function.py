import json
import os
import boto3
from boto3.dynamodb.conditions import Attr

# Get table name and queue URL from environment variables
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

    # Check path parameters or body
    path_parameters = event.get("pathParameters") or {}
    appointment_id = path_parameters.get("id", "")

    body_text = event.get("body", "{}")
    if not body_text:
        body_text = "{}"
    try:
        body_data = json.loads(body_text)
    except Exception:
        body_data = {}

    doctor_id = body_data.get("doctorId", "")
    slot_time = body_data.get("slotTime", "")

    # If doctorId or slotTime are missing, search by appointmentId or parse
    target_item = None
    if doctor_id and slot_time:
        res = appointments_table.get_item(Key={"doctorId": doctor_id, "slotTime": slot_time})
        target_item = res.get("Item")
    elif appointment_id:
        # Try scanning for the appointmentId
        scan_res = appointments_table.scan(
            FilterExpression=Attr("appointmentId").eq(appointment_id)
        )
        items = scan_res.get("Items", [])
        if items:
            target_item = items[0]
            doctor_id = target_item.get("doctorId")
            slot_time = target_item.get("slotTime")

    if not target_item or not doctor_id or not slot_time:
        return build_response(404, {"message": "Appointment not found"})

    try:
        # Delete the appointment so the slot can be booked again
        appointments_table.delete_item(
            Key={
                "doctorId": doctor_id,
                "slotTime": slot_time
            }
        )

        # Notify via SQS that the appointment was cancelled
        if QUEUE_URL:
            try:
                sqs_payload = {
                    "eventType": "BOOKING_CANCELLED",
                    "patientEmail": target_item.get("patientEmail", ""),
                    "doctorName": target_item.get("doctorName", "Doctor"),
                    "slotTime": slot_time,
                    "department": target_item.get("department", "General"),
                    "appointmentId": appointment_id or f"{doctor_id}_{slot_time}"
                }
                sqs_client.send_message(
                    QueueUrl=QUEUE_URL,
                    MessageBody=json.dumps(sqs_payload)
                )
            except Exception as sqs_err:
                print(f"Warning: Failed to send cancellation SQS message: {str(sqs_err)}")

        return build_response(200, {
            "message": "Appointment cancelled successfully",
            "appointmentId": appointment_id
        })

    except Exception as error:
        return build_response(500, {"message": f"Error cancelling appointment: {str(error)}"})
