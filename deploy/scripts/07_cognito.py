import boto3
import os

REGION = "us-east-1"
ACCOUNT_ID = "355628740179"
USER_POOL_NAME = "medibook-user-pool"
CLIENT_NAME = "medibook-web-client"
TRIGGER_ARN = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:medibook-post-confirmation"

cognito_client = boto3.client("cognito-idp", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)

def setup_cognito():
    print("=" * 60)
    print(" === Phase 7: Setting up Amazon Cognito User Pool ===")
    print("=" * 60)

    # 1. Find or create user pool
    user_pool_id = None
    pools = cognito_client.list_user_pools(MaxResults=60)
    for pool in pools.get("UserPools", []):
        if pool["Name"] == USER_POOL_NAME:
            user_pool_id = pool["Id"]
            print(f"Found existing User Pool: {USER_POOL_NAME} ({user_pool_id})")
            break

    if not user_pool_id:
        print(f"Creating User Pool '{USER_POOL_NAME}'...")
        response = cognito_client.create_user_pool(
            PoolName=USER_POOL_NAME,
            Policies={
                "PasswordPolicy": {
                    "MinimumLength": 8,
                    "RequireUppercase": False,
                    "RequireLowercase": False,
                    "RequireNumbers": True,
                    "RequireSymbols": False
                }
            },
            AutoVerifiedAttributes=["email"],
            UsernameAttributes=["email"],
            LambdaConfig={
                "PostConfirmation": TRIGGER_ARN
            }
        )
        user_pool_id = response["UserPool"]["Id"]
        print(f"  [OK] Created User Pool: {user_pool_id}")
    else:
        # Update Lambda trigger to ensure post_confirmation is attached
        print(f"Updating Lambda trigger on User Pool...")
        cognito_client.update_user_pool(
            UserPoolId=user_pool_id,
            AutoVerifiedAttributes=["email"],
            LambdaConfig={
                "PostConfirmation": TRIGGER_ARN
            }
        )
        print("  [OK] Lambda trigger updated.")

    # Allow Cognito to invoke post_confirmation Lambda
    try:
        lambda_client.add_permission(
            FunctionName="medibook-post-confirmation",
            StatementId=f"cognito-{user_pool_id}-invoke",
            Action="lambda:InvokeFunction",
            Principal="cognito-idp.amazonaws.com",
            SourceArn=f"arn:aws:cognito-idp:{REGION}:{ACCOUNT_ID}:userpool/{user_pool_id}"
        )
    except lambda_client.exceptions.ResourceConflictException:
        pass

    # 2. Find or create App Client (no secret, USER_PASSWORD_AUTH on)
    client_id = None
    clients = cognito_client.list_user_pool_clients(UserPoolId=user_pool_id, MaxResults=60)
    for c in clients.get("UserPoolClients", []):
        if c["ClientName"] == CLIENT_NAME:
            client_id = c["ClientId"]
            print(f"Found existing App Client: {CLIENT_NAME} ({client_id})")
            break

    if not client_id:
        print(f"Creating App Client '{CLIENT_NAME}'...")
        client_resp = cognito_client.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName=CLIENT_NAME,
            GenerateSecret=False,
            ExplicitAuthFlows=[
                "ALLOW_USER_PASSWORD_AUTH",
                "ALLOW_REFRESH_TOKEN_AUTH",
                "ALLOW_USER_SRP_AUTH"
            ]
        )
        client_id = client_resp["UserPoolClient"]["ClientId"]
        print(f"  [OK] Created App Client: {client_id}")

    # 3. Create the 3 Groups: patient, doctor, admin
    print("\nEnsuring User Pool Groups (patient, doctor, admin)...")
    groups = ["patient", "doctor", "admin"]
    for grp in groups:
        try:
            cognito_client.create_group(
                GroupName=grp,
                UserPoolId=user_pool_id,
                Description=f"MediBook {grp} group"
            )
            print(f"  [OK] Created group: {grp}")
        except cognito_client.exceptions.GroupExistsException:
            print(f"  [OK] Group '{grp}' already exists.")

    print("\n" + "=" * 60)
    print(" === Cognito Setup Summary ===")
    print("=" * 60)
    print(f" User Pool Name: {USER_POOL_NAME}")
    print(f" User Pool ID:   {user_pool_id}")
    print(f" App Client ID:  {client_id}")
    print(" Groups:         patient, doctor, admin")
    print(f" Trigger:        {TRIGGER_ARN}")
    print("=" * 60)

    # Save output for next phases
    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cognito_ids.json")
    with open(out_file, "w") as f:
        json.dump({"USER_POOL_ID": user_pool_id, "CLIENT_ID": client_id}, f)

if __name__ == "__main__":
    setup_cognito()
