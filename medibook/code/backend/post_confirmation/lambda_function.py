import json
import boto3

# Connect to Cognito Identity Provider
cognito_client = boto3.client("cognito-idp")

def lambda_handler(event, context):
    # This function is triggered by Amazon Cognito after a user confirms their sign-up
    print("PostConfirmation trigger received:", json.dumps(event))

    user_pool_id = event.get("userPoolId", "")
    username = event.get("userName", "")

    # Group name to assign every new registered user
    group_name = "patient"

    if user_pool_id and username:
        try:
            # Automatically add the new user to the "patient" group
            cognito_client.admin_add_user_to_group(
                UserPoolId=user_pool_id,
                Username=username,
                GroupName=group_name
            )
            print(f"Successfully added user '{username}' to group '{group_name}'")
        except Exception as error:
            # Log error if adding to group fails, but do not stop user signup
            print(f"Error adding user to group: {str(error)}")

    # Always return the original event back to Cognito
    return event
