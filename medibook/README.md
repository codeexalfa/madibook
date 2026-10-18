# MediBook 🏥 - Cloud-Based Hospital Appointment System

**MediBook** is a serverless, event-driven hospital appointment booking web application built on **Amazon Web Services (AWS)** in the **us-east-1** region for university cloud computing coursework.

---

## 🌟 Key Features by User Role

### 1. 🧑‍⚕️ Patient
- Register an account, verify with a 6-digit email code, and log in.
- Filter doctors by medical department (Cardiology, Neurology, Pediatrics, Orthopedics, Dermatology).
- View real-time available time slots for any doctor.
- **Book an appointment** with strict **anti-double-booking protection**.
- View scheduled appointments with current status.
- **Cancel an appointment** (frees the slot and triggers an email notification).
- **Upload medical referral documents** directly to a private AWS S3 bucket using **S3 Presigned URLs**.

### 2. 🩺 Doctor
- Log in with doctor credentials.
- Set standard **weekly visiting hours / daily slot availability** saved to DynamoDB.
- View **today's scheduled patient list** with patient email, time, and visit notes.

### 3. 📊 Administrator
- Log in with administrator credentials.
- Real-time **Hospital Analytics Dashboard**:
  - Total bookings count
  - Missed appointment **no-show rate** percentage
  - **Busiest day of the week** detection
  - Visual **Chart.js** bar chart of bookings per medical department
  - Detailed department workload data table

---

## ☁️ AWS Cloud Architecture

```text
[ Browser User ] 
       │
       ▼ (HTTPS)
[ Amazon CloudFront CDN ] ──► [ Amazon S3 Website Bucket (Static HTML/CSS/JS) ]
       │
       ├─► [ Amazon Cognito User Pool ] (Auth: patient, doctor, admin groups)
       │
       └─► [ Amazon API Gateway (REST API) ] (Cognito JWT Authorizer)
                 │
                 ├──► [ AWS Lambda Functions (Python 3.12) ]
                 │         │
                 │         ├──► [ Amazon DynamoDB ]
                 │         │      • MediBook-Appointments (PK: doctorId, SK: slotTime)
                 │         │      • MediBook-Doctors      (PK: doctorId)
                 │         │      • MediBook-Patients     (PK: patientId)
                 │         │
                 │         ├──► [ Amazon S3 Bucket ] (Referral Documents via Presigned URL)
                 │         │
                 │         └──► [ Amazon SQS ] (medibook-booking-events)
                 │                    │
                 │                    ▼
                 │              [ Notifier Lambda ]
                 │                    │
                 │                    ▼
                 │              [ Amazon SES ] (Confirmation & 24hr Reminder Emails)
                 │
                 └─► [ Amazon CloudWatch ] (Lambda Error Alarm & Execution Logs)
```

---

## 💡 Design Decisions & Simplest Options Chosen

1. **Zero Framework Frontend:**
   - Built entirely with plain HTML5, CSS3, and vanilla JavaScript.
   - No React, Angular, Vue, Webpack, or npm dependencies. It opens directly in any browser and can be served statically from Amazon S3.

2. **Plain `fetch` Cognito Authentication:**
   - Rather than bundling the 5MB AWS Amplify or Cognito SDK, authentication uses raw HTTP POST calls to `https://cognito-idp.us-east-1.amazonaws.com/` (`USER_PASSWORD_AUTH`, `SignUp`, `ConfirmSignUp`).

3. **Anti-Double-Booking Protection:**
   - Uses DynamoDB conditional writes:
     `ConditionExpression="attribute_not_exists(doctorId) AND attribute_not_exists(slotTime)"`
   - If two patients attempt to book the exact same slot at the exact same millisecond, DynamoDB guarantees that only one succeeds; the second receives a `ConditionalCheckFailedException` and the API responds with HTTP 409 `"This slot is already taken"`.

4. **Decoupled Asynchronous Emailing:**
   - The booking Lambda does not wait for SES email delivery. It immediately writes the booking to DynamoDB, drops an event into Amazon SQS (`medibook-booking-events`), and responds in under 50ms.
   - The `notifier` Lambda consumes SQS messages and dispatches HTML confirmation emails with 24-hour preparation reminders via Amazon SES.

5. **Direct S3 Uploads via Presigned URLs:**
   - Large PDF/image referrals never pass through API Gateway or Lambda payloads (preventing the 10MB payload limit and memory costs). The client requests a 5-minute presigned PUT URL and uploads directly to S3.

