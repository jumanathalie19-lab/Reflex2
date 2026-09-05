const form = document.getElementById("registerForm");

const message = document.getElementById("message");

const registerButton =
    document.getElementById("registerButton");


// ============================================================
// SHOW MESSAGE
// ============================================================

function showMessage(text, type) {

    message.textContent = text;

    message.className =
        `message ${type}`;

}


// ============================================================
// REGISTRATION
// ============================================================

form.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();


        const name =
            document
                .getElementById("name")
                .value
                .trim();


        const phone =
            document
                .getElementById("phone")
                .value
                .trim();


        const password =
            document
                .getElementById("password")
                .value;


        const confirmPassword =
            document
                .getElementById("confirm_password")
                .value;


        const role =
            document
                .getElementById("role")
                .value;


        // ====================================================
        // CLIENT-SIDE VALIDATION
        // ====================================================

        if (!name) {

            showMessage(
                "Please enter your name.",
                "error"
            );

            return;
        }


        if (!phone) {

            showMessage(
                "Please enter your phone number.",
                "error"
            );

            return;
        }


        if (!password) {

            showMessage(
                "Please enter a password.",
                "error"
            );

            return;
        }


        if (password.length < 6) {

            showMessage(
                "Password must be at least 6 characters.",
                "error"
            );

            return;
        }


        if (password !== confirmPassword) {

            showMessage(
                "Passwords do not match.",
                "error"
            );

            return;
        }


        if (!role) {

            showMessage(
                "Please select your role.",
                "error"
            );

            return;
        }


        // ====================================================
        // SUBMIT
        // ====================================================

        registerButton.disabled = true;

        registerButton.textContent =
            "Creating Account...";


        showMessage(
            "Creating your account...",
            "success"
        );


        try {

            const response = await fetch(
                "/register",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    credentials: "same-origin",

                    body: JSON.stringify({
                        name: name,
                        phone: phone,
                        password: password,
                        confirm_password:
                            confirmPassword,
                        role: role
                    })
                }
            );


            const data =
                await response.json();


            // Registration failed
            if (!response.ok) {

                throw new Error(
                    data.error ||
                    "Registration failed."
                );

            }


            // Successful registration
            showMessage(
                "Account created successfully! Redirecting to login...",
                "success"
            );


            form.reset();


            setTimeout(
                function () {

                    window.location.href =
                        data.redirect || "/login";

                },
                1000
            );


        } catch (error) {

            console.error(
                "Registration error:",
                error
            );


            showMessage(
                error.message ||
                "Unable to create your account.",
                "error"
            );


            registerButton.disabled = false;

            registerButton.textContent =
                "Create Account";

        }

    }
);