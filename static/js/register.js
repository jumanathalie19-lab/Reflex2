
// ============================================================
// REFLEX REGISTRATION
// Account creation
// ============================================================

document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("registerForm");
    const message = document.getElementById("message");
    const registerButton = document.getElementById("registerButton");

    // ========================================================
    // REGISTER USER
    // ========================================================

    if (!form) {
        console.error("Registration form not found.");
        return;
    }

    form.addEventListener("submit", async function (event) {

        event.preventDefault();

        const name = document.getElementById("name").value.trim();
        const phone = document.getElementById("phone").value.trim();
        const password = document.getElementById("password").value;
        const confirmPassword =
            document.getElementById("confirm_password").value;
        const role = document.getElementById("role").value;

        // ----------------------------------------------------
        // Validate name
        // ----------------------------------------------------

        if (!name) {
            message.textContent = "Please enter your full name.";
            return;
        }

        // ----------------------------------------------------
        // Validate phone
        // ----------------------------------------------------

        if (!phone) {
            message.textContent = "Please enter your phone number.";
            return;
        }

        // ----------------------------------------------------
        // Validate password
        // ----------------------------------------------------

        if (!password) {
            message.textContent = "Please enter a password.";
            return;
        }

        if (password.length < 6) {
            message.textContent =
                "Password must be at least 6 characters.";
            return;
        }

        // ----------------------------------------------------
        // Confirm password
        // ----------------------------------------------------

        if (password !== confirmPassword) {
            message.textContent = "Passwords do not match.";
            return;
        }

        // ----------------------------------------------------
        // Validate role
        // ----------------------------------------------------

        if (!role) {
            message.textContent = "Please select a role.";
            return;
        }

        // ----------------------------------------------------
        // Disable button
        // ----------------------------------------------------

        registerButton.disabled = true;
        registerButton.textContent = "Creating account...";
        message.textContent = "Creating your account...";

        // ----------------------------------------------------
        // Registration data
        // ----------------------------------------------------

        const registrationData = {
            name: name,
            phone: phone,
            password: password,
            confirm_password: confirmPassword,
            role: role
        };

        try {

            // ------------------------------------------------
            // Send registration request
            // ------------------------------------------------

            const response = await fetch("/register", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                credentials: "same-origin",

                body: JSON.stringify(registrationData)
            });

            // ------------------------------------------------
            // Read server response
            // ------------------------------------------------

            const result = await response.json();

            // ------------------------------------------------
            // Registration successful
            // ------------------------------------------------

            if (response.ok) {

                message.textContent =
                    result.message ||
                    "Account created successfully.";

                form.reset();

                // Redirect to login
                setTimeout(function () {

                    window.location.href =
                        result.redirect || "/login";

                }, 1500);

            }

            // ------------------------------------------------
            // Registration failed
            // ------------------------------------------------

            else {

                message.textContent =
                    result.error ||
                    result.message ||
                    "Registration failed.";
            }

        } catch (error) {

            console.error("Registration error:", error);

            message.textContent =
                "Could not connect to the Reflex server.";

        } finally {

            // ------------------------------------------------
            // Re-enable button
            // ------------------------------------------------

            registerButton.disabled = false;
            registerButton.textContent = "Create Account";
        }

    });

});
