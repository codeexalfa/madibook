import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timezone

# Get table names from environment variables
DOCTORS_TABLE = os.environ.get("DOCTORS_TABLE", "Doctors")
APPOINTMENTS_TABLE = os.environ.get("APPOINTMENTS_TABLE", "Appointments")

# Connect to DynamoDB
dynamodb_resource = boto3.resource("dynamodb")
doctors_table = dynamodb_resource.Table(DOCTORS_TABLE)
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

    # Get doctor ID from path parameters
    path_parameters = event.get("pathParameters") or {}
    doctor_id = path_parameters.get("id")

    # If not in path, check query parameters
    query_params = event.get("queryStringParameters") or {}
    if not doctor_id:
        doctor_id = query_params.get("doctorId")

    # Check for requested date (e.g. 2026-10-20)
    target_date = query_params.get("date")
    if not target_date:
        target_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if not doctor_id:
        return build_response(400, {"message": "Doctor ID is required"})

    try:
        # Step 1: Find the doctor to see their schedule
        doc_response = doctors_table.get_item(Key={"doctorId": doctor_id})
        doctor = doc_response.get("Item")
        if not doctor:
            return build_response(404, {"message": "Doctor not found"})

        # Get doctor's available times (or use standard office hours if empty)
        daily_times = doctor.get("schedule", [
            "09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00"
        ])

        # Generate full slot strings like "2026-10-20 09:00"
        all_slots = []
        for time_str in daily_times:
            all_slots.append(f"{target_date} {time_str}")

        # Step 2: Query DynamoDB for existing appointments for this doctor
        # Partition key is doctorId
        app_response = appointments_table.query(
            KeyConditionExpression=Key("doctorId").eq(doctor_id)
        )
        existing_appointments = app_response.get("Items", [])

        # Step 3: Find taken slots (that are CONFIRMED)
        taken_slots = set()
        for item in existing_appointments:
            status = item.get("status", "CONFIRMED")
            if status != "CANCELLED":
                taken_slots.add(item.get("slotTime"))

        # Step 4: Subtract taken slots from all slots to find free slots
        free_slots = []
        for slot in all_slots:
            if slot not in taken_slots:
                free_slots.append(slot)

        return build_response(200, {
            "doctorId": doctor_id,
            "doctorName": doctor.get("name", "Doctor"),
            "date": target_date,
            "freeSlots": free_slots
        })

    except Exception as error:
        return build_response(500, {"message": f"Error finding slots: {str(error)}"})