6. **Automatic Role Assignment via Post Confirmation Trigger:**
   - When a student registers on the web page, the `post_confirmation` Cognito Lambda trigger automatically adds the user to the `patient` group in Cognito.

---

## 📁 Repository Structure

```text
medibook/
├── code/
│   ├── frontend/
│   │   ├── index.html                 # Landing page & navigation
│   │   ├── login.html                 # Sign In, Sign Up & Verification code
│   │   ├── patient.html               # Doctor search, slots, booking, referrals
│   │   ├── doctor.html                # Availability editor & daily appointments
│   │   ├── admin.html                 # Analytics dashboard with Chart.js
│   │   ├── css/
│   │   │   └── style.css              # Hospital blue/white responsive stylesheet
│   │   └── js/
│   │       ├── config.js              # AWS endpoint & Cognito ID placeholders
│   │       ├── auth.js                # Plain-fetch Cognito authentication
│   │       ├── api.js                 # Authenticated REST API client
│   │       ├── patient.js             # Patient portal actions
│   │       ├── doctor.js              # Doctor portal actions
│   │       └── admin.js               # Admin dashboard rendering
│   ├── backend/
│   │   ├── book_appointment/         # DynamoDB conditional write + SQS event
│   │   ├── get_doctors/              # List doctors with optional ?dept=
│   │   ├── get_slots/                # Calculate free slots
│   │   ├── my_appointments/          # Logged-in patient appointments
│   │   ├── cancel_appointment/       # Cancel slot + SQS cancel event
│   │   ├── doctor_availability/      # Doctor weekly availability save
│   │   ├── doctor_today/             # Doctor's appointments for today
│   │   ├── admin_stats/              # Hospital KPI calculations
│   │   ├── referral_upload_url/      # S3 presigned PUT URL generator
│   │   ├── notifier/                 # SQS consumer -> SES email dispatcher
│   │   └── post_confirmation/        # Cognito trigger auto-assigns 'patient'
│   └── seed/
│       └── seed_data.py               # Populates fake doctors & appointments
├── deploy/
│   ├── make_zips.py                   # Automated zip packager for all Lambdas
│   ├── zips/                          # Ready-to-upload Lambda .zip packages
│   └── frontend_ready/                # Ready-to-upload S3 static website files
├── images/
│   └── .gitkeep                       # Put your report and video screenshots here
├── README.md                          # Project documentation (this file)
└── AWS_SETUP_GUIDE.md                 # 16-step AWS Console walkthrough
```

---

## 🔌 REST API Specification

All responses include CORS headers (`Access-Control-Allow-Origin: *`).

| Method | Route | Auth / Role | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/appointments` | Patient | Books an appointment slot (anti-double-booking) |
| `GET` | `/doctors` | Any User | Lists doctors (optional `?dept=Cardiology`) |
| `GET` | `/doctors/{id}/slots` | Any User | Returns free slots for a doctor on a date |
| `GET` | `/appointments/mine` | Patient | Returns all appointments for current patient |
| `DELETE` | `/appointments/{id}` | Patient | Cancels an appointment and frees the slot |
| `POST` | `/doctors/availability` | Doctor / Admin | Saves weekly available time slots |
| `GET` | `/doctors/today` | Doctor / Admin | Lists appointments for the doctor for today |
| `GET` | `/admin/stats` | Admin | Returns bookings by dept, busiest day, no-show rate |
| `POST` | `/referrals/upload-url` | Patient | Generates an S3 presigned PUT upload URL |

---

## 🚀 Quick Start Guide

### 1. Package the Code
From your terminal:
```bash
python medibook/deploy/make_zips.py
```
This automatically produces:
- 11 zipped Lambda archives in `medibook/deploy/zips/`
- Static website ready in `medibook/deploy/frontend_ready/`

### 2. Follow the AWS Deployment Walkthrough
Open [AWS_SETUP_GUIDE.md](AWS_SETUP_GUIDE.md) and follow steps 1 through 16 to set up your AWS resources in the AWS Console.

### 3. Seed Demo Data
Once your DynamoDB tables and AWS credentials are ready:
```bash
python medibook/code/seed/seed_data.py
```
This loads 5 realistic doctors across 5 departments and historical appointments so your Admin dashboard shows charts immediately!
