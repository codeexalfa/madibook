import json
import os
import boto3

# Get sender email address from environment variables
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "noreply@medibook.hospital.com")

# Connect to Amazon SES
ses_client = boto3.client("ses", region_name=os.environ.get("AWS_REGION", "us-east-1"))

def lambda_handler(event, context):
    # The notifier is triggered by Amazon SQS
    records = event.get("Records", [])
    print(f"Received {len(records)} message(s) from SQS")

    for record in records:
        message_body_str = record.get("body", "{}")
        try:
            message_data = json.loads(message_body_str)
        except Exception as error:
            print(f"Error parsing SQS body: {str(error)}")
            continue

        event_type = message_data.get("eventType", "BOOKING_CONFIRMED")
        patient_email = message_data.get("patientEmail", "")
        doctor_name = message_data.get("doctorName", "Your Doctor")
        slot_time = message_data.get("slotTime", "Scheduled Slot")
        department = message_data.get("department", "Outpatient")
        appointment_id = message_data.get("appointmentId", "N/A")

        if not patient_email:
            print("Skipping message because patientEmail is missing")
            continue

        # Prepare subject and email body based on event type
        if event_type == "BOOKING_CONFIRMED":
            subject = f"MediBook: Appointment Confirmation - {doctor_name}"
            body_text = (
                f"Hello,\n\n"
                f"Your hospital appointment has been successfully confirmed!\n\n"
                f"Appointment Details:\n"
                f"- Doctor: {doctor_name}\n"
                f"- Department: {department}\n"
                f"- Date & Time: {slot_time}\n"
                f"- Appointment ID: {appointment_id}\n\n"
                f"Important Reminder:\n"
                f"Please arrive 15 minutes before your appointment time. "
                f"Bring any relevant medical records and a photo ID.\n\n"
                f"Thank you for choosing MediBook Hospital System."
            )
            body_html = f"""
            <div style="font-family: Arial, sans-serif; color: #1e293b; max-width: 600px; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
                <h2 style="color: #0284c7; margin-top: 0;">🏥 MediBook Appointment Confirmed</h2>
                <p>Hello,</p>
                <p>Your appointment has been successfully scheduled. Here are your booking details:</p>
                <div style="background-color: #f0f9ff; padding: 15px; border-radius: 6px; border-left: 4px solid #0284c7; margin: 15px 0;">
                    <p style="margin: 5px 0;"><strong>Doctor:</strong> {doctor_name}</p>
                    <p style="margin: 5px 0;"><strong>Department:</strong> {department}</p>
                    <p style="margin: 5px 0;"><strong>Date & Time:</strong> {slot_time}</p>
                    <p style="margin: 5px 0;"><strong>Appointment ID:</strong> <code>{appointment_id}</code></p>
                </div>
                <div style="background-color: #fef3c7; padding: 10px 15px; border-radius: 6px; margin: 15px 0;">
                    <p style="margin: 0; font-size: 13px; color: #92400e;">
                        ⏰ <strong>24-Hour Reminder Notice:</strong> Please arrive 15 minutes prior to your scheduled time with your referral documents and ID.
                    </p>
                </div>
                <p style="font-size: 12px; color: #64748b; margin-top: 25px;">
                    MediBook Serverless Healthcare • AWS us-east-1
                </p>
            </div>
            """
        else:
            subject = f"MediBook: Appointment Cancelled - {doctor_name}"
            body_text = (
                f"Hello,\n\n"
                f"Your appointment with {doctor_name} on {slot_time} has been cancelled.\n"
                f"If you did not request this, please visit the MediBook portal to reschedule.\n\n"
                f"MediBook Hospital System"
            )
            body_html = f"""
            <div style="font-family: Arial, sans-serif; color: #1e293b; max-width: 600px; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
                <h2 style="color: #ef4444; margin-top: 0;">❌ MediBook Appointment Cancelled</h2>
                <p>Hello,</p>
                <p>Your appointment with <strong>{doctor_name}</strong> for <strong>{slot_time}</strong> has been cancelled.</p>
                <p>You can log in to your MediBook account at any time to book another available slot.</p>
                <p style="font-size: 12px; color: #64748b; margin-top: 25px;">
                    MediBook Serverless Healthcare • AWS us-east-1
                </p>
            </div>
            """

        # Send email via Amazon SES
        try:
            ses_client.send_email(
                Source=SENDER_EMAIL,
                Destination={
                    "ToAddresses": [patient_email]
                },
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {
                        "Text": {"Data": body_text, "Charset": "UTF-8"},
                        "Html": {"Data": body_html, "Charset": "UTF-8"}
                    }
                }
            )
            print(f"Sent {event_type} email to {patient_email}")
        except Exception as ses_error:
            # If email sending fails (e.g. SES sandbox address not verified), log error
            print(f"Error sending SES email to {patient_email}: {str(ses_error)}")

    return {"status": "success", "processedRecords": len(records)}
