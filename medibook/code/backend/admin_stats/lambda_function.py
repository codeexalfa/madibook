import json
import os
import boto3
from datetime import datetime

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

    # Role check: only admins can access stats
    if claims and ("admin" not in user_groups):
        return build_response(403, {"message": "Access denied: Admins only"})

    try:
        # Scan all appointments to compute dashboard stats
        response = appointments_table.scan()
        all_items = response.get("Items", [])

        # Stats variables
        department_counts = {}
        day_counts = {
            "Monday": 0,
            "Tuesday": 0,
            "Wednesday": 0,
            "Thursday": 0,
            "Friday": 0,
            "Saturday": 0,
            "Sunday": 0
        }
        total_count = len(all_items)
        no_show_count = 0
        confirmed_count = 0
        cancelled_count = 0

        # Loop through every appointment
        for item in all_items:
            dept = item.get("department", "General")
            if dept not in department_counts:
                department_counts[dept] = 0
            department_counts[dept] += 1

            status = item.get("status", "CONFIRMED")
            if status == "NO_SHOW":
                no_show_count += 1
            elif status == "CANCELLED":
                cancelled_count += 1
            else:
                confirmed_count += 1

            # Determine day of week from slotTime (format: "YYYY-MM-DD HH:MM")
            slot_time = item.get("slotTime", "")
            if len(slot_time) >= 10:
                try:
                    date_part = slot_time[:10]
                    parsed_date = datetime.strptime(date_part, "%Y-%m-%d")
                    day_name = parsed_date.strftime("%A")
                    if day_name in day_counts:
                        day_counts[day_name] += 1
                except Exception:
                    pass

        # Calculate no-show rate percentage
        if total_count > 0:
            no_show_rate = round((no_show_count / total_count) * 100, 1)
        else:
            no_show_rate = 0.0

        # Find the busiest day
        busiest_day = "Monday"
        max_bookings = -1
        for day, count in day_counts.items():
            if count > max_bookings:
                max_bookings = count
                busiest_day = day

        # Build table rows for departments
        department_table = []
        for dept, count in department_counts.items():
            percentage = round((count / total_count * 100), 1) if total_count > 0 else 0
            department_table.append({
                "department": dept,
                "bookings": count,
                "percentage": f"{percentage}%"
            })

        return build_response(200, {
            "totalAppointments": total_count,
            "confirmedCount": confirmed_count,
            "noShowCount": no_show_count,
            "cancelledCount": cancelled_count,
            "noShowRate": f"{no_show_rate}%",
            "busiestDay": busiest_day,
            "busiestDayCount": max_bookings if max_bookings > 0 else 0,
            "bookingsPerDepartment": department_counts,
            "bookingsPerDay": day_counts,
            "departmentTable": department_table
        })

    except Exception as error:
        return build_response(500, {"message": f"Error calculating stats: {str(error)}"})
