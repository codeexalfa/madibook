// MediBook Authentication Helper
// Works seamlessly in both:
// 1. Local Offline Mode (instant testing with demo users)
// 2. Production AWS Mode (calling Amazon Cognito Identity Provider directly via fetch)

// Check if running locally or using placeholder IDs
function isLocalOrDemoMode() {
    return (
        window.location.hostname === "localhost" ||
        window.location.hostname === "127.0.0.1" ||
        !CONFIG.COGNITO_CLIENT_ID ||
        CONFIG.COGNITO_CLIENT_ID.includes("YOUR_")
    );
}

// Helper function to call the Amazon Cognito HTTPS endpoint
async function callCognito(targetAction, payload) {
    const endpoint = `https://cognito-idp.${CONFIG.REGION}.amazonaws.com/`;

    const response = await fetch(endpoint, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": `AWSCognitoIdentityProviderService.${targetAction}`
        },
        body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (!response.ok) {
        const errorMessage = data.message || data.Message || "Cognito error occurred";
        throw new Error(errorMessage);
    }

    return data;
}

// 1. Register a new user
async function authSignUp(email, password, fullName) {
    if (isLocalOrDemoMode()) {
        // Save in localStorage for local testing
        const localUsers = JSON.parse(localStorage.getItem("medibook_local_users") || "{}");
        localUsers[email.toLowerCase()] = {
            email: email,
            name: fullName,
            confirmed: false
        };
        localStorage.setItem("medibook_local_users", JSON.stringify(localUsers));
        return { UserConfirmed: false, CodeDeliveryDetails: { Destination: email } };
    }

    const payload = {
        ClientId: CONFIG.COGNITO_CLIENT_ID,
        Username: email,
        Password: password,
        UserAttributes: [
            { Name: "email", Value: email },
            { Name: "name", Value: fullName }
        ]
    };

    return await callCognito("SignUp", payload);
}

// 2. Confirm registration with 6-digit email code
async function authConfirmSignUp(email, confirmationCode) {
    if (isLocalOrDemoMode()) {
        const localUsers = JSON.parse(localStorage.getItem("medibook_local_users") || "{}");
        if (localUsers[email.toLowerCase()]) {
            localUsers[email.toLowerCase()].confirmed = true;
            localStorage.setItem("medibook_local_users", JSON.stringify(localUsers));
        }
        return true;
    }

    const payload = {
        ClientId: CONFIG.COGNITO_CLIENT_ID,
        Username: email,
        ConfirmationCode: confirmationCode
    };

    return await callCognito("ConfirmSignUp", payload);
}

// 3. Log in with Email and Password
async function authSignIn(email, password) {
    if (isLocalOrDemoMode()) {
        const emailLower = email.toLowerCase();
        let role = "patient";

        if (emailLower.includes("admin")) {
            role = "admin";
        } else if (emailLower.includes("doctor")) {
            role = "doctor";
        }

        const mockUser = {
            sub: "local-user-" + Math.floor(Math.random() * 1000),
            email: email,
            name: email.split("@")[0],
            "cognito:groups": [role]
        };

        const mockToken = "LOCAL_MOCK_TOKEN_" + btoa(JSON.stringify(mockUser));
        sessionStorage.setItem("medibook_id_token", mockToken);
        sessionStorage.setItem("medibook_access_token", mockToken);
        sessionStorage.setItem("medibook_user", JSON.stringify(mockUser));
        return mockUser;
    }

    const payload = {
        AuthFlow: "USER_PASSWORD_AUTH",
        ClientId: CONFIG.COGNITO_CLIENT_ID,
        AuthParameters: {
            USERNAME: email,
            PASSWORD: password
        }
    };

    const result = await callCognito("InitiateAuth", payload);

    if (result.AuthenticationResult) {
        const idToken = result.AuthenticationResult.IdToken;
        const accessToken = result.AuthenticationResult.AccessToken;
        const refreshToken = result.AuthenticationResult.RefreshToken;

        sessionStorage.setItem("medibook_id_token", idToken);
        sessionStorage.setItem("medibook_access_token", accessToken);
        if (refreshToken) {
            sessionStorage.setItem("medibook_refresh_token", refreshToken);
        }

        const user = parseJwt(idToken);
        sessionStorage.setItem("medibook_user", JSON.stringify(user));
        return user;
    } else {
        throw new Error("Login failed. No authentication tokens returned.");
    }
}

// 4. Log out
function authSignOut() {
    sessionStorage.removeItem("medibook_id_token");
    sessionStorage.removeItem("medibook_access_token");
    sessionStorage.removeItem("medibook_refresh_token");
    sessionStorage.removeItem("medibook_user");
    window.location.href = "login.html";
}

// 5. Get saved ID Token for API calls
function getAuthToken() {
    return sessionStorage.getItem("medibook_id_token") || "";
}

// 6. Get current logged in user details
function getCurrentUser() {
    const userJson = sessionStorage.getItem("medibook_user");
    if (!userJson) return null;
    try {
        return JSON.parse(userJson);
    } catch (e) {
        return null;
    }
}

// 7. Get user's role (patient, doctor, or admin)
function getUserRole() {
    const user = getCurrentUser();
    if (!user) return null;

    const groups = user["cognito:groups"] || [];
    if (typeof groups === "string") {
        return groups.toLowerCase();
    }
    if (Array.isArray(groups)) {
        if (groups.includes("admin")) return "admin";
        if (groups.includes("doctor")) return "doctor";
        if (groups.includes("patient")) return "patient";
    }
    return "patient";
}

// 8. Protect pages by role
function requireAuth(allowedRole = null) {
    const token = getAuthToken();
    const user = getCurrentUser();

    if (!token) {
        alert("Please log in to continue.");
        window.location.href = "login.html";
        return;
    }

    if (allowedRole) {
        const role = getUserRole();
        if (role !== allowedRole && role !== "admin") {
            alert(`Access denied. This page is for ${allowedRole}s only.`);
            window.location.href = "index.html";
            return;
        }
    }
}

// Helper: Decode JWT payload
function parseJwt(token) {
    try {
        if (token.startsWith("LOCAL_MOCK_TOKEN_")) {
            return JSON.parse(atob(token.replace("LOCAL_MOCK_TOKEN_", "")));
        }
        const base64Url = token.split(".")[1];
        const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
        const jsonPayload = decodeURIComponent(
            atob(base64)
                .split("")
                .map(c => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
                .join("")
        );
        return JSON.parse(jsonPayload);
    } catch (e) {
        return {};
    }
}
