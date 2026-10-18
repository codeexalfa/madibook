// MediBook Patient Portal Logic

let doctorsCache = [];
let selectedDoctor = null;
let selectedSlot = null;
let selectedReferralFile = null;

// Mock doctors for local preview before AWS is configured
const MOCK_DOCTORS = [
    { doctorId: "doc-101", name: "Dr. Sarah Jenkins", department: "Cardiology", room: "Room 201", bio: "Senior cardiologist specializing in heart health." },
    { doctorId: "doc-102", name: "Dr. Michael Chen", department: "Neurology", room: "Room 305", bio: "Consultant neurologist with 12 years clinical experience." },
    { doctorId: "doc-103", name: "Dr. Emily Taylor", department: "Pediatrics", room: "Room 104", bio: "Gentle and friendly pediatric specialist." },
    { doctorId: "doc-104", name: "Dr. Marcus Johnson", department: "Orthopedics", room: "Room 402", bio: "Joint restoration and sports injuries specialist." },
    { doctorId: "doc-105", name: "Dr. Olivia Patel", department: "Dermatology", room: "Room 210", bio: "Expert dermatologist for all skin health." }
];

document.addEventListener("DOMContentLoaded", () => {
    // Role protection
    requireAuth("patient");
    setupUserNav();

    // Set default date to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dateInput = document.getElementById("appointment-date");
    if (dateInput) {
        dateInput.value = tomorrow.toISOString().split("T")[0];
        dateInput.min = new Date().toISOString().split("T")[0];
    }

    // Load doctors and appointments
    loadDoctors();
    loadMyAppointments();
});

function setupUserNav() {
    const user = getCurrentUser();
    const container = document.getElementById("nav-user-container");
    if (container && user) {
        container.innerHTML = `
            <span class="user-badge">PATIENT</span>
            <span style="font-size: 0.9rem; color: #475569; margin: 0 0.5rem;">${user.email || user.name || "Patient"}</span>
            <button onclick="authSignOut()" class="btn btn-secondary btn-sm">Log Out</button>
        `;
    }
}

