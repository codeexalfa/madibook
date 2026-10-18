import os
import boto3
from datetime import datetime, timedelta

# Table names from environment or default names
DOCTORS_TABLE = os.environ.get("DOCTORS_TABLE", "Doctors")
APPOINTMENTS_TABLE = os.environ.get("APPOINTMENTS_TABLE", "Appointments")

# Connect to DynamoDB
dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))
doctors_table = dynamodb.Table(DOCTORS_TABLE)
appointments_table = dynamodb.Table(APPOINTMENTS_TABLE)

# List of realistic fake doctors
DEMO_DOCTORS = [
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

def seed_doctors():
    print(f"--- Seeding Doctors Table ({DOCTORS_TABLE}) ---")
    for doc in DEMO_DOCTORS:
        try:
            doctors_table.put_item(Item=doc)
            print(f"Added doctor: {doc['name']} ({doc['department']})")
        except Exception as err:
            print(f"Failed to add {doc['name']}: {str(err)}")

def seed_appointments():
    print(f"\n--- Seeding Appointments Table ({APPOINTMENTS_TABLE}) ---")
    today = datetime.now()

    # Create realistic sample appointments over recent days
    sample_records = [
        # Cardiology
        ("doc-101", "Dr. Sarah Jenkins", "Cardiology", -4, "09:00", "CONFIRMED", "pat-1", "john.doe@example.com", "Regular checkup"),
        ("doc-101", "Dr. Sarah Jenkins", "Cardiology", -3, "10:00", "NO_SHOW", "pat-2", "alice.smith@example.com", "Chest tightness"),
        ("doc-101", "Dr. Sarah Jenkins", "Cardiology", -2, "11:00", "CONFIRMED", "pat-3", "bob.lee@example.com", "ECG review"),
        ("doc-101", "Dr. Sarah Jenkins", "Cardiology", 0, "14:00", "CONFIRMED", "pat-4", "emma.watson@example.com", "Blood pressure follow-up"),
        ("doc-101", "Dr. Sarah Jenkins", "Cardiology", 1, "09:00", "CONFIRMED", "demo-patient-1", "patient@example.com", "First consultation"),

        # Neurology
        ("doc-102", "Dr. Michael Chen", "Neurology", -4, "09:30", "CONFIRMED", "pat-5", "clara.oswald@example.com", "Migraine consultation"),
        ("doc-102", "Dr. Michael Chen", "Neurology", -3, "11:30", "CONFIRMED", "pat-6", "david.tennant@example.com", "Nerve study"),
        ("doc-102", "Dr. Michael Chen", "Neurology", -1, "14:30", "NO_SHOW", "pat-7", "rose.tyler@example.com", "Sleep consultation"),
        ("doc-102", "Dr. Michael Chen", "Neurology", 0, "10:30", "CONFIRMED", "pat-8", "martha.jones@example.com", "Follow up scan review"),

        # Pediatrics
        ("doc-103", "Dr. Emily Taylor", "Pediatrics", -5, "08:30", "CONFIRMED", "pat-9", "sarah.parent@example.com", "Annual toddler vaccine"),
        ("doc-103", "Dr. Emily Taylor", "Pediatrics", -3, "09:30", "CONFIRMED", "pat-10", "james.parent@example.com", "Cough and cold"),
        ("doc-103", "Dr. Emily Taylor", "Pediatrics", -2, "13:00", "CONFIRMED", "pat-11", "oliver.parent@example.com", "Nutrition check"),
        ("doc-103", "Dr. Emily Taylor", "Pediatrics", 0, "08:30", "CONFIRMED", "pat-12", "lucas.parent@example.com", "Ear discomfort"),

        # Orthopedics
        ("doc-104", "Dr. Marcus Johnson", "Orthopedics", -4, "10:00", "CONFIRMED", "pat-13", "bruce.wayne@example.com", "Knee joint pain"),
        ("doc-104", "Dr. Marcus Johnson", "Orthopedics", -2, "14:00", "NO_SHOW", "pat-14", "clark.kent@example.com", "Shoulder strain"),
        ("doc-104", "Dr. Marcus Johnson", "Orthopedics", -1, "15:00", "CONFIRMED", "pat-15", "diana.prince@example.com", "Sprained wrist recovery"),
        ("doc-104", "Dr. Marcus Johnson", "Orthopedics", 0, "11:00", "CONFIRMED", "pat-16", "barry.allen@example.com", "Running injury check"),

        # Dermatology
        ("doc-105", "Dr. Olivia Patel", "Dermatology", -3, "10:00", "CONFIRMED", "pat-17", "tony.stark@example.com", "Skin rash inspection"),
        ("doc-105", "Dr. Olivia Patel", "Dermatology", -1, "11:00", "CONFIRMED", "pat-18", "steve.rogers@example.com", "Mole examination"),
        ("doc-105", "Dr. Olivia Patel", "Dermatology", 1, "10:00", "CONFIRMED", "pat-19", "natasha.roman@example.com", "Allergy flare-up")
    ]

    for doc_id, doc_name, dept, day_offset, time_str, status, pat_id, pat_email, notes in sample_records:
        date_obj = today + timedelta(days=day_offset)
        date_str = date_obj.strftime("%Y-%m-%d")
        slot_time = f"{date_str} {time_str}"
        appointment_id = f"{doc_id}_{slot_time}".replace(" ", "_")

        item = {
            "doctorId": doc_id,
            "slotTime": slot_time,
            "appointmentId": appointment_id,
            "doctorName": doc_name,
            "patientId": pat_id,
            "patientEmail": pat_email,
            "department": dept,
            "notes": notes,
            "status": status,
            "createdAt": date_str
        }

        try:
            appointments_table.put_item(Item=item)
            print(f"Added appointment: {doc_name} | {slot_time} | {dept} | {status}")
        except Exception as err:
            print(f"Failed to add appointment: {str(err)}")

if __name__ == "__main__":
    print("==================================================")
    print(" MediBook: Seeding Fake Doctors and Appointments")
    print("==================================================")
    seed_doctors()
    seed_appointments()
    print("\n[OK] Seeding complete! The admin dashboard and doctor booking are ready to test.")
