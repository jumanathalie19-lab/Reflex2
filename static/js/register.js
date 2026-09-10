
// ============================================================
// REFLEX REGISTRATION
// Account creation
// ============================================================

document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("registerForm");
    const message = document.getElementById("message");
    const registerButton = document.getElementById("registerButton");

    if (!form) {
        console.error("Registration form not found.");
        return;
    }

    function showError(text) {
        message.textContent = text;
        message.className = "message error";
    }

    function showSuccess(text) {
        message.textContent = text;
        message.className = "message success";
    }

    form.addEventListener("submit", async function (event) {

        event.preventDefault();

        const name = document
            .getElementById("name")
            .value
            .trim();

        const phone = document
            .getElementById("phone")
            .value
            .trim();

        const password = document
            .getElementById("password")
            .value;

        const confirmPassword = document
            .getElementById("confirm_password")
            .value;

        const role = document
            .getElementById("role")
            .value;

        // ====================================================
        // VALIDATION
        // ====================================================

        if (!name) {
            showError("Please enter your full name.");
            return;
        }

        if (!phone) {
            showError("Please enter your phone number.");
            return;
        }

        if (!password) {
            showError("Please enter a password.");
            return;
        }

        if (password.length < 6) {
            showError(
                "Password must be at least 6 characters."
            );
            return;
        }

        if (password !== confirmPassword) {
            showError("Passwords do not match.");
            return;
        }

        if (!role) {
            showError("Please select a role.");
            return;
        }

        // ====================================================
        // DISABLE BUTTON
        // ====================================================

        registerButton.disabled = true;
        registerButton.textContent = "Creating account...";

        showSuccess("Creating your account...");

        // ====================================================
        // REGISTRATION DATA
        // ====================================================

        const registrationData = {
            name: name,
            phone: phone,
            password: password,
            confirm_password: confirmPassword,
            role: role
        };

        try {

            const response = await fetch("/register", {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                credentials: "same-origin",

                body: JSON.stringify(registrationData)
            });

            const contentType =
                response.headers.get("content-type") || "";

            let result = {};

            if (contentType.includes("application/json")) {
                result = await response.json();
            } else {
                throw new Error(
                    "The server returned an unexpected response."
                );
            }

            // =================================================
            // REGISTRATION FAILED
            // =================================================

            if (!response.ok) {

                showError(
                    result.error ||
                    result.message ||
                    "Registration failed."
                );

                return;
            }

            // =================================================
            // REGISTRATION SUCCESSFUL
            // =================================================

            showSuccess(
                result.message ||
                "Account created successfully."
            );

            // Go to login immediately
            window.location.href =
                result.redirect || "/login";

        } catch (error) {

            console.error(
                "Registration error:",
                error
            );

            showError(
                error.message ||
                "Could not connect to the Reflex server."
            );

        } finally {

            registerButton.disabled = false;
            registerButton.textContent = "Create Account";
        }
    });
});

