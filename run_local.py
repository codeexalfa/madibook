import http.server
import json
import os
import socketserver
import urllib.parse
from datetime import datetime, timedelta

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "medibook", "code", "frontend")
UPLOADS_DIR = os.path.join(BASE_DIR, "medibook", "local_referrals")

os.makedirs(UPLOADS_DIR, exist_ok=True)

# In-Memory Database (matches DynamoDB tables)
DOCTORS_DB = [
    {
        "doctorId": "doc-101",
        "name": "Dr. Sarah Jenkins",
        "department": "Cardiology",
        "room": "Room 201 - Heart Center",
        "bio": "Senior cardiologist specializing in preventative cardiovascular health.",
        "schedule": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
    },
    {
        "doctorId": "doc-102",
        "name": "Dr. Michael Chen",
        "department": "Neurology",
        "room": "Room 305 - Neuro Wing",
        "bio": "Consultant neurologist with 12 years of clinical research experience.",
        "schedule": ["09:30", "10:30", "11:30", "13:30", "14:30", "15:30"]
    },
    {
        "doctorId": "doc-103",
        "name": "Dr. Emily Taylor",
        "department": "Pediatrics",
        "room": "Room 104 - Children Pavilion",
        "bio": "Friendly pediatrician committed to gentle and child-focused care.",
        "schedule": ["08:30", "09:30", "10:30", "13:00", "14:00", "15:00"]
    },
    {
        "doctorId": "doc-104",
        "name": "Dr. Marcus Johnson",
        "department": "Orthopedics",
        "room": "Room 402 - Bone & Joint Clinic",
        "bio": "Orthopedic specialist focusing on joint restoration and sports injuries.",
        "schedule": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
    },
    {
        "doctorId": "doc-105",
        "name": "Dr. Olivia Patel",
        "department": "Dermatology",
        "room": "Room 210 - Skin & Wellness",
        "bio": "Expert dermatologist specializing in skin health and minor procedures.",
        "schedule": ["10:00", "11:00", "12:00", "14:00", "15:00", "16:00"]
    }
]

# Seed appointments for dynamic charts and stats
APPOINTMENTS_DB = []

def init_seed_data():
    today = datetime.now()
    sample_records = [
        ("doc-101", "Dr. Sarah Jenkins", "Cardiology", -4, "09:00", "CONFIRMED", "pat-1", "john.doe@example.com", "Regular checkup"),
        ("doc-101", "Dr. Sarah Jenkins", "Cardiology", -3, "10:00", "NO_SHOW", "pat-2", "alice.smith@example.com", "Chest tightness"),
        ("doc-101", "Dr. Sarah Jenkins", "Cardiology", -2, "11:00", "CONFIRMED", "pat-3", "bob.lee@example.com", "ECG review"),
        ("doc-101", "Dr. Sarah Jenkins", "Cardiology", 0, "14:00", "CONFIRMED", "pat-4", "emma.watson@example.com", "Blood pressure follow-up"),
        ("doc-102", "Dr. Michael Chen", "Neurology", -4, "09:30", "CONFIRMED", "pat-5", "clara.oswald@example.com", "Migraine consultation"),
        ("doc-102", "Dr. Michael Chen", "Neurology", -3, "11:30", "CONFIRMED", "pat-6", "david.tennant@example.com", "Nerve study"),
        ("doc-102", "Dr. Michael Chen", "Neurology", -1, "14:30", "NO_SHOW", "pat-7", "rose.tyler@example.com", "Sleep consultation"),
        ("doc-103", "Dr. Emily Taylor", "Pediatrics", -5, "08:30", "CONFIRMED", "pat-8", "sarah.parent@example.com", "Annual toddler vaccine"),
        ("doc-103", "Dr. Emily Taylor", "Pediatrics", -3, "09:30", "CONFIRMED", "pat-9", "james.parent@example.com", "Cough and cold"),
        ("doc-104", "Dr. Marcus Johnson", "Orthopedics", -4, "10:00", "CONFIRMED", "pat-10", "bruce.wayne@example.com", "Knee joint pain"),
        ("doc-104", "Dr. Marcus Johnson", "Orthopedics", -2, "14:00", "NO_SHOW", "pat-11", "clark.kent@example.com", "Shoulder strain"),
        ("doc-104", "Dr. Marcus Johnson", "Orthopedics", 0, "11:00", "CONFIRMED", "pat-12", "barry.allen@example.com", "Running injury check"),
        ("doc-105", "Dr. Olivia Patel", "Dermatology", -3, "10:00", "CONFIRMED", "pat-13", "tony.stark@example.com", "Skin rash inspection"),
        ("doc-105", "Dr. Olivia Patel", "Dermatology", -1, "11:00", "CONFIRMED", "pat-14", "steve.rogers@example.com", "Mole examination")
    ]

    for doc_id, doc_name, dept, day_offset, time_str, status, pat_id, pat_email, notes in sample_records:
        date_obj = today + timedelta(days=day_offset)
        date_str = date_obj.strftime("%Y-%m-%d")
        slot_time = f"{date_str} {time_str}"
        APPOINTMENTS_DB.append({
            "doctorId": doc_id,
            "slotTime": slot_time,
            "appointmentId": f"{doc_id}_{slot_time}".replace(" ", "_"),
            "doctorName": doc_name,
            "patientId": pat_id,
            "patientEmail": pat_email,
            "department": dept,
            "notes": notes,
            "status": status,
            "createdAt": date_str
        })

