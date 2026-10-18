import boto3
import json
import os
import time

REGION = "us-east-1"
ACCOUNT_ID = "355628740179"
API_NAME = "medibook-api"
USER_POOL_ID = "us-east-1_WUtK6EmCF"
USER_POOL_ARN = f"arn:aws:cognito-idp:{REGION}:{ACCOUNT_ID}:userpool/{USER_POOL_ID}"

apigw_client = boto3.client("apigateway", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)

def setup_api_gateway():
    print("=" * 60)
    print(" === Phase 8: Deploying Amazon API Gateway (REST API) ===")
    print("=" * 60)

    # 1. Find or create REST API
    api_id = None
    apis = apigw_client.get_rest_apis().get("items", [])
    for a in apis:
        if a["name"] == API_NAME:
            api_id = a["id"]
            print(f"Found existing REST API: {API_NAME} ({api_id})")
            break

    if not api_id:
        print(f"Creating REST API '{API_NAME}'...")
        api_resp = apigw_client.create_rest_api(
            name=API_NAME,
            description="MediBook Hospital REST API",
            endpointConfiguration={"types": ["REGIONAL"]}
        )
        api_id = api_resp["id"]
        print(f"  [OK] Created API: {api_id}")

    # Get root resource id
    resources = apigw_client.get_resources(restApiId=api_id).get("items", [])
    root_id = next(r["id"] for r in resources if r["path"] == "/")

    # 2. Setup Cognito Authorizer
    print("\nConfiguring Cognito Authorizer...")
    authorizer_id = None
    auths = apigw_client.get_authorizers(restApiId=api_id).get("items", [])
    for auth in auths:
        if auth["name"] == "medibook-authorizer":
            authorizer_id = auth["id"]
            print(f"Found existing Authorizer: {authorizer_id}")
            break

    if not authorizer_id:
        auth_resp = apigw_client.create_authorizer(
            restApiId=api_id,
            name="medibook-authorizer",
            type="COGNITO_USER_POOLS",
            providerARNs=[USER_POOL_ARN],
            identitySource="method.request.header.Authorization"
        )
        authorizer_id = auth_resp["id"]
        print(f"  [OK] Created Authorizer: {authorizer_id}")

    # Helper: Ensure a child resource exists
    def get_or_create_resource(parent_id, path_part):
        res_list = apigw_client.get_resources(restApiId=api_id).get("items", [])
        for r in res_list:
            if r.get("parentId") == parent_id and r.get("pathPart") == path_part:
                return r["id"]
        created = apigw_client.create_resource(
            restApiId=api_id,
            parentId=parent_id,
            pathPart=path_part
        )
        return created["id"]

    # Helper: Enable CORS (OPTIONS mock method)
    def enable_cors(res_id):
        # Create or update OPTIONS method
        try:
            apigw_client.put_method(
                restApiId=api_id,
                resourceId=res_id,
                httpMethod="OPTIONS",
                authorizationType="NONE"
            )
        except apigw_client.exceptions.ConflictException:
            pass

        apigw_client.put_integration(
            restApiId=api_id,
            resourceId=res_id,
            httpMethod="OPTIONS",
            type="MOCK",
            requestTemplates={"application/json": '{"statusCode": 200}'}
        )

        try:
            apigw_client.put_method_response(
                restApiId=api_id,
                resourceId=res_id,
                httpMethod="OPTIONS",
                statusCode="200",
                responseParameters={
                    "method.response.header.Access-Control-Allow-Headers": True,
                    "method.response.header.Access-Control-Allow-Methods": True,
                    "method.response.header.Access-Control-Allow-Origin": True
                }
            )
        except apigw_client.exceptions.ConflictException:
            pass

        apigw_client.put_integration_response(
            restApiId=api_id,
            resourceId=res_id,
            httpMethod="OPTIONS",
            statusCode="200",
            responseParameters={
                "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                "method.response.header.Access-Control-Allow-Methods": "'GET,POST,DELETE,OPTIONS'",
                "method.response.header.Access-Control-Allow-Origin": "'*'"
            }
        )

    # Helper: Attach method with Lambda proxy integration
    def attach_method(res_id, method, lambda_name, requires_auth=True):
        auth_type = "COGNITO_USER_POOLS" if requires_auth else "NONE"
        auth_kwargs = {"authorizationType": auth_type}
        if requires_auth:
            auth_kwargs["authorizerId"] = authorizer_id

        try:
            apigw_client.put_method(
                restApiId=api_id,
                resourceId=res_id,
                httpMethod=method,
                **auth_kwargs
            )
        except apigw_client.exceptions.ConflictException:
            # Update method
            apigw_client.put_method(
                restApiId=api_id,
                resourceId=res_id,
                httpMethod=method,
                **auth_kwargs
            )

        lambda_arn = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:{lambda_name}"
        lambda_uri = f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"

        apigw_client.put_integration(
            restApiId=api_id,
            resourceId=res_id,
            httpMethod=method,
            type="AWS_PROXY",
            integrationHttpMethod="POST",
            uri=lambda_uri
        )

        # Grant Lambda invoke permission from API Gateway
        statement_id = f"apigw-{api_id}-{res_id}-{method}"
        source_arn = f"arn:aws:execute-api:{REGION}:{ACCOUNT_ID}:{api_id}/*/{method}/*"
        try:
            lambda_client.add_permission(
                FunctionName=lambda_name,
                StatementId=statement_id,
                Action="lambda:InvokeFunction",
                Principal="apigateway.amazonaws.com",
                SourceArn=f"arn:aws:execute-api:{REGION}:{ACCOUNT_ID}:{api_id}/*"
            )
        except lambda_client.exceptions.ResourceConflictException:
            pass

    # 3. Create Resource Hierarchy and Routes
    print("\nBuilding routes and resources...")

    # Route 1: /appointments
    res_appts = get_or_create_resource(root_id, "appointments")
    enable_cors(res_appts)
    attach_method(res_appts, "POST", "medibook-book-appointment", requires_auth=True)
    print("  [OK] POST   /appointments (Protected)")

    # Route 2: /appointments/mine
    res_mine = get_or_create_resource(res_appts, "mine")
    enable_cors(res_mine)
    attach_method(res_mine, "GET", "medibook-my-appointments", requires_auth=True)
    print("  [OK] GET    /appointments/mine (Protected)")

    # Route 3: /appointments/{id}
    res_appt_id = get_or_create_resource(res_appts, "{id}")
    enable_cors(res_appt_id)
    attach_method(res_appt_id, "DELETE", "medibook-cancel-appointment", requires_auth=True)
    print("  [OK] DELETE /appointments/{id} (Protected)")

    # Route 4: /doctors
    res_docs = get_or_create_resource(root_id, "doctors")
    enable_cors(res_docs)
    attach_method(res_docs, "GET", "medibook-get-doctors", requires_auth=False)
    print("  [OK] GET    /doctors (Public)")

    # Route 5: /doctors/availability
    res_avail = get_or_create_resource(res_docs, "availability")
    enable_cors(res_avail)
    attach_method(res_avail, "POST", "medibook-doctor-availability", requires_auth=True)
    print("  [OK] POST   /doctors/availability (Protected)")

    # Route 6: /doctors/today
    res_today = get_or_create_resource(res_docs, "today")
    enable_cors(res_today)
    attach_method(res_today, "GET", "medibook-doctor-today", requires_auth=True)
    print("  [OK] GET    /doctors/today (Protected)")

    # Route 7: /doctors/{id}/slots
    res_doc_id = get_or_create_resource(res_docs, "{id}")
    enable_cors(res_doc_id)
    res_slots = get_or_create_resource(res_doc_id, "slots")
    enable_cors(res_slots)
    attach_method(res_slots, "GET", "medibook-get-slots", requires_auth=False)
    print("  [OK] GET    /doctors/{id}/slots (Public)")

    # Route 8: /admin/stats
    res_admin = get_or_create_resource(root_id, "admin")
    enable_cors(res_admin)
    res_stats = get_or_create_resource(res_admin, "stats")
    enable_cors(res_stats)
    attach_method(res_stats, "GET", "medibook-admin-stats", requires_auth=True)
    print("  [OK] GET    /admin/stats (Protected)")

    # Route 9: /referrals/upload-url
    res_refs = get_or_create_resource(root_id, "referrals")
    enable_cors(res_refs)
    res_upload = get_or_create_resource(res_refs, "upload-url")
    enable_cors(res_upload)
    attach_method(res_upload, "POST", "medibook-referral-upload-url", requires_auth=True)
    print("  [OK] POST   /referrals/upload-url (Protected)")

    # 4. Deploy to Stage 'prod'
    print("\nDeploying API to stage 'prod'...")
    deployment = apigw_client.create_deployment(
        restApiId=api_id,
        stageName="prod",
        description="Production stage deployment"
    )
    invoke_url = f"https://{api_id}.execute-api.{REGION}.amazonaws.com/prod"

    print("\n" + "=" * 60)
    print(" === API Gateway Deployment Summary ===")
    print("=" * 60)
    print(f" REST API Name: {API_NAME}")
    print(f" REST API ID:   {api_id}")
    print(f" Stage:         prod")
    print(f" Invoke URL:    {invoke_url}")
    print("=" * 60)

    # Save output for frontend config
    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_info.json")
    with open(out_file, "w") as f:
        json.dump({"API_ID": api_id, "INVOKE_URL": invoke_url}, f)

if __name__ == "__main__":
    setup_api_gateway()
