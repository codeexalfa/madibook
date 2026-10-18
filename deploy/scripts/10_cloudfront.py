import boto3
import json
import os
import time

REGION = "us-east-1"
ACCOUNT_ID = "355628740179"
BUCKET = "medibook-website-40179-app"
REFERRALS_BUCKET = "medibook-referrals-40179-app"
ORIGIN_DOMAIN = f"{BUCKET}.s3.{REGION}.amazonaws.com"
ORIGIN_ID = f"S3-{BUCKET}"

cf_client = boto3.client("cloudfront")
s3_client = boto3.client("s3", region_name=REGION)

def setup_cloudfront():
    print("=" * 60)
    print(" === Phase 10: Setting up Amazon CloudFront CDN with OAC ===")
    print("=" * 60)

    # 1. Create or find Origin Access Control (OAC)
    oac_id = None
    oacs = cf_client.list_origin_access_controls().get("OriginAccessControlList", {}).get("Items", [])
    for o in oacs:
        if o["Name"] == "medibook-oac":
            oac_id = o["Id"]
            print(f"Found existing OAC: {oac_id}")
            break

    if not oac_id:
        print("Creating Origin Access Control (OAC)...")
        oac_resp = cf_client.create_origin_access_control(
            OriginAccessControlConfig={
                "Name": "medibook-oac",
                "Description": "OAC for MediBook website S3 bucket",
                "SigningProtocol": "sigv4",
                "SigningBehavior": "always",
                "OriginAccessControlOriginType": "s3"
            }
        )
        oac_id = oac_resp["OriginAccessControl"]["Id"]
        print(f"  [OK] Created OAC: {oac_id}")

    # 2. Check if distribution already exists
    dist_id = None
    domain_name = None
    dists = cf_client.list_distributions().get("DistributionList", {}).get("Items", [])
    for d in dists:
        for orig in d.get("Origins", {}).get("Items", []):
            if orig["DomainName"] == ORIGIN_DOMAIN:
                dist_id = d["Id"]
                domain_name = d["DomainName"]
                print(f"Found existing CloudFront Distribution: {dist_id} ({domain_name})")
                break

    if not dist_id:
        print("Creating CloudFront distribution (pointing to S3 website bucket)...")
        caller_ref = f"medibook-{int(time.time())}"
        dist_config = {
            "CallerReference": caller_ref,
            "Comment": "MediBook Static Website CDN",
            "Enabled": True,
            "DefaultRootObject": "index.html",
            "Origins": {
                "Quantity": 1,
                "Items": [
                    {
                        "Id": ORIGIN_ID,
                        "DomainName": ORIGIN_DOMAIN,
                        "OriginAccessControlId": oac_id,
                        "S3OriginConfig": {
                            "OriginAccessIdentity": ""
                        }
                    }
                ]
            },
            "DefaultCacheBehavior": {
                "TargetOriginId": ORIGIN_ID,
                "ViewerProtocolPolicy": "redirect-to-https",
                "AllowedMethods": {
                    "Quantity": 3,
                    "Items": ["GET", "HEAD", "OPTIONS"],
                    "CachedMethods": {
                        "Quantity": 2,
                        "Items": ["GET", "HEAD"]
                    }
                },
                "ForwardedValues": {
                    "QueryString": False,
                    "Cookies": {"Forward": "none"}
                },
                "MinTTL": 0,
                "DefaultTTL": 86400,
                "MaxTTL": 31536000
            }
        }

        dist_resp = cf_client.create_distribution(DistributionConfig=dist_config)
        dist_id = dist_resp["Distribution"]["Id"]
        domain_name = dist_resp["Distribution"]["DomainName"]
        print(f"  [OK] Created Distribution: {dist_id}")
        print(f"  [OK] Domain Name: https://{domain_name}")

    # 3. Apply S3 Bucket Policy allowing CloudFront OAC
    print("\nApplying CloudFront OAC policy to website bucket...")
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowCloudFrontServicePrincipalReadOnly",
                "Effect": "Allow",
                "Principal": {
                    "Service": "cloudfront.amazonaws.com"
                },
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{BUCKET}/*",
                "Condition": {
                    "StringEquals": {
                        "AWS:SourceArn": f"arn:aws:cloudfront::{ACCOUNT_ID}:distribution/{dist_id}"
                    }
                }
            }
        ]
    }
    s3_client.put_bucket_policy(
        Bucket=BUCKET,
        Policy=json.dumps(bucket_policy)
    )
    print("  [OK] S3 Bucket Policy applied successfully.")

    # 4. Tighten referral bucket CORS to CloudFront URL
    print(f"\nTightening referral bucket CORS to allowed origin: https://{domain_name}")
    cors_config = {
        "CORSRules": [
            {
                "AllowedHeaders": ["*"],
                "AllowedMethods": ["GET", "PUT", "POST", "HEAD"],
                "AllowedOrigins": [f"https://{domain_name}", "http://localhost:8000"],
                "ExposeHeaders": ["ETag"]
            }
        ]
    }
    s3_client.put_bucket_cors(
        Bucket=REFERRALS_BUCKET,
        CORSConfiguration=cors_config
    )
    print("  [OK] Referral bucket CORS updated.")

    print("\n" + "=" * 60)
    print(" === CloudFront Deployment Summary ===")
    print("=" * 60)
    print(f" Distribution ID: {dist_id}")
    print(f" Live Website:   https://{domain_name}")
    print("=" * 60)

    # Save details
    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloudfront_info.json")
    with open(out_file, "w") as f:
        json.dump({"DISTRIBUTION_ID": dist_id, "DOMAIN_NAME": domain_name, "LIVE_URL": f"https://{domain_name}"}, f)

if __name__ == "__main__":
    setup_cloudfront()
