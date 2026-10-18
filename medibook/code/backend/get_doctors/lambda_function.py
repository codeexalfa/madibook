import json
import os
import boto3
from boto3.dynamodb.conditions import Attr

# Get doctor table name from environment variables
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

    # Check query string parameters for optional department filter
    query_params = event.get("queryStringParameters") or {}
    department_filter = query_params.get("dept")

    try:
        # If user asked for a specific department, filter doctors
        if department_filter:
            response = doctors_table.scan(
                FilterExpression=Attr("department").eq(department_filter)
            )
        else:
            # Otherwise return all doctors
            response = doctors_table.scan()

        doctors_list = response.get("Items", [])
        return build_response(200, {"doctors": doctors_list})

    except Exception as error:
        return build_response(500, {"message": f"Error fetching doctors: {str(error)}"})
