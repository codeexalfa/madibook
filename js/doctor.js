// MediBook Doctor Portal Logic

document.addEventListener("DOMContentLoaded", () => {
    // Role check: Doctor or Admin
    requireAuth("doctor");
    setupUserNav();

    // Default to today's date
    const todayStr = new Date().toISOString().split("T")[0];
    const dateInput = document.getElementById("schedule-date");
    if (dateInput) {
        dateInput.value = todayStr;
    }

    loadDoctorTodayAppointments();
});

function setupUserNav() {
    const user = getCurrentUser();
    const container = document.getElementById("nav-user-container");
    if (container && user) {
        container.innerHTML = `
            <span class="user-badge" style="background:#d1fae5; color:#065f46;">DOCTOR</span>
            <span style="font-size: 0.9rem; color: #475569; margin: 0 0.5rem;">${user.email || user.name || "Doctor"}</span>
            <button onclick="authSignOut()" class="btn btn-secondary btn-sm">Log Out</button>
        `;
    }
}

function showDoctorAlert(message, type = "success") {
    const box = document.getElementById("doctor-alert");
    box.className = `alert alert-${type}`;
    box.textContent = message;
    box.style.display = "block";
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function hideDoctorAlert() {
    const box = document.getElementById("doctor-alert");
    if (box) box.style.display = "none";
}

// 1. Load Today's Appointments
async function loadDoctorTodayAppointments() {
    const date = document.getElementById("schedule-date").value || new Date().toISOString().split("T")[0];
    const tbody = document.getElementById("today-appointments-tbody");
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #94a3b8; padding: 1.5rem;">Loading appointments for ${date}...</td></tr>`;

    try {
        let appointments = [];
        if (!CONFIG.API_URL || CONFIG.API_URL.includes("YOUR_")) {
            // Local preview sample data
            appointments = [
                {
                    slotTime: `${date} 09:00`,
                    patientEmail: "john.doe@example.com",
                    department: "Cardiology",
                    status: "CONFIRMED",
                    notes: "Chest tightness checkup"
                },
                {
                    slotTime: `${date} 11:00`,
                    patientEmail: "emma.watson@example.com",
                    department: "Cardiology",
                    status: "CONFIRMED",
                    notes: "Routine ECG test"
                },
                {
                    slotTime: `${date} 14:00`,
                    patientEmail: "alex.brown@example.com",
                    department: "Cardiology",
                    status: "CONFIRMED",
                    notes: "Prescription renewal"
                }
            ];
        } else {
            const data = await apiGetDoctorToday("", date);
            appointments = data.appointments || [];
        }

        if (appointments.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #64748b; padding: 2rem;">No appointments scheduled for ${date}.</td></tr>`;
            return;
        }

        let rowsHtml = "";
        appointments.forEach(app => {
            const timePart = app.slotTime.split(" ")[1] || app.slotTime;
            const statusClass = app.status === "CONFIRMED" ? "badge-confirmed" : (app.status === "CANCELLED" ? "badge-cancelled" : "badge-noshow");
            rowsHtml += `
                <tr>
                    <td><strong>${timePart}</strong></td>
                    <td>${app.patientEmail || app.patientId || "Patient"}</td>
                    <td>${app.department || "General"}</td>
                    <td><span class="badge ${statusClass}">${app.status || "CONFIRMED"}</span></td>
                    <td style="color: #64748b; font-size: 0.85rem;">${app.notes || "-"}</td>
                </tr>
            `;
        });
        tbody.innerHTML = rowsHtml;

    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #ef4444; padding: 1.5rem;">Failed to load schedule: ${err.message}</td></tr>`;
    }
}

// 2. Save Doctor Availability
async function saveAvailability(event) {
    event.preventDefault();
    const btn = document.getElementById("btn-save-schedule");
    const name = document.getElementById("doc-name-input").value.trim();
    const dept = document.getElementById("doc-dept-input").value;

    const checkboxes = document.querySelectorAll("input[name='time-slot']:checked");
    const scheduleList = Array.from(checkboxes).map(cb => cb.value);

    if (scheduleList.length === 0) {
        alert("Please select at least one available time slot.");
        return;
    }

    try {
        btn.disabled = true;
        btn.textContent = "Saving...";
        hideDoctorAlert();

        if (!CONFIG.API_URL || CONFIG.API_URL.includes("YOUR_")) {
            await new Promise(r => setTimeout(r, 600));
            showDoctorAlert(`Weekly availability saved with ${scheduleList.length} slots! (Demo Mode)`, "success");
        } else {
            await apiSaveAvailability(scheduleList, name, dept);
            showDoctorAlert("Weekly availability updated successfully in DynamoDB!", "success");
        }
    } catch (err) {
        showDoctorAlert(`Error saving schedule: ${err.message}`, "danger");
    } finally {
        btn.disabled = false;
        btn.textContent = "Save Weekly Availability";
    }
}
