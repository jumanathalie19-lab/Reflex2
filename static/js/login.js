
const form = document.getElementById("loginForm");
const message = document.getElementById("message");
const loginButton = document.getElementById("loginButton");

// ============================================================
// SHOW MESSAGE
// ============================================================

function showMessage(text, type) {
    message.textContent = text;
    message.className = `message ${type}`;
}

// ============================================================
// LOGIN
// ============================================================

form.addEventListener("submit", async function (event) {

    event.preventDefault();

    const phone = document
        .getElementById("phone")
        .value
        .trim();

    const password = document
        .getElementById("password")
        .value;

    // ========================================================
    // VALIDATION
    // ========================================================

    if (!phone) {
        showMessage(
            "Please enter your phone number.",
            "error"
        );
        return;
    }

    if (!password) {
        showMessage(
            "Please enter your password.",
            "error"
        );
        return;
    }

    // ========================================================
    // DISABLE BUTTON
    // ========================================================

    loginButton.disabled = true;
    loginButton.textContent = "Signing in...";

    showMessage("Signing in...", "success");

    try {

        const response = await fetch("/login", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            credentials: "same-origin",

            body: JSON.stringify({
                phone: phone,
                password: password
            })
        });

        // ====================================================
        // HANDLE RESPONSE SAFELY
        // ====================================================

        const contentType =
            response.headers.get("content-type") || "";

        let data = {};

        if (contentType.includes("application/json")) {
            data = await response.json();
        } else {
            // Flask returned HTML instead of JSON
            throw new Error(
                "The server encountered an error. Please try again."
            );
        }

        // ====================================================
        // LOGIN FAILED
        // ====================================================

        if (!response.ok) {

            throw new Error(
                data.error ||
                data.message ||
                "Login failed."
            );
        }

        // ====================================================
        // LOGIN SUCCESSFUL
        // ====================================================

        showMessage(
            `Welcome, ${data.user.name}!`,
            "success"
        );

        // ====================================================
        // REDIRECT ACCORDING TO ROLE
        // ====================================================

        setTimeout(function () {

            window.location.href =
                data.redirect || "/";

        }, 400);

    } catch (error) {

        console.error("Login error:", error);

        showMessage(
            error.message ||
            "Unable to connect to the server.",
            "error"
        );

        loginButton.disabled = false;
        loginButton.textContent = "Sign In";
    }
});

