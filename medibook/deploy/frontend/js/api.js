// MediBook API Client
// Connects frontend pages to AWS API Gateway REST API endpoints.

async function requestApi(path, method = "GET", bodyData = null) {
    const baseUrl = CONFIG.API_URL.replace(/\/+$/, "");
    const url = `${baseUrl}${path}`;
    const token = getAuthToken();

    const headers = {
        "Content-Type": "application/json"
    };

    // Attach Cognito token in Authorization header
    if (token) {
        headers["Authorization"] = token;
    }

    const options = {
        method: method,
        headers: headers
    };

    if (bodyData && (method === "POST" || method === "PUT" || method === "PATCH" || method === "DELETE")) {
        options.body = JSON.stringify(bodyData);
    }

    try {
        const response = await fetch(url, options);
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            // Friendly error handling
            if (response.status === 409) {
                throw new Error("This slot is already taken");
            } else if (response.status === 401) {
                throw new Error("Please log in to continue");
            } else if (response.status === 403) {
                throw new Error("Access denied: You do not have permission for this action");
            } else {
                throw new Error(data.message || `API Error (${response.status})`);
            }
        }

        return data;
    } catch (err) {
        console.error("API Call failed:", err);
        throw err;
    }
}

// 1. List doctors (optional ?dept=)
async function apiGetDoctors(department = "") {
    let path = "/doctors";
    if (department) {
        path += `?dept=${encodeURIComponent(department)}`;
    }
    return await requestApi(path, "GET");
}

// 2. Get free slots for a doctor on a specific date
async function apiGetSlots(doctorId, dateString = "") {
    let path = `/doctors/${encodeURIComponent(doctorId)}/slots`;
    if (dateString) {
        path += `?date=${encodeURIComponent(dateString)}`;
    }
    return await requestApi(path, "GET");
}

// 3. Book an appointment (patient)
async function apiBookAppointment(payload) {
    return await requestApi("/appointments", "POST", payload);
}

// 4. Get logged-in patient's appointments
async function apiGetMyAppointments() {
    return await requestApi("/appointments/mine", "GET");
}

// 5. Cancel an appointment
async function apiCancelAppointment(appointmentId, doctorId, slotTime) {
    const payload = {
        doctorId: doctorId,
        slotTime: slotTime
    };
    return await requestApi(`/appointments/${encodeURIComponent(appointmentId)}`, "DELETE", payload);
}

// 6. Doctor saves weekly availability
async function apiSaveAvailability(scheduleList, doctorName = "", department = "") {
    const payload = {
        schedule: scheduleList,
        name: doctorName,
        department: department
    };
    return await requestApi("/doctors/availability", "POST", payload);
}

// 7. Doctor sees today's appointment list
async function apiGetDoctorToday(doctorId = "", dateString = "") {
    let path = "/doctors/today";
    const params = [];
    if (doctorId) params.push(`doctorId=${encodeURIComponent(doctorId)}`);
    if (dateString) params.push(`date=${encodeURIComponent(dateString)}`);
    if (params.length > 0) {
        path += `?${params.join("&")}`;
    }
    return await requestApi(path, "GET");
}

// 8. Admin gets dashboard statistics
async function apiGetAdminStats() {
    return await requestApi("/admin/stats", "GET");
}

// 9. Get S3 presigned upload URL for referral document
async function apiGetReferralUploadUrl(fileName, contentType) {
    const payload = {
        fileName: fileName,
        contentType: contentType
    };
    return await requestApi("/referrals/upload-url", "POST", payload);
}

// 10. Direct S3 upload using presigned PUT URL
async function apiUploadToS3(uploadUrl, file) {
    const response = await fetch(uploadUrl, {
        method: "PUT",
        headers: {
            "Content-Type": file.type || "application/octet-stream"
        },
        body: file
    });

    if (!response.ok) {
        throw new Error(`S3 upload failed with status ${response.status}`);
    }
    return true;
}
