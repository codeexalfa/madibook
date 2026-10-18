# MediBook - Complete AWS Setup Guide (Beginner Walkthrough)

This guide takes you step-by-step through setting up **MediBook** entirely using the **AWS Management Console (website)**.
All steps are designed for complete beginners and tested in the **us-east-1 (N. Virginia)** region.

> **Important Note for Your University Submission:**
> Look for the **📸 Take a screenshot here:** markers throughout this guide. Capture these screens for your report, architecture documentation, and video demonstration.

---

## 🧭 Pre-Flight Checklist: Region Selection
Before starting, log in to the [AWS Management Console](https://console.aws.amazon.com/). In the top-right corner of the AWS navigation bar, check the Region dropdown and select:
- **US East (N. Virginia) `us-east-1`**
Keep all services in this same region.

---

## Step 1: AWS Account, Safe IAM Admin User & Billing Alarm

1. **Log in to AWS:**
   - Log in using your root account email and password.
2. **Create a safe IAM Admin User:**
   - Type **IAM** in the top search bar and click **IAM**.
   - In the left sidebar, click **Users** ➔ Click **Create user**.
   - User name: `medibook-admin`
   - Check **Provide user access to the AWS Management Console**.
   - Select **I want to create an IAM-user** and set a password.
   - Click **Next**.
   - Select **Attach policies directly** ➔ Check **AdministratorAccess** ➔ Click **Next** ➔ Click **Create user**.
   - Download the credentials .csv or save your password safely.
   - Log out of root and log in as `medibook-admin`.
3. **Set a Zero-Spend / Low Billing Alarm:**
   - Type **CloudWatch** in the search bar and open it.
   - In the left menu, click **Alarms** ➔ **Billing** ➔ Click **Create alarm**.
   - Metric: EstimatedCharges (Currency: USD).
   - Threshold: Static, Greater than `$5` (or `$10`).
   - Action: Select or create an SNS topic with your student email address.
   - Click **Next**, name it `MediBook-Billing-Alert`, and click **Create alarm**.
   - Check your student email and click **Confirm subscription**.

> 📸 **Take a screenshot here:** The CloudWatch Billing Alarm page showing the `$5` threshold and status `OK`.

---

## Step 2: Create the 3 DynamoDB Tables

Open **DynamoDB** from the AWS console search bar.

### Table 1: Appointments
1. Click **Create table**.
2. Table name: `MediBook-Appointments`
3. Partition key: `doctorId` (Type: **String**)
4. Sort key: `slotTime` (Type: **String**)
5. Table settings: Select **Customize settings**.
6. Read/write capacity settings: Select **On-demand** (this is completely free for low student traffic and incurs zero hourly idle costs).
7. Click **Create table**.

### Table 2: Doctors
1. Click **Create table**.
2. Table name: `MediBook-Doctors`
3. Partition key: `doctorId` (Type: **String**)
4. Sort key: *(Leave empty)*
5. Table settings: Select **Customize settings** ➔ **On-demand**.
6. Click **Create table**.

### Table 3: Patients
1. Click **Create table**.
2. Table name: `MediBook-Patients`
3. Partition key: `patientId` (Type: **String**)
4. Sort key: *(Leave empty)*
5. Table settings: Select **Customize settings** ➔ **On-demand**.
6. Click **Create table**.

> 📸 **Take a screenshot here:** The DynamoDB **Tables** list showing all 3 tables with Status `Active` and Partition/Sort keys visible.

---

## Step 3: Create the 2 Amazon S3 Buckets

Open **S3** from the top search bar. Note: S3 bucket names are globally unique across all AWS accounts, so append your student ID or initials.

### Bucket 1: Referral Documents Bucket
1. Click **Create bucket**.
2. Bucket name: `medibook-referrals-YOUR_NAME` (example: `medibook-referrals-john101`).
3. AWS Region: **US East (N. Virginia) us-east-1**.
4. Block Public Access settings: **Keep "Block all public access" CHECKED** (referral medical records must be strictly private; uploads and downloads use presigned URLs).
5. Bucket Versioning: Disable.
6. Encryption: Server-side encryption with Amazon S3 managed keys (SSE-S3).
7. Click **Create bucket**.
8. **Configure CORS for Referral Uploads:**
   - Click on your newly created referral bucket name.
   - Click the **Permissions** tab.
   - Scroll down to **Cross-origin resource sharing (CORS)** and click **Edit**.
   - Paste the following configuration:
     ```json
     [
       {
         "AllowedHeaders": ["*"],
         "AllowedMethods": ["GET", "PUT", "POST", "HEAD"],
         "AllowedOrigins": ["*"],
         "ExposeHeaders": ["ETag"]
       }
     ]
     ```
   - Click **Save changes**.

### Bucket 2: Static Website Bucket
1. Click **Create bucket**.
2. Bucket name: `medibook-website-YOUR_NAME` (example: `medibook-website-john101`).
3. AWS Region: **US East (N. Virginia) us-east-1**.
4. Block Public Access settings: **Keep "Block all public access" CHECKED** (we will safely serve it via CloudFront Origin Access Control without exposing the bucket to the raw public internet).
5. Click **Create bucket**.

> 📸 **Take a screenshot here:** The S3 Buckets list showing both buckets created, and the Referral Bucket Permissions tab showing the saved CORS JSON.

---

## Step 4: Create the Amazon SQS Queue

Open **Simple Queue Service (SQS)** from the console search bar.

1. Click **Create queue**.
2. Type: Select **Standard**.
3. Name: `medibook-booking-events`
4. Configuration:
   - Visibility timeout: `30 seconds`
   - Message retention period: `4 days`
   - Delivery delay: `0 seconds`
5. Encryption: Amazon SQS key (SSE-SQS).
6. Click **Create queue**.
7. Note down the **URL** (e.g., `https://sqs.us-east-1.amazonaws.com/123456789012/medibook-booking-events`).

> 📸 **Take a screenshot here:** The `medibook-booking-events` SQS queue details page showing the URL, Type (Standard), and ARN.

---

## Step 5: Verify Sender & Test Email in Amazon SES

Open **Amazon Simple Email Service (SES)** from the console search bar.

> **Note on SES Sandbox:**
> New AWS accounts start in SES Sandbox mode. In sandbox mode, SES can only send emails **FROM** verified email addresses **TO** verified email addresses.

1. In the left menu, under **Configuration**, click **Identities**.
2. Click **Create identity**.
3. Identity type: Select **Email address**.
4. Email address: Enter your personal email address (e.g. `yourname@gmail.com`).
5. Click **Create identity**.
6. Open your email inbox, find the verification email from Amazon Web Services, and click the confirmation link.
7. Return to the AWS SES Console and refresh the page. The identity status will change to **Verified** in green.
8. *(Optional)* If you want to receive booking emails at a second test email address, repeat these steps to verify that second email address too.

> 📸 **Take a screenshot here:** The SES **Identities** table displaying your email address with the green **Verified** badge.

---

## Step 6: Create the Lambda IAM Role & Deploy the 11 Functions

### 6.1 Create the Unified Lambda Execution Role
Open **IAM** from the search bar ➔ Click **Roles** ➔ Click **Create role**.
1. Trusted entity type: **AWS service**.
2. Use case: Select **Lambda** ➔ Click **Next**.
3. Search and attach the following standard AWS managed policies:
   - `AWSLambdaBasicExecutionRole` (writes logs to CloudWatch)
   - `AmazonDynamoDBFullAccess` (queries, updates, and conditional writes)
   - `AmazonSQSFullAccess` (sends and consumes messages)
   - `AmazonSESFullAccess` (dispatches confirmation emails)
   - `AmazonS3FullAccess` (generates presigned URLs)
   - `AmazonCognitoPowerUser` (for post_confirmation Lambda to add users to groups)
4. Click **Next**.
5. Role name: `MediBook-Lambda-Role`
6. Click **Create role**.

### 6.2 Generate Your Lambda Zip Files
On your local computer, open a terminal in the project directory and run:
```bash
python medibook/deploy/make_zips.py
```
This generates all 11 zip files inside `medibook/deploy/zips/`.

### 6.3 Create Each Lambda Function
Open **Lambda** in the AWS Console. For each function below:
1. Click **Create function**.
2. Select **Author from scratch**.
3. Runtime: **Python 3.12**.
4. Architecture: **x86_64**.
5. Under **Permissions** ➔ Change default execution role ➔ Select **Use an existing role** ➔ Pick `MediBook-Lambda-Role`.
6. Click **Create function**.
7. In the **Code** tab, click **Upload from** ➔ Select **.zip file** ➔ Upload the corresponding file from `medibook/deploy/zips/`.
8. Click the **Configuration** tab:
   - Click **Environment variables** ➔ Click **Edit** ➔ Click **Add environment variable** and enter the variables specified in the table below.
   - Click **Save**.

#### 📋 Function Matrix & Environment Variables:

| # | Function Name | Upload Zip File | Environment Variables to Add |
|---|---|---|---|
| 1 | `medibook-book-appointment` | `book_appointment.zip` | `APPOINTMENTS_TABLE`: `MediBook-Appointments`<br>`QUEUE_URL`: *(Your SQS URL from Step 4)* |
| 2 | `medibook-get-doctors` | `get_doctors.zip` | `DOCTORS_TABLE`: `MediBook-Doctors` |
| 3 | `medibook-get-slots` | `get_slots.zip` | `DOCTORS_TABLE`: `MediBook-Doctors`<br>`APPOINTMENTS_TABLE`: `MediBook-Appointments` |
| 4 | `medibook-my-appointments` | `my_appointments.zip` | `APPOINTMENTS_TABLE`: `MediBook-Appointments` |
| 5 | `medibook-cancel-appointment` | `cancel_appointment.zip` | `APPOINTMENTS_TABLE`: `MediBook-Appointments`<br>`QUEUE_URL`: *(Your SQS URL)* |
| 6 | `medibook-doctor-availability`| `doctor_availability.zip`| `DOCTORS_TABLE`: `MediBook-Doctors` |
| 7 | `medibook-doctor-today` | `doctor_today.zip` | `APPOINTMENTS_TABLE`: `MediBook-Appointments` |
| 8 | `medibook-admin-stats` | `admin_stats.zip` | `APPOINTMENTS_TABLE`: `MediBook-Appointments` |
| 9 | `medibook-referral-upload-url`| `referral_upload_url.zip`| `REFERRAL_BUCKET`: *(Your S3 Referral Bucket Name)* |
| 10| `medibook-notifier` | `notifier.zip` | `SENDER_EMAIL`: *(Your verified SES email)* |
| 11| `medibook-post-confirmation` | `post_confirmation.zip` | *(No custom environment variables needed)* |

### 6.4 Attach SQS Trigger to `medibook-notifier`
1. Open the `medibook-notifier` Lambda function.
2. Under the **Function overview** section at the top, click **+ Add trigger**.
3. Select **SQS** as the source.
4. SQS queue: Select `medibook-booking-events`.
5. Batch size: `5`.
6. Check **Activate trigger**.
7. Click **Add**.

> 📸 **Take a screenshot here:** The `medibook-notifier` function overview showing the SQS trigger attached, and the Lambda Functions list page showing all 11 functions.

---

## Step 7: Create the Cognito User Pool & App Client

Open **Cognito** from the search bar ➔ Click **Create user pool**.

1. **Step 1: Configure sign-in experience**
   - Cognite user pool sign-in options: Check **Email**.
   - Click **Next**.
2. **Step 2: Configure security requirements**
   - Password policy: Select **Cognito defaults** (or custom with 8 characters minimum).
   - Multi-factor authentication (MFA): Select **No MFA** (for straightforward university demo testing).
   - User account recovery: Check **Enable self-service account recovery** ➔ **Email only**.
   - Click **Next**.
3. **Step 3: Configure sign-up experience**
   - Self-service sign-up: Check **Enable self-registration**.
   - Attribute verification: Select **Send email message, verify email address**.
   - Required attributes: Check **name** and **email**.
   - Click **Next**.
4. **Step 4: Configure message delivery**
   - Email provider: Select **Send email with Cognito** (free 50 emails/day, no setup required).
   - Click **Next**.
5. **Step 5: Integrate your app**
   - User pool name: `MediBook-UserPool`
   - Initial app client: Select **Public client**.
   - App client name: `medibook-web-client`
   - Client secret: Select **Don't generate a client secret** *(CRITICAL: Web browsers cannot store client secrets!)*.
   - Authentication flows: Click **Advanced authentication flows** dropdown ➔ Check **ALLOW_USER_PASSWORD_AUTH** and **ALLOW_REFRESH_TOKEN_AUTH**.
   - Click **Next**.
6. **Step 6: Review and create**
   - Scroll to the bottom and click **Create user pool**.

### 7.1 Create the 3 User Groups (patient, doctor, admin)
1. Click on `MediBook-UserPool`.
2. Click the **Groups** tab ➔ Click **Create group**.
   - Group name: `patient` ➔ Click **Create group**.
3. Click **Create group** again.
   - Group name: `doctor` ➔ Click **Create group**.
4. Click **Create group** again.
   - Group name: `admin` ➔ Click **Create group**.

### 7.2 Attach `post_confirmation` Lambda Trigger
1. In `MediBook-UserPool`, click the **User pool properties** tab.
2. Scroll down to **Lambda triggers** ➔ Click **Add Lambda trigger**.
3. Trigger type: Select **Sign-up** ➔ Check **Post confirmation trigger**.
4. Assign Lambda function: Select `medibook-post-confirmation`.
5. Click **Add Lambda trigger**.

### 7.3 Copy Your Cognito IDs
Copy down:
- **User Pool ID** (e.g. `us-east-1_aBcDeFg12`) from the User Pool overview.
- **App Client ID** (e.g. `1234567890abcdefghijklmnop`) from the **App integration** tab under App clients.

> 📸 **Take a screenshot here:** The Cognito **Groups** tab showing `patient`, `doctor`, and `admin`, and the **Lambda triggers** section showing the Post Confirmation trigger attached.

---

## Step 8: Create the API Gateway REST API, Routes & Authorizer

Open **API Gateway** from the search bar.

### 8.1 Create the REST API
1. Scroll to **REST API** (do NOT choose HTTP API or WebSocket) ➔ Click **Build**.
2. Choose the protocol: **REST**.
3. Create new API: **New API**.
4. API name: `MediBook-API`
5. Endpoint Type: **Regional**.
6. Click **Create API**.

### 8.2 Create the Cognito Authorizer
1. In the left sidebar of your API, click **Authorizers** ➔ Click **Create authorizer**.
2. Authorizer name: `MediBook-Cognito-Auth`
3. Authorizer type: **Cognito**.
4. Cognito user pool: Select `MediBook-UserPool`.
5. Token source: `Authorization`
6. Token validation: *(Leave empty)*
7. Click **Create authorizer**.

### 8.3 Create Resources and Methods
Click **Resources** in the left menu. Create each of the following endpoints:

#### Resource 1: `/appointments`
- Click **Create resource** ➔ Resource name: `appointments` ➔ Resource path: `appointments` ➔ Click **Create resource**.
- Click on `/appointments` ➔ Click **Create method**:
  - Method type: **POST**
  - Integration type: **Lambda function**
  - Use Lambda Proxy integration: **Check this box** (Yes)
  - Lambda Function: `medibook-book-appointment`
  - Click **Create method**.
- Select the `POST` method ➔ Click **Method request** ➔ Click **Edit**:
  - Authorization: Select `MediBook-Cognito-Auth`
  - Click **Save**.

#### Resource 2: `/appointments/mine`
- Click on `/appointments` ➔ Click **Create resource** ➔ Resource name: `mine` ➔ Path: `mine`.
- Click on `/appointments/mine` ➔ Click **Create method**:
  - Method type: **GET**
  - Proxy integration: **Checked**
  - Lambda Function: `medibook-my-appointments`
  - Method request authorization: `MediBook-Cognito-Auth`

#### Resource 3: `/appointments/{id}`
- Click on `/appointments` ➔ Click **Create resource** ➔ Resource name: `{id}` ➔ Path: `{id}`.
- Click on `/appointments/{id}` ➔ Click **Create method**:
  - Method type: **DELETE**
  - Proxy integration: **Checked**
  - Lambda Function: `medibook-cancel-appointment`
  - Method request authorization: `MediBook-Cognito-Auth`

#### Resource 4: `/doctors`
- Click on `/` (root) ➔ Click **Create resource** ➔ Resource name: `doctors`.
- Click on `/doctors` ➔ Click **Create method**:
  - Method type: **GET**
  - Proxy integration: **Checked**
  - Lambda Function: `medibook-get-doctors`
  - Method request authorization: **None** (Publicly browseable)

#### Resource 5: `/doctors/availability`
- Click on `/doctors` ➔ Click **Create resource** ➔ Resource name: `availability`.
- Click on `/doctors/availability` ➔ Click **Create method**:
  - Method type: **POST**
  - Proxy integration: **Checked**
  - Lambda Function: `medibook-doctor-availability`
  - Method request authorization: `MediBook-Cognito-Auth`

#### Resource 6: `/doctors/today`
- Click on `/doctors` ➔ Click **Create resource** ➔ Resource name: `today`.
- Click on `/doctors/today` ➔ Click **Create method**:
  - Method type: **GET**
  - Proxy integration: **Checked**
  - Lambda Function: `medibook-doctor-today`
  - Method request authorization: `MediBook-Cognito-Auth`

#### Resource 7: `/doctors/{id}` & `/doctors/{id}/slots`
- Click on `/doctors` ➔ Click **Create resource** ➔ Resource name: `{id}` ➔ Path: `{id}`.
- Click on `/doctors/{id}` ➔ Click **Create resource** ➔ Resource name: `slots` ➔ Path: `slots`.
- Click on `/doctors/{id}/slots` ➔ Click **Create method**:
  - Method type: **GET**
  - Proxy integration: **Checked**
  - Lambda Function: `medibook-get-slots`
  - Method request authorization: **None** (Publicly browseable)

#### Resource 8: `/admin` & `/admin/stats`
- Click on `/` (root) ➔ Click **Create resource** ➔ Resource name: `admin`.
- Click on `/admin` ➔ Click **Create resource** ➔ Resource name: `stats`.
- Click on `/admin/stats` ➔ Click **Create method**:
  - Method type: **GET**
  - Proxy integration: **Checked**
  - Lambda Function: `medibook-admin-stats`
  - Method request authorization: `MediBook-Cognito-Auth`

#### Resource 9: `/referrals` & `/referrals/upload-url`
- Click on `/` (root) ➔ Click **Create resource** ➔ Resource name: `referrals`.
- Click on `/referrals` ➔ Click **Create resource** ➔ Resource name: `upload-url`.
- Click on `/referrals/upload-url` ➔ Click **Create method**:
  - Method type: **POST**
  - Proxy integration: **Checked**
  - Lambda Function: `medibook-referral-upload-url`
  - Method request authorization: `MediBook-Cognito-Auth`

### 8.4 Enable CORS on All Resources
For each top-level resource (`/appointments`, `/doctors`, `/admin`, `/referrals`):
1. Click on the resource name.
2. Click the **Enable CORS** button at the top right.
3. Check **DEFAULT 4XX** and **DEFAULT 5XX**.
4. Access-Control-Allow-Methods: Check `GET`, `POST`, `DELETE`, `OPTIONS`.
5. Access-Control-Allow-Headers: `'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'`.
6. Click **Save**.

### 8.5 Deploy the API
1. Click the orange **Deploy API** button.
2. Stage: Select **[New stage]**.
3. Stage name: `prod`
4. Click **Deploy**.
5. Copy your **Invoke URL** displayed at the top of the stage page:
   `https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod`

> 📸 **Take a screenshot here:** The API Gateway Resources tree showing all routes and methods, and the `prod` stage page showing the Invoke URL.

---

## Step 9: Configure `js/config.js`

Open `medibook/code/frontend/js/config.js` in your code editor and replace the placeholders with your real values:

```javascript
const CONFIG = {
    // 1. Your API Gateway Invoke URL from Step 8.5
    API_URL: "https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod",

    // 2. Your Amazon Cognito App Client ID from Step 7.3
    COGNITO_CLIENT_ID: "20abcdef1234567890ghijklmn",

    // 3. Your Amazon Cognito User Pool ID from Step 7.3
    USER_POOL_ID: "us-east-1_AbCdEfG12",

    // 4. AWS Region
    REGION: "us-east-1"
};
```

After updating `config.js`, re-run `python medibook/deploy/make_zips.py` so your `medibook/deploy/frontend_ready/js/config.js` copy is updated automatically!

---

## Step 10: Upload the Website to S3 & Create CloudFront Distribution

### 10.1 Upload Files to S3
1. Open **S3** ➔ Click on your website bucket: `medibook-website-YOUR_NAME`.
2. Click **Upload** ➔ Click **Add files** / **Add folder**.
3. Upload all the files inside `medibook/deploy/frontend_ready/`:
   - `index.html`
   - `login.html`
   - `patient.html`
   - `doctor.html`
   - `admin.html`
   - `css/style.css`
   - `js/config.js`, `js/auth.js`, `js/api.js`, `js/patient.js`, `js/doctor.js`, `js/admin.js`
4. Click **Upload**.

### 10.2 Create CloudFront Distribution
Open **CloudFront** from the search bar ➔ Click **Create distribution**.
1. **Origin domain:** Click the box and choose your website S3 bucket (`medibook-website-YOUR_NAME.s3.us-east-1.amazonaws.com`).
2. **Origin access:** Select **Origin access control settings (recommended)**.
   - Click **Create new OAC** ➔ Leave name as default ➔ Click **Create**.
3. **Default cache behavior:**
   - Viewer protocol policy: Select **Redirect HTTP to HTTPS**.
   - Allowed HTTP methods: **GET, HEAD, OPTIONS**.
4. **Web Application Firewall (WAF):** Select **Do not enable security protections** (to stay within free tier).
5. **Default root object:** Enter `index.html`.
6. Click **Create distribution**.
7. **Apply the S3 Bucket Policy (Crucial Step):**
   - CloudFront will display a yellow banner: *"The S3 bucket policy needs to be updated..."*
   - Click the **Copy policy** button in the banner.
   - Click the link to open your S3 bucket permissions in a new tab.
   - Under **Bucket policy**, click **Edit** ➔ Paste the copied policy JSON ➔ Click **Save changes**.
8. Wait 2-3 minutes for the CloudFront distribution status to change from *Deploying* to *Enabled*.
9. Copy your **Distribution domain name** (e.g. `d123456abcdef8.cloudfront.net`).
10. Open `https://d123456abcdef8.cloudfront.net` in your browser. MediBook will load securely over HTTPS!

> 📸 **Take a screenshot here:** The CloudFront distribution details page showing the Domain Name, Status (Enabled), and the browser loading MediBook on the CloudFront domain.

---

## Step 11: Seed Fake Doctors and Appointments

On your local machine, run the seed script:
```bash
python medibook/code/seed/seed_data.py
```
This populates:
- 5 specialized doctors across Cardiology, Neurology, Pediatrics, Orthopedics, and Dermatology in `MediBook-Doctors`.
- Historical appointments across the past week in `MediBook-Appointments` with varying statuses (`CONFIRMED`, `NO_SHOW`, etc.) so the Admin Dashboard charts and tables render immediately!

> 📸 **Take a screenshot here:** The terminal output showing the successful execution of `seed_data.py`.

---

## Step 12: Create Test Users for All 3 Roles

Open **Cognito** ➔ `MediBook-UserPool` ➔ Click **Users** tab.

### User 1: Patient
- You can register this patient directly from your website `login.html` page to test the real sign-up flow, or create it in the console:
  - Click **Create user**.
  - Email: `patient@example.com` (or your verified SES email address).
  - Password: `Password123!`
  - Mark email address as verified: **Checked**.
  - Click **Create user**.
  - In the **Groups** tab, add this user to the `patient` group.

### User 2: Doctor
- Click **Create user**.
- Email: `doctor@example.com`
- Password: `Password123!`
- Mark email address as verified: **Checked**.
- Click **Create user**.
- Click on the doctor user ➔ **Add to group** ➔ Select `doctor`.

### User 3: Admin
- Click **Create user**.
- Email: `admin@example.com`
- Password: `Password123!`
- Mark email address as verified: **Checked**.
- Click **Create user**.
- Click on the admin user ➔ **Add to group** ➔ Select `admin`.

> 📸 **Take a screenshot here:** The Cognito **Users** list showing all 3 users and their respective group assignments.

---

## Step 13: CloudWatch Logs & Lambda Error Alarm

Open **CloudWatch** from the search bar.

### 13.1 View Lambda Logs
1. Click **Log groups** in the left sidebar.
2. Filter for `/aws/lambda/medibook-`.
3. Click on any log group (e.g. `/aws/lambda/medibook-book-appointment`) to see execution streams, incoming requests, and print statements.

### 13.2 Create Lambda Error Alarm
1. Click **Alarms** ➔ **All alarms** ➔ Click **Create alarm**.
2. Click **Select metric** ➔ Click **Lambda** ➔ Click **By Function Name**.
3. Find `medibook-book-appointment` with MetricName **Errors**.
4. Statistic: **Sum**, Period: **5 minutes**.
5. Conditions: Static, **Greater than or equal to 1**.
6. Notification: Send notification to your email SNS topic.
7. Alarm name: `MediBook-Lambda-Error-Alarm`.
8. Click **Create alarm**.

> 📸 **Take a screenshot here:** The CloudWatch Alarm configuration page and the Log Groups list showing the `/aws/lambda/medibook-` streams.

---

## Step 14: Comprehensive System Testing

Run through this complete test sequence to verify every cloud component:

1. **User Registration & Login:**
   - Go to `login.html`. Click **Register (Patient)**.
   - Enter your name, your verified SES test email, and password. Click **Register**.
   - Enter the 6-digit verification code received by email.
   - Sign in. Verify you are automatically redirected to `patient.html`.
2. **Search Doctors & Free Slots:**
   - On `patient.html`, filter by department (e.g., Cardiology).
   - Select **Dr. Sarah Jenkins**.
   - Notice the time slots load dynamically.
3. **Book an Appointment:**
   - Select an available slot (e.g., 09:00 AM).
   - Click **Confirm Booking**.
   - Verify the success message: `"Booked! Your appointment confirmation has been emailed to you."`.
4. **Anti-Double-Booking Test (Important):**
   - Attempt to book the exact same slot again for the same doctor.
   - Verify the error message appears immediately: **`"This slot is already taken"`** (proves the DynamoDB conditional write works!).
5. **Verify Email Notification:**
   - Check your inbox. You should receive the HTML email confirmation with doctor name, appointment ID, and the **24-hour reminder notice** dispatched by SQS + SES.
6. **Upload Referral Document:**
   - On `patient.html`, click the upload dropzone and select a sample PDF or image.
   - Click **Upload Document to S3**.
   - Verify the file is uploaded directly to your private S3 bucket via the presigned URL.
7. **Cancel Appointment:**
   - In the **My Scheduled Appointments** table, click **Cancel** on your appointment.
   - Verify the slot is freed and a cancellation email notification is dispatched.
8. **Doctor Portal Test:**
   - Sign in as `doctor@example.com`.
   - Open `doctor.html`.
   - Update weekly visiting hours and click **Save Weekly Availability**.
   - Review today's schedule list.
9. **Admin Dashboard Test:**
   - Sign in as `admin@example.com`.
   - Open `admin.html`.
   - Verify the KPI summary cards (Total Bookings, No-Show Rate, Busiest Day).
   - Verify the **Chart.js Bar Chart** renders bookings across all departments.
   - Verify the department workload breakdown table displays correctly.

> 📸 **Take a screenshot here:**
> - The Patient portal showing the "Booked!" confirmation and "This slot is already taken" message.
> - The confirmation email received in your inbox.
> - The Doctor schedule table.
> - The Admin Dashboard with the Chart.js visual graph and KPI cards.

---

## Step 15: Common Errors & Troubleshooting

| Symptom / Error | Root Cause | Exact Solution |
| :--- | :--- | :--- |
| **CORS error in browser console** (`No 'Access-Control-Allow-Origin' header`) | API Gateway resource is missing the OPTIONS mock method, or Lambda didn't return CORS headers. | In API Gateway, click the resource ➔ Click **Enable CORS** ➔ Deploy the API again to `prod`. All MediBook Lambdas already return `Access-Control-Allow-Origin: *`. |
| **HTTP 401 Unauthorized** | Missing or expired Cognito token in the `Authorization` header. | Log out and sign in again on `login.html`. Verify that the Cognito Authorizer in API Gateway is attached to that method. |
| **HTTP 403 Forbidden** | Role mismatch: a user with the `patient` group tried to open a doctor or admin API. | The Lambda inspected `cognito:groups` in JWT claims and rejected the call. Log in with a user assigned to the `doctor` or `admin` Cognito group. |
| **Email not received from SES** | Amazon SES is in Sandbox mode and the recipient email has not been verified. | Open AWS SES Console ➔ Go to **Identities** ➔ Click **Create identity** ➔ Add the recipient email and click the confirmation link sent to that inbox. |
| **S3 Presigned Upload Fails (CORS / 403)** | S3 Referral bucket lacks CORS permissions or bucket name in Lambda env vars is incorrect. | Go to your referral S3 bucket ➔ **Permissions** ➔ Paste the CORS JSON from Step 3. Verify `REFERRAL_BUCKET` environment variable on `medibook-referral-upload-url` matches your bucket name. |
| **CloudFront shows 403 Access Denied** | S3 website bucket policy was not applied after creating the CloudFront distribution. | In CloudFront, open your distribution ➔ Click the **Origin** tab ➔ Click **Edit** ➔ Re-copy the bucket policy and paste it into the S3 bucket Permissions ➔ Bucket policy editor. |

---

## Step 16: Clean-Up Guide (How to Delete Everything to Incur Zero Costs)

When your course grading, video demonstration, and report are submitted, delete your resources in this order to avoid any recurring charges:

1. **CloudFront:** Open CloudFront ➔ Select your distribution ➔ Click **Disable** ➔ Wait until disabled ➔ Click **Delete**.
2. **S3 Buckets:** Open S3 ➔ Select `medibook-website-YOUR_NAME` ➔ Click **Empty** (type *permanently delete*) ➔ Click **Delete bucket**. Repeat for `medibook-referrals-YOUR_NAME`.
3. **API Gateway:** Open API Gateway ➔ Select `MediBook-API` ➔ Click **Actions** ➔ **Delete**.
4. **Lambda Functions:** Open Lambda ➔ Select all 11 `medibook-*` functions ➔ Click **Actions** ➔ **Delete**.
5. **SQS Queue:** Open SQS ➔ Select `medibook-booking-events` ➔ Click **Delete**.
6. **DynamoDB Tables:** Open DynamoDB ➔ Select all 3 tables (`MediBook-Appointments`, `MediBook-Doctors`, `MediBook-Patients`) ➔ Click **Delete table**.
7. **Cognito User Pool:** Open Cognito ➔ Select `MediBook-UserPool` ➔ Click **Delete**.
8. **CloudWatch Alarms & Logs:** Delete the `MediBook-Lambda-Error-Alarm` and delete log groups starting with `/aws/lambda/medibook-`.
9. **IAM Role:** In IAM, delete `MediBook-Lambda-Role`.

---
*Congratulations! You have successfully built, deployed, and tested MediBook, an enterprise-grade serverless healthcare system on AWS!*
