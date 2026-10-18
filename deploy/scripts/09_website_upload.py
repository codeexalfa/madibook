import os
import shutil
import mimetypes
import boto3

REGION = "us-east-1"
BUCKET = "medibook-website-40179-app"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEPLOY_DIR = os.path.dirname(SCRIPT_DIR)
MEDIBOOK_ROOT = os.path.dirname(DEPLOY_DIR)
FRONTEND_SRC = os.path.join(MEDIBOOK_ROOT, "code", "frontend")
FRONTEND_DEPLOY = os.path.join(DEPLOY_DIR, "frontend")

s3_client = boto3.client("s3", region_name=REGION)

def upload_website():
    print("=" * 60)
    print(" === Phase 9: Uploading Static Website to Amazon S3 ===")
    print("=" * 60)

    # 1. Copy to deploy/frontend
    if os.path.exists(FRONTEND_DEPLOY):
        shutil.rmtree(FRONTEND_DEPLOY)
    shutil.copytree(FRONTEND_SRC, FRONTEND_DEPLOY)
    print(f"Copied frontend assets to: {FRONTEND_DEPLOY}")

    # 2. Upload to S3 with content types
    print(f"\nUploading files to S3 bucket '{BUCKET}'...")
    uploaded_count = 0
    for root, _, files in os.walk(FRONTEND_DEPLOY):
        for file in files:
            file_path = os.path.join(root, file)
            s3_key = os.path.relpath(file_path, FRONTEND_DEPLOY).replace("\\", "/")

            content_type = "application/octet-stream"
            if file.endswith(".html"):
                content_type = "text/html"
            elif file.endswith(".css"):
                content_type = "text/css"
            elif file.endswith(".js"):
                content_type = "application/javascript"
            elif file.endswith(".json"):
                content_type = "application/json"
            elif file.endswith(".png"):
                content_type = "image/png"
            elif file.endswith(".jpg") or file.endswith(".jpeg"):
                content_type = "image/jpeg"

            s3_client.upload_file(
                Filename=file_path,
                Bucket=BUCKET,
                Key=s3_key,
                ExtraArgs={"ContentType": content_type}
            )
            print(f"  [OK] Uploaded: {s3_key:28} ({content_type})")
            uploaded_count += 1

    print(f"\nSuccessfully uploaded {uploaded_count} file(s) to s3://{BUCKET}/")

if __name__ == "__main__":
    upload_website()