init_seed_data()

class MediBookLocalHandler(http.server.SimpleHTTPRequestHandler):
    def send_cors_headers(self, status_code=200, content_type="application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,DELETE,PUT,OPTIONS")

    def do_OPTIONS(self):
        self.send_cors_headers(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. API: List Doctors
        if path == "/api/doctors":
            dept = query.get("dept", [None])[0]
            docs = [d for d in DOCTORS_DB if not dept or d["department"] == dept]
            self.send_cors_headers(200)
            self.end_headers()
            self.wfile.write(json.dumps({"doctors": docs}).encode("utf-8"))
            return

        # 2. API: Get Doctor Slots
        if path.startswith("/api/doctors/") and path.endswith("/slots"):
            doc_id = path.replace("/api/doctors/", "").replace("/slots", "")
            target_date = query.get("date", [datetime.now().strftime("%Y-%m-%d")])[0]

            doctor = next((d for d in DOCTORS_DB if d["doctorId"] == doc_id), None)
            if not doctor:
                self.send_cors_headers(404)
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Doctor not found"}).encode("utf-8"))
                return

            daily_times = doctor.get("schedule", ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"])
            all_slots = [f"{target_date} {t}" for t in daily_times]

            taken_slots = set(
                a["slotTime"] for a in APPOINTMENTS_DB 
                if a["doctorId"] == doc_id and a["status"] != "CANCELLED"
            )
            free_slots = [s for s in all_slots if s not in taken_slots]

            self.send_cors_headers(200)
            self.end_headers()
            self.wfile.write(json.dumps({
                "doctorId": doc_id,
                "doctorName": doctor["name"],
                "date": target_date,
                "freeSlots": free_slots
            }).encode("utf-8"))
            return

        # 3. API: My Appointments
        if path == "/api/appointments/mine":
            active_apps = [a for a in APPOINTMENTS_DB if a["status"] != "CANCELLED"]
            active_apps.sort(key=lambda x: x.get("slotTime", ""))
            self.send_cors_headers(200)
            self.end_headers()
            self.wfile.write(json.dumps({"appointments": active_apps}).encode("utf-8"))
            return

        # 4. API: Doctor Today's Schedule
        if path == "/api/doctors/today":
            today_str = query.get("date", [datetime.now().strftime("%Y-%m-%d")])[0]
            doc_id = query.get("doctorId", ["doc-101"])[0]

            apps = [
                a for a in APPOINTMENTS_DB 
                if a.get("slotTime", "").startswith(today_str) and a["status"] != "CANCELLED"
            ]
            self.send_cors_headers(200)
            self.end_headers()
            self.wfile.write(json.dumps({
                "date": today_str,
                "totalToday": len(apps),
                "appointments": apps
            }).encode("utf-8"))
            return

        # 5. API: Admin Stats
        if path == "/api/admin/stats":
            dept_counts = {}
            day_counts = {"Monday": 0, "Tuesday": 0, "Wednesday": 0, "Thursday": 0, "Friday": 0, "Saturday": 0, "Sunday": 0}
            total = len(APPOINTMENTS_DB)
            no_show = sum(1 for a in APPOINTMENTS_DB if a["status"] == "NO_SHOW")
            cancelled = sum(1 for a in APPOINTMENTS_DB if a["status"] == "CANCELLED")
            confirmed = total - no_show - cancelled

            for a in APPOINTMENTS_DB:
                dept = a.get("department", "General")
                dept_counts[dept] = dept_counts.get(dept, 0) + 1
                slot = a.get("slotTime", "")
                if len(slot) >= 10:
                    try:
                        d_name = datetime.strptime(slot[:10], "%Y-%m-%d").strftime("%A")
                        if d_name in day_counts:
                            day_counts[d_name] += 1
                    except Exception:
                        pass

            busiest = max(day_counts, key=day_counts.get)
            busiest_count = day_counts[busiest]
            no_show_rate = round((no_show / total * 100), 1) if total > 0 else 0

            dept_table = [
                {"department": d, "bookings": c, "percentage": f"{round((c/total*100), 1) if total > 0 else 0}%"}
                for d, c in dept_counts.items()
            ]

            self.send_cors_headers(200)
            self.end_headers()
            self.wfile.write(json.dumps({
                "totalAppointments": total,
                "confirmedCount": confirmed,
                "noShowCount": no_show,
                "cancelledCount": cancelled,
                "noShowRate": f"{no_show_rate}%",
                "busiestDay": busiest,
                "busiestDayCount": busiest_count,
                "bookingsPerDepartment": dept_counts,
                "bookingsPerDay": day_counts,
                "departmentTable": dept_table
            }).encode("utf-8"))
            return

        # Serve static frontend files
        clean_path = path.lstrip("/")
        if clean_path == "" or clean_path == "index.html":
            target_file = os.path.join(FRONTEND_DIR, "index.html")
        else:
            target_file = os.path.join(FRONTEND_DIR, clean_path)

        if os.path.exists(target_file) and os.path.isfile(target_file):
            content_type = "text/html"
            if target_file.endswith(".css"):
                content_type = "text/css"
            elif target_file.endswith(".js"):
                content_type = "application/javascript"
            elif target_file.endswith(".json"):
                content_type = "application/json"
            elif target_file.endswith(".png"):
                content_type = "image/png"
            elif target_file.endswith(".jpg"):
                content_type = "image/jpeg"

            self.send_cors_headers(200, content_type)
            self.end_headers()
            with open(target_file, "rb") as f:
                self.wfile.write(f.read())
            return

        # Fallback to default handler
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        data = json.loads(body) if body else {}

        # 1. API: Book Appointment (Anti-Double-Booking Guard)
        if path == "/api/appointments":
            doc_id = data.get("doctorId")
            slot_time = data.get("slotTime")

            # Check if already booked (simulates DynamoDB conditional check)
            existing = next(
                (a for a in APPOINTMENTS_DB if a["doctorId"] == doc_id and a["slotTime"] == slot_time and a["status"] != "CANCELLED"),
                None
            )

            if existing:
                print(f"[REJECTED] Double booking prevented for {doc_id} at {slot_time}!")
                self.send_cors_headers(409)
                self.end_headers()
                self.wfile.write(json.dumps({"message": "This slot is already taken"}).encode("utf-8"))
                return

            app_id = f"{doc_id}_{slot_time}".replace(" ", "_")
            new_app = {
                "doctorId": doc_id,
                "slotTime": slot_time,
                "appointmentId": app_id,
                "doctorName": data.get("doctorName", "Doctor"),
                "patientId": data.get("patientId", "local-patient"),
                "patientEmail": data.get("patientEmail", "patient@example.com"),
                "department": data.get("department", "General"),
                "notes": data.get("notes", ""),
                "status": "CONFIRMED",
                "createdAt": slot_time[:10]
            }
            APPOINTMENTS_DB.append(new_app)
            print(f"[CONFIRMED] Booked appointment {app_id} - [Simulated SQS Event Dispatched!]")

            self.send_cors_headers(201)
            self.end_headers()
            self.wfile.write(json.dumps({"message": "Booked!", "appointment": new_app}).encode("utf-8"))
            return

        # 2. API: Doctor Save Availability
        if path == "/api/doctors/availability":
            doc_id = data.get("doctorId", "doc-101")
            schedule = data.get("schedule", [])
            for d in DOCTORS_DB:
                if d["doctorId"] == doc_id:
                    d["schedule"] = schedule
                    break
            self.send_cors_headers(200)
            self.end_headers()
            self.wfile.write(json.dumps({"message": "Availability updated", "schedule": schedule}).encode("utf-8"))
            return

        # 3. API: S3 Presigned Upload URL Simulation
        if path == "/api/referrals/upload-url":
            filename = data.get("fileName", "referral.pdf").replace(" ", "_")
            upload_url = f"http://localhost:{PORT}/local-upload/{filename}"
            self.send_cors_headers(200)
            self.end_headers()
            self.wfile.write(json.dumps({
                "message": "Presigned URL generated",
                "uploadUrl": upload_url,
                "fileKey": f"referrals/{filename}"
            }).encode("utf-8"))
            return

        self.send_cors_headers(404)
        self.end_headers()
        self.wfile.write(json.dumps({"message": "API route not found"}).encode("utf-8"))

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/appointments/"):
            app_id = path.replace("/api/appointments/", "")
            for a in APPOINTMENTS_DB:
                if a["appointmentId"] == app_id or app_id in a["appointmentId"]:
                    a["status"] = "CANCELLED"
                    print(f"[CANCELLED] Appointment {app_id} cancelled - [Simulated SQS Event Dispatched!]")
                    break

            self.send_cors_headers(200)
            self.end_headers()
            self.wfile.write(json.dumps({"message": "Appointment cancelled successfully"}).encode("utf-8"))
            return

        self.send_cors_headers(404)
        self.end_headers()

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/local-upload/"):
            filename = path.replace("/local-upload/", "")
            length = int(self.headers.get("Content-Length", 0))
            file_data = self.rfile.read(length)

            save_path = os.path.join(UPLOADS_DIR, filename)
            with open(save_path, "wb") as f:
                f.write(file_data)

            print(f"[UPLOADED] Referral document saved to: {save_path}")
            self.send_cors_headers(200)
            self.end_headers()
            self.wfile.write(json.dumps({"message": "Uploaded to local S3 simulation successfully"}).encode("utf-8"))
            return

        self.send_cors_headers(404)
        self.end_headers()

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), MediBookLocalHandler) as httpd:
        print("=" * 60)
        print(f" [ONLINE] MediBook Full Stack Server Running Locally!")
        print("=" * 60)
        print(f" Web Portal:         http://localhost:{PORT}/")
        print(f" Patient Portal:     http://localhost:{PORT}/patient.html")
        print(f" Doctor Portal:      http://localhost:{PORT}/doctor.html")
        print(f" Admin Dashboard:    http://localhost:{PORT}/admin.html")
        print(f" Login & Register:   http://localhost:{PORT}/login.html")
        print("=" * 60)
        print(" Press Ctrl+C in your terminal to stop the server.")
        httpd.serve_forever()
