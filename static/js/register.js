
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
        // Validate passwords
        // ----------------------------------------------------

        if (password !== confirmPassword) {

            message.textContent = "Passwords do not match.";
            return;
        }

        if (password.length < 6) {

            message.textContent =
                "Password must be at least 6 characters.";

            return;
        }

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

            const result = await response.json();

            // ------------------------------------------------
            // Success
            // ------------------------------------------------

            if (response.ok) {

                message.textContent =
                    result.message ||
                    "Account created successfully.";

                form.reset();

                setTimeout(function () {

                    window.location.href = "/login";

                }, 1500);

            } else {

                message.textContent =
                    result.message ||
                    result.error ||
                    "Registration failed.";
            }

        } catch (error) {

            console.error("Registration error:", error);

            message.textContent =
                "Could not connect to the Reflex server.";

        } finally {

            registerButton.disabled = false;
            registerButton.textContent = "Create Account";
        }

    });

});
