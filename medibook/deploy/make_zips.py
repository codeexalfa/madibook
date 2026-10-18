import os
import shutil
import zipfile

# Determine project paths
DEPLOY_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIBOOK_ROOT = os.path.dirname(DEPLOY_DIR)
BACKEND_DIR = os.path.join(MEDIBOOK_ROOT, "code", "backend")
FRONTEND_DIR = os.path.join(MEDIBOOK_ROOT, "code", "frontend")

ZIPS_OUTPUT_DIR = os.path.join(DEPLOY_DIR, "zips")
FRONTEND_READY_DIR = os.path.join(DEPLOY_DIR, "frontend_ready")

def ensure_clean_dir(directory_path):
    if os.path.exists(directory_path):
        shutil.rmtree(directory_path)
    os.makedirs(directory_path, exist_ok=True)

def zip_backend_lambdas():
    print("=" * 60)
    print(" [*] PACKAGING MEDIBOOK AWS LAMBDA FUNCTIONS")
    print("=" * 60)

    ensure_clean_dir(ZIPS_OUTPUT_DIR)

    if not os.path.exists(BACKEND_DIR):
        print(f"Error: Backend directory not found at {BACKEND_DIR}")
        return

    lambda_folders = [f for f in os.listdir(BACKEND_DIR) if os.path.isdir(os.path.join(BACKEND_DIR, f))]
    lambda_folders.sort()

    created_zips = []

    for folder_name in lambda_folders:
        folder_path = os.path.join(BACKEND_DIR, folder_name)
        zip_file_name = f"{folder_name}.zip"
        zip_output_path = os.path.join(ZIPS_OUTPUT_DIR, zip_file_name)

        with zipfile.ZipFile(zip_output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(".pyc") or "__pycache__" in root:
                        continue
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, arcname)

        size_kb = os.path.getsize(zip_output_path) / 1024.0
        print(f"  [OK] Created: {zip_file_name:30} ({size_kb:5.1f} KB)")
        created_zips.append(zip_output_path)

    print(f"\nSuccessfully generated {len(created_zips)} zip package(s) in:\n  -> {ZIPS_OUTPUT_DIR}\n")

def prepare_frontend_copy():
    print("=" * 60)
    print(" [*] PREPARING FRONTEND WEBSITE COPY FOR S3 UPLOAD")
    print("=" * 60)

    ensure_clean_dir(FRONTEND_READY_DIR)

    if not os.path.exists(FRONTEND_DIR):
        print(f"Error: Frontend directory not found at {FRONTEND_DIR}")
        return

    shutil.copytree(FRONTEND_DIR, FRONTEND_READY_DIR, dirs_exist_ok=True)
    print(f"  [OK] Copied static web assets to:\n  -> {FRONTEND_READY_DIR}")
    print("\nYou can upload the entire contents of 'frontend_ready' directly to your S3 website bucket!\n")

if __name__ == "__main__":
    zip_backend_lambdas()
    prepare_frontend_copy()
    print("=" * 60)
    print(" [DONE] ALL DEPLOYMENT ARTIFACTS READY!")
    print("=" * 60)
