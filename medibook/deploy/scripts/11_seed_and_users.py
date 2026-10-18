import os
import boto3

REGION = "us-east-1"
USER_POOL_ID = "us-east-1_WUtK6EmCF"

cognito_client = boto3.client("cognito-idp", region_name=REGION)
dynamodb_resource = boto3.resource("dynamodb", region_name=REGION)

DEMO_USERS = [
    {"email": "patient@medibook.hospital", "name": "Demo Patient", "role": "patient"},
    {"email": "doctor@medibook.hospital", "name": "Dr. Sarah Jenkins", "role": "doctor"},
    {"email": "admin@medibook.hospital", "name": "Hospital Admin", "role": "admin"},
    {"email": "rabbiraz123@gmail.com", "name": "Rabbi Raz", "role": "patient"}
]

TEMP_PASSWORD = "Password123!"

def seed_users():
    print("=" * 60)
    print(" === Phase 11: Seeding Demo Data & Creating Cognito Users ===")
    print("=" * 60)

    # 1. Run seed_data.py to populate DynamoDB
    print("Seeding DynamoDB Doctors and Appointments tables...")
    import sys
    script_dir = os.path.dirname(os.path.abspath(__file__))
    medibook_root = os.path.dirname(os.path.dirname(script_dir))
    seed_script = os.path.join(medibook_root, "code", "seed", "seed_data.py")

    with open(seed_script, "r", encoding="utf-8") as f:
        exec(f.read(), globals())

    # 2. Create Cognito Users
    print("\nCreating demo users in Cognito User Pool...")
    for u in DEMO_USERS:
        email = u["email"]
        role = u["role"]
        name = u["name"]

        # Check if user exists
        try:
            cognito_client.admin_get_user(UserPoolId=USER_POOL_ID, Username=email)
            print(f"User '{email}' already exists. Updating password & role...")
        except cognito_client.exceptions.UserNotFoundException:
            print(f"Creating user '{email}' ({role})...")
            cognito_client.admin_create_user(
                UserPoolId=USER_POOL_ID,
                Username=email,
                UserAttributes=[
                    {"Name": "email", "Value": email},
                    {"Name": "email_verified", "Value": "true"},
                    {"Name": "name", "Value": name}
                ],
                MessageAction="SUPPRESS"
            )

        # Set permanent password
        cognito_client.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=email,
            Password=TEMP_PASSWORD,
            Permanent=True
        )

        # Add to group
        try:
            cognito_client.admin_add_user_to_group(
                UserPoolId=USER_POOL_ID,
                Username=email,
                GroupName=role
            )
            print(f"  [OK] Added '{email}' to group '{role}'")
        except Exception as e:
            print(f"  Note: {e}")

    print("\n" + "=" * 60)
    print(" === Demo Users Ready ===")
    print("=" * 60)
    for u in DEMO_USERS:
        print(f" Role: {u['role'].upper():7} | Email: {u['email']:25} | Password: {TEMP_PASSWORD}")
    print("=" * 60)

if __name__ == "__main__":
    seed_users()
