# MediBook - Deployed AWS Resources

This document records the exact names, identifiers, and endpoints of all resources deployed to AWS in the **us-east-1** region for the MediBook serverless healthcare hospital system.

---

## ☁️ Environment & Account Info
- **AWS Region:** `us-east-1`
- **AWS Account ID:** `355628740179`
- **IAM User:** `medibook-admin`
- **Live CloudFront Web Portal:** [https://d34odm7mjkejmu.cloudfront.net](https://d34odm7mjkejmu.cloudfront.net)
- **API Gateway Invoke URL:** `https://067ri0xkui.execute-api.us-east-1.amazonaws.com/prod`

---

## 🗄️ DynamoDB Tables (On-Demand) — Phase 1 ✅
- **`Appointments`**
  - Partition Key: `doctorId` (String)
  - Sort Key: `slotTime` (String)
  - Status: `ACTIVE` ✅
  - ARN: `arn:aws:dynamodb:us-east-1:355628740179:table/Appointments`
- **`Doctors`**
  - Partition Key: `doctorId` (String)
  - Status: `ACTIVE` ✅
  - ARN: `arn:aws:dynamodb:us-east-1:355628740179:table/Doctors`
- **`Patients`**
  - Partition Key: `patientId` (String)
  - Status: `ACTIVE` ✅
  - ARN: `arn:aws:dynamodb:us-east-1:355628740179:table/Patients`

---

## 🪣 Amazon S3 Buckets — Phase 2 ✅
- **Referrals Bucket:** `medibook-referrals-40179-app`
  - Access: Private (Block Public Access ON) ✅
  - CORS: Configured for CloudFront domain & wildcard (`PUT`, `GET`, `POST`, `HEAD`) ✅
  - ARN: `arn:aws:s3:::medibook-referrals-40179-app`
- **Website Bucket:** `medibook-website-40179-app`
  - Access: Private (Block Public Access ON, secured with CloudFront OAC) ✅
  - Bucket Policy: Grants read access to CloudFront distribution `E2WAP3H33Z68L0` ✅
  - ARN: `arn:aws:s3:::medibook-website-40179-app`

---

## 📬 Amazon SQS — Phase 3 ✅
- **Queue Name:** `medibook-booking-events`
- **Type:** Standard Queue ✅
- **Visibility Timeout:** `30 seconds`
- **Message Retention:** `4 days`
- **Queue URL:** `https://sqs.us-east-1.amazonaws.com/355628740179/medibook-booking-events` ✅
- **Queue ARN:** `arn:aws:sqs:us-east-1:355628740179:medibook-booking-events`

---

## ✉️ Amazon SES — Phase 4 ✅
- **Sender & Notification Email:** `rabbiraz123@gmail.com`
  - Verification Status: `Success` ✅
- **SES Mode:** Sandbox (Emails are enabled between verified addresses)

---

## 🔑 IAM Role — Phase 5 ✅
- **Role Name:** `medibook-lambda-role`
- **Role ARN:** `arn:aws:iam::355628740179:role/medibook-lambda-role` ✅
- **Trust Policy:** `lambda.amazonaws.com` (AWS Lambda Service)
- **Attached Policies:**
  - `AWSLambdaBasicExecutionRole` (CloudWatch Logging)
  - `medibook-lambda-permissions` (Least-privilege policy for Appointments, Doctors, Patients DynamoDB tables, S3 referrals bucket, SQS queue, SES SendEmail, and Cognito group assignment)

---

## ⚡ AWS Lambda Functions (Python 3.12) — Phase 6 ✅
All functions deployed with runtime `python3.12`, handler `lambda_function.lambda_handler`, and role `medibook-lambda-role`:

| Function Name | Environment Variables | SQS / Trigger | Test Status |
|---|---|---|---|
| `medibook-book-appointment` | `APPOINTMENTS_TABLE`: `Appointments`<br>`QUEUE_URL`: `https://sqs.us-east-1.amazonaws.com/355628740179/medibook-booking-events` | — | HTTP 200 ✅ |
| `medibook-get-doctors` | `DOCTORS_TABLE`: `Doctors` | — | HTTP 200 ✅ |
| `medibook-get-slots` | `DOCTORS_TABLE`: `Doctors`<br>`APPOINTMENTS_TABLE`: `Appointments` | — | HTTP 200 ✅ |
| `medibook-my-appointments` | `APPOINTMENTS_TABLE`: `Appointments` | — | HTTP 200 ✅ |
| `medibook-cancel-appointment` | `APPOINTMENTS_TABLE`: `Appointments`<br>`QUEUE_URL`: `https://sqs.us-east-1.amazonaws.com/355628740179/medibook-booking-events` | — | HTTP 200 ✅ |
| `medibook-doctor-availability` | `DOCTORS_TABLE`: `Doctors` | — | HTTP 200 ✅ |
| `medibook-doctor-today` | `APPOINTMENTS_TABLE`: `Appointments` | — | HTTP 200 ✅ |
| `medibook-admin-stats` | `APPOINTMENTS_TABLE`: `Appointments` | — | HTTP 200 ✅ |
| `medibook-referral-upload-url` | `REFERRAL_BUCKET`: `medibook-referrals-40179-app` | — | HTTP 200 ✅ |
| `medibook-notifier` | `SENDER_EMAIL`: `rabbiraz123@gmail.com` | **SQS Trigger Active** (`medibook-booking-events`, batch size 5) | HTTP 200 ✅ |
| `medibook-post-confirmation` | — | Connected to Cognito Post Confirmation | HTTP 200 ✅ |

---

## 👥 Amazon Cognito — Phase 7 ✅
- **User Pool Name:** `medibook-user-pool`
- **User Pool ID:** `us-east-1_WUtK6EmCF` ✅
- **App Client Name:** `medibook-web-client`
- **App Client ID:** `4706gmhndouui0i0fn20hidl5a` ✅
- **Client Secret:** None (Public browser client) ✅
- **Auth Flows:** `ALLOW_USER_PASSWORD_AUTH`, `ALLOW_REFRESH_TOKEN_AUTH`, `ALLOW_USER_SRP_AUTH` ✅
- **Groups:**
  - `patient` ✅
  - `doctor` ✅
  - `admin` ✅
- **Post Confirmation Trigger:** `arn:aws:lambda:us-east-1:355628740179:function:medibook-post-confirmation` ✅

---

## 🌐 Amazon API Gateway (REST API) — Phase 8 ✅
- **API Name:** `medibook-api`
- **API ID:** `067ri0xkui` ✅
- **Stage:** `prod` ✅
- **Invoke URL:** `https://067ri0xkui.execute-api.us-east-1.amazonaws.com/prod` ✅
- **Cognito Authorizer:** `medibook-authorizer` (ID: `7e7m2h`) ✅
- **Routes & Authentication:**
  - `POST   /appointments` ➔ `medibook-book-appointment` (Cognito Protected) ✅
  - `GET    /doctors` ➔ `medibook-get-doctors` (Public: HTTP 200) ✅
  - `GET    /doctors/{id}/slots` ➔ `medibook-get-slots` (Public: HTTP 200) ✅
  - `GET    /appointments/mine` ➔ `medibook-my-appointments` (Cognito Protected) ✅
  - `DELETE /appointments/{id}` ➔ `medibook-cancel-appointment` (Cognito Protected) ✅
  - `POST   /doctors/availability` ➔ `medibook-doctor-availability` (Cognito Protected) ✅
  - `GET    /doctors/today` ➔ `medibook-doctor-today` (Cognito Protected) ✅
  - `GET    /admin/stats` ➔ `medibook-admin-stats` (Cognito Protected) ✅
  - `POST   /referrals/upload-url` ➔ `medibook-referral-upload-url` (Cognito Protected) ✅
- **CORS:** Enabled on every resource (OPTIONS mock integration returning 200) ✅

---

## 💻 Website Hosting & S3 Sync — Phase 9 ✅
- **S3 Website Bucket:** `medibook-website-40179-app`
- **Configuration Injected:** `js/config.js` synced with live `API_URL`, `USER_POOL_ID`, and `COGNITO_CLIENT_ID`
- **Files Uploaded:** `index.html`, `login.html`, `patient.html`, `doctor.html`, `admin.html`, `css/style.css`, and JavaScript modules with proper MIME types.

---

## 🚀 Amazon CloudFront CDN — Phase 10 ✅
- **Distribution ID:** `E2WAP3H33Z68L0` ✅
- **Origin Access Control (OAC):** `medibook-website-oac` (`EOGXL90UJMYP3`) ✅
- **Origin Domain:** `medibook-website-40179-app.s3.us-east-1.amazonaws.com`
- **Distribution Domain:** `d34odm7mjkejmu.cloudfront.net` ✅
- **Live HTTPS Website URL:** [https://d34odm7mjkejmu.cloudfront.net](https://d34odm7mjkejmu.cloudfront.net) ✅
- **Viewer Protocol Policy:** Redirect HTTP to HTTPS ✅
- **Default Root Object:** `index.html` ✅

---

## 📊 Demo Seed Data & Test Users — Phase 11 ✅
- **Seed Doctors (5 total):** Dr. Sarah Jenkins (Cardiology), Dr. Michael Chen (Neurology), Dr. Emily Taylor (Pediatrics), Dr. Marcus Johnson (Orthopedics), Dr. Olivia Patel (Dermatology).
- **Historical Seed Appointments (20 total):** Populated across departments with varying statuses (`CONFIRMED`, `NO_SHOW`).
- **Cognito Demo Users:**
  | Role | Email | Password | Group |
  |---|---|---|---|
  | **Patient** | `patient@medibook.hospital` | `Password123!` | `patient` |
  | **Doctor** | `doctor@medibook.hospital` | `Password123!` | `doctor` |
  | **Admin** | `admin@medibook.hospital` | `Password123!` | `admin` |
  | **Patient (SES Verified)** | `rabbiraz123@gmail.com` | `Password123!` | `patient` |

---

## 🔔 Amazon SNS & CloudWatch Monitoring — Phase 12 ✅
- **SNS Topic Name:** `medibook-alarms-topic`
  - Topic ARN: `arn:aws:sns:us-east-1:355628740179:medibook-alarms-topic` ✅
  - Subscription: `rabbiraz123@gmail.com` (Email alert notification) ✅
- **CloudWatch Metric Alarm:**
  - Name: `MediBook-Lambda-Error-Alarm` ✅
  - Metric: `AWS/Lambda` > `Errors` for `medibook-book-appointment`
  - Condition: `>= 1` error within 5 minutes (`Period=300`)
  - Action: Dispatches alert to `medibook-alarms-topic`
- **CloudWatch Log Groups:** All 11 `/aws/lambda/medibook-*` log groups active and recording execution telemetry.

---

## 🧪 Comprehensive System Test Results (Phase 13) ✅
All 11 automated verification tests passed against the live cloud infrastructure (`python medibook/deploy/scripts/13_system_tests.py`):

| Test ID | Test Category | Detailed Description | Result |
|---|---|---|---|
| **T0** | CloudFront CDN | Fetch `https://d34odm7mjkejmu.cloudfront.net/index.html` over HTTPS | **PASS** (HTTP 200) ✅ |
| **T1** | Cognito Auth | Initiate `USER_PASSWORD_AUTH` flow & acquire JWT ID tokens for patient, doctor, and admin | **PASS** ✅ |
| **T2** | Public Discovery | `GET /doctors` returns 5 doctors and `GET /doctors/{id}/slots` returns active slots | **PASS** (HTTP 200) ✅ |
| **T3** | Booking Flow | `POST /appointments` creates new appointment in DynamoDB & queues event | **PASS** (HTTP 201) ✅ |
| **T4** | Anti-Double-Booking | Duplicate `POST /appointments` for same doctor/slot triggers DynamoDB condition check | **PASS** (HTTP 409 Conflict) ✅ |
| **T5** | Event Notification | SQS queue connectivity & notification trigger to `medibook-notifier` Lambda | **PASS** ✅ |
| **T6** | Cancellation | `DELETE /appointments/{id}` cancels appointment and frees slot | **PASS** (HTTP 200) ✅ |
| **T7** | RBAC Enforcement | Patient token attempting to call `GET /admin/stats` blocked by Cognito claims validation | **PASS** (HTTP 403 Forbidden) ✅ |
| **T8** | Doctor Portal | `POST /doctors/availability` updates schedule & `GET /doctors/today` lists doctor's appointments | **PASS** (HTTP 200) ✅ |
| **T9** | Admin Analytics | `GET /admin/stats` calculates workload, no-show rate (15%), and busiest day | **PASS** (HTTP 200) ✅ |
| **T10** | S3 Upload Presigned URL | `POST /referrals/upload-url` returns secure temporary presigned S3 PUT URL | **PASS** (HTTP 200) ✅ |

---

## 🧹 Automated Cleanup Script — Phase 14 ✅
When grading and demonstration are complete, all AWS resources can be safely deleted to incur zero cost using:
```bash
python medibook/deploy/scripts/99_cleanup.py
# or bash:
bash medibook/deploy/scripts/99_cleanup.sh
```
The script asks for confirmation (`DELETE_ALL_MEDIBOOK`) before cleanly deleting CloudFront, S3 buckets, API Gateway, 11 Lambdas, SQS, DynamoDB tables, Cognito user pool, CloudWatch alarms, and IAM roles in reverse order.
