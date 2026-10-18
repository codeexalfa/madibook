import json
import os
import boto3

# Get table name from environment variables
DOCTORS_TABLE = os.environ.get("DOCTORS_TABLE", "Doctors")

# Connect to DynamoDB
dynamodb_resource = boto3.resource("dynamodb")
doctors_table = dynamodb_resource.Table(DOCTORS_TABLE)

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

    # Role check: only doctors or admins can update availability
    # (Allow demo testing if claims are empty)
    if claims and ("doctor" not in user_groups and "admin" not in user_groups):
        return build_response(403, {"message": "Access denied: Doctors only"})

    # Parse body
    body_text = event.get("body", "{}")
    if not body_text:
        body_text = "{}"
    try:
        body_data = json.loads(body_text)
    except Exception:
        return build_response(400, {"message": "Invalid JSON in request body"})

    doctor_id = body_data.get("doctorId")
    # If not passed in body, try Cognito sub or username
    if not doctor_id and claims:
        doctor_id = claims.get("sub") or claims.get("cognito:username")
    if not doctor_id:
        doctor_id = "doc-1"

    schedule = body_data.get("schedule", [])
    doctor_name = body_data.get("name", "Dr. Specialist")
    department = body_data.get("department", "General")

    if not schedule:
        return build_response(400, {"message": "Schedule list cannot be empty"})

    try:
        # Update or insert doctor availability in DynamoDB
        doctors_table.update_item(
            Key={"doctorId": doctor_id},
            UpdateExpression="SET schedule = :s, #n = if_not_exists(#n, :name), department = if_not_exists(department, :dept)",
            ExpressionAttributeNames={"#n": "name"},
            ExpressionAttributeValues={
                ":s": schedule,
                ":name": doctor_name,
                ":dept": department
            }
        )

        return build_response(200, {
            "message": "Weekly availability updated successfully",
            "doctorId": doctor_id,
            "schedule": schedule
        })

    except Exception as error:
        return build_response(500, {"message": f"Error updating availability: {str(error)}"})