function showPatientAlert(message, type = "success") {
    const box = document.getElementById("patient-alert");
    box.className = `alert alert-${type}`;
    box.textContent = message;
    box.style.display = "block";
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function hidePatientAlert() {
    const box = document.getElementById("patient-alert");
    if (box) box.style.display = "none";
}

// 1. Fetch & Populate Doctors
async function loadDoctors(department = "") {
    const select = document.getElementById("doctor-select");
    select.innerHTML = `<option value="">Loading doctors...</option>`;

    try {
        let doctors = [];
        if (!CONFIG.API_URL || CONFIG.API_URL.includes("YOUR_")) {
            // Local preview fallback
            doctors = department ? MOCK_DOCTORS.filter(d => d.department === department) : MOCK_DOCTORS;
        } else {
            const data = await apiGetDoctors(department);
            doctors = data.doctors || [];
        }

        doctorsCache = doctors;

        if (doctors.length === 0) {
            select.innerHTML = `<option value="">No doctors found in this department</option>`;
            return;
        }

        let optionsHtml = `<option value="">-- Choose a Doctor --</option>`;
        doctors.forEach(doc => {
            optionsHtml += `<option value="${doc.doctorId}">${doc.name} (${doc.department})</option>`;
        });
        select.innerHTML = optionsHtml;

    } catch (err) {
        console.error("Failed to load doctors:", err);
        select.innerHTML = `<option value="">Failed to load doctors from API</option>`;
    }
}

function onDepartmentChange() {
    const dept = document.getElementById("dept-select").value;
    loadDoctors(dept);
    document.getElementById("doctor-info-box").style.display = "none";
    document.getElementById("slots-container").innerHTML = `<span style="color: #94a3b8; font-size: 0.9rem;">Select a doctor and date to view free slots.</span>`;
    document.getElementById("btn-book-slot").disabled = true;
    selectedDoctor = null;
    selectedSlot = null;
}

function onDoctorChange() {
    const docId = document.getElementById("doctor-select").value;
    selectedDoctor = doctorsCache.find(d => d.doctorId === docId) || null;

    const infoBox = document.getElementById("doctor-info-box");
    if (selectedDoctor) {
        document.getElementById("doc-info-name").textContent = selectedDoctor.name;
        document.getElementById("doc-info-room").textContent = `📍 ${selectedDoctor.room || selectedDoctor.department}`;
        document.getElementById("doc-info-bio").textContent = selectedDoctor.bio || `Specialist in ${selectedDoctor.department}`;
        infoBox.style.display = "block";
        loadDoctorSlots();
    } else {
        infoBox.style.display = "none";
        document.getElementById("slots-container").innerHTML = `<span style="color: #94a3b8; font-size: 0.9rem;">Select a doctor and date to view free slots.</span>`;
        document.getElementById("btn-book-slot").disabled = true;
    }
}

// 2. Load Free Slots
async function loadDoctorSlots() {
    if (!selectedDoctor) return;

    const date = document.getElementById("appointment-date").value;
    const container = document.getElementById("slots-container");
    const loading = document.getElementById("slots-loading");
    const bookBtn = document.getElementById("btn-book-slot");

    selectedSlot = null;
    bookBtn.disabled = true;
    loading.style.display = "block";
    container.innerHTML = "";

    try {
        let freeSlots = [];
        if (!CONFIG.API_URL || CONFIG.API_URL.includes("YOUR_")) {
            // Demo fallback slots
            freeSlots = [
                `${date} 09:00`,
                `${date} 10:00`,
                `${date} 11:00`,
                `${date} 14:00`,
                `${date} 15:00`
            ];
        } else {
            const data = await apiGetSlots(selectedDoctor.doctorId, date);
            freeSlots = data.freeSlots || [];
        }

        loading.style.display = "none";

        if (freeSlots.length === 0) {
            container.innerHTML = `<span style="color: #ef4444; font-size: 0.9rem;">No free slots available for this doctor on this date.</span>`;
            return;
        }

        freeSlots.forEach(slot => {
            const chip = document.createElement("button");
            chip.type = "button";
            chip.className = "slot-chip";
            chip.textContent = slot.split(" ")[1] || slot;
            chip.onclick = () => selectSlotChip(chip, slot);
            container.appendChild(chip);
        });

    } catch (err) {
        loading.style.display = "none";
        container.innerHTML = `<span style="color: #ef4444;">Error fetching slots: ${err.message}</span>`;
    }
}

function selectSlotChip(buttonElement, slotString) {
    document.querySelectorAll(".slot-chip").forEach(el => el.classList.remove("selected"));
    buttonElement.classList.add("selected");
    selectedSlot = slotString;
    document.getElementById("btn-book-slot").disabled = false;
}

// 3. Book Appointment
async function bookSelectedSlot() {
    if (!selectedDoctor || !selectedSlot) {
        alert("Please pick a doctor and a slot.");
        return;
    }

    const notes = document.getElementById("booking-notes").value.trim();
    const btn = document.getElementById("btn-book-slot");

    const payload = {
        doctorId: selectedDoctor.doctorId,
        doctorName: selectedDoctor.name,
        department: selectedDoctor.department,
        slotTime: selectedSlot,
        notes: notes
    };

    try {
        btn.disabled = true;
        btn.textContent = "Booking...";
        hidePatientAlert();

        if (!CONFIG.API_URL || CONFIG.API_URL.includes("YOUR_")) {
            // Local preview simulation
            await new Promise(r => setTimeout(r, 600));
            showPatientAlert(`Booked! Your appointment with ${selectedDoctor.name} at ${selectedSlot} is confirmed. (Demo Mode)`, "success");
        } else {
            const response = await apiBookAppointment(payload);
            showPatientAlert("Booked! Your appointment confirmation has been emailed to you.", "success");
        }

        // Refresh slots and appointments list
        loadDoctorSlots();
        loadMyAppointments();
    } catch (err) {
        // Show double-booking or other friendly error
        showPatientAlert(err.message, "danger");
    } finally {
        btn.disabled = false;
        btn.textContent = "Confirm Booking";
    }
}

// 4. Referral Document Upload
function onFileSelected(event) {
    const file = event.target.files[0];
    const label = document.getElementById("selected-file-label");
    const uploadBtn = document.getElementById("btn-upload-referral");

    if (file) {
        selectedReferralFile = file;
        label.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        label.style.color = "#0284c7";
        uploadBtn.disabled = false;
    } else {
        selectedReferralFile = null;
        label.textContent = "Maximum size 10MB";
        label.style.color = "#64748b";
        uploadBtn.disabled = true;
    }
}

async function uploadReferralDocument() {
    if (!selectedReferralFile) return;

    const btn = document.getElementById("btn-upload-referral");
    const statusText = document.getElementById("upload-status-text");

    try {
        btn.disabled = true;
        statusText.textContent = "Requesting S3 Presigned URL...";
        statusText.style.color = "#0284c7";

        if (!CONFIG.API_URL || CONFIG.API_URL.includes("YOUR_")) {
            await new Promise(r => setTimeout(r, 800));
            statusText.textContent = "Demo: Document uploaded successfully to S3 bucket!";
            statusText.style.color = "#10b981";
            showPatientAlert("Referral document uploaded successfully!", "success");
            return;
        }

        // 1. Get Presigned S3 URL from Lambda
        const res = await apiGetReferralUploadUrl(selectedReferralFile.name, selectedReferralFile.type);
        const uploadUrl = res.uploadUrl;

        // 2. Direct upload to Amazon S3
        statusText.textContent = "Uploading file to Amazon S3...";
        await apiUploadToS3(uploadUrl, selectedReferralFile);

        statusText.textContent = "Upload complete!";
        statusText.style.color = "#10b981";
        showPatientAlert("Referral document uploaded to AWS S3 successfully!", "success");

    } catch (err) {
        console.error(err);
        statusText.textContent = `Upload failed: ${err.message}`;
        statusText.style.color = "#ef4444";
    } finally {
        btn.disabled = false;
    }
}

// 5. My Appointments List & Cancel
async function loadMyAppointments() {
    const tableBody = document.getElementById("my-appointments-table-body");
    tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #94a3b8; padding: 1.5rem;">Loading your appointments...</td></tr>`;

    try {
        let appointments = [];
        if (!CONFIG.API_URL || CONFIG.API_URL.includes("YOUR_")) {
            appointments = [
                {
                    appointmentId: "demo-app-1",
                    doctorId: "doc-101",
                    doctorName: "Dr. Sarah Jenkins",
                    department: "Cardiology",
                    slotTime: "2026-10-22 10:00",
                    status: "CONFIRMED",
                    notes: "Checkup"
                }
            ];
        } else {
            const data = await apiGetMyAppointments();
            appointments = data.appointments || [];
        }

        if (appointments.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #64748b; padding: 2rem;">You do not have any scheduled appointments.</td></tr>`;
            return;
        }

        let rowsHtml = "";
        appointments.forEach(app => {
            const statusClass = app.status === "CONFIRMED" ? "badge-confirmed" : (app.status === "CANCELLED" ? "badge-cancelled" : "badge-noshow");
            const canCancel = app.status === "CONFIRMED";

            rowsHtml += `
                <tr>
                    <td><strong>${app.doctorName || "Doctor"}</strong></td>
                    <td>${app.department || "General"}</td>
                    <td>${app.slotTime}</td>
                    <td><span class="badge ${statusClass}">${app.status || "CONFIRMED"}</span></td>
                    <td style="color: #64748b; font-size: 0.85rem;">${app.notes || "-"}</td>
                    <td>
                        ${canCancel ? `<button class="btn btn-danger btn-sm" onclick="cancelAppointment('${app.appointmentId || ""}', '${app.doctorId}', '${app.slotTime}')">Cancel</button>` : `<span style="color: #94a3b8; font-size: 0.85rem;">Cancelled</span>`}
                    </td>
                </tr>
            `;
        });
        tableBody.innerHTML = rowsHtml;

    } catch (err) {
        tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #ef4444; padding: 1.5rem;">Failed to load appointments: ${err.message}</td></tr>`;
    }
}

async function cancelAppointment(appointmentId, doctorId, slotTime) {
    if (!confirm(`Are you sure you want to cancel your appointment on ${slotTime}?`)) {
        return;
    }

    try {
        hidePatientAlert();
        if (!CONFIG.API_URL || CONFIG.API_URL.includes("YOUR_")) {
            showPatientAlert("Appointment cancelled. (Demo Mode)", "info");
        } else {
            await apiCancelAppointment(appointmentId, doctorId, slotTime);
            showPatientAlert("Appointment cancelled successfully. A notification has been triggered.", "info");
        }
        loadMyAppointments();
        loadDoctorSlots();
    } catch (err) {
        showPatientAlert(`Could not cancel appointment: ${err.message}`, "danger");
    }
}
