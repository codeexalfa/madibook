import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timezone

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

    # Check user role from Cognito JWT claims
    request_context = event.get("requestContext", {})
    authorizer = request_context.get("authorizer", {})
    claims = authorizer.get("claims", {})
    user_groups = claims.get("cognito:groups", "")

    # Role check: only doctors and admins can view doctor schedules
    if claims and ("doctor" not in user_groups and "admin" not in user_groups):
        return build_response(403, {"message": "Access denied: Doctors only"})

    # Find doctor ID from claims, query string, or fallback for demo
    query_params = event.get("queryStringParameters") or {}
    doctor_id = query_params.get("doctorId")
    if not doctor_id and claims:
        doctor_id = claims.get("sub") or claims.get("cognito:username")
    if not doctor_id:
        doctor_id = "doc-1"

    # Today's date in YYYY-MM-DD format (or passed ?date=)
    today_date = query_params.get("date")
    if not today_date:
        today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    try:
        # Query appointments for this doctor where slotTime begins with today's date
        response = appointments_table.query(
            KeyConditionExpression=Key("doctorId").eq(doctor_id) & Key("slotTime").begins_with(today_date)
        )
        today_appointments = response.get("Items", [])

        # Sort by time
        today_appointments.sort(key=lambda x: x.get("slotTime", ""))

        return build_response(200, {
            "doctorId": doctor_id,
            "date": today_date,
            "totalToday": len(today_appointments),
            "appointments": today_appointments
        })

    except Exception as error:
        return build_response(500, {"message": f"Error loading today's schedule: {str(error)}"})
