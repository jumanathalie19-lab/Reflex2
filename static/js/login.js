
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

form.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();


        const phone =
            document
                .getElementById("phone")
                .value
                .trim();


        const password =
            document
                .getElementById("password")
                .value;


        // Validate
        if (!phone || !password) {

            showMessage(
                "Enter your phone number and password.",
                "error"
            );

            return;
        }


        // Disable button
        loginButton.disabled = true;

        loginButton.textContent =
            "Signing in...";


        showMessage(
            "Signing in...",
            "success"
        );


        try {

            const response = await fetch(
                "/login",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    credentials: "same-origin",

                    body: JSON.stringify({
                        phone: phone,
                        password: password
                    })
                }
            );


            const data =
                await response.json();


            // Login failed
            if (!response.ok) {

                throw new Error(
                    data.error ||
                    "Login failed."
                );

            }


            // Successful login
            showMessage(
                `Welcome, ${data.user.name}!`,
                "success"
            );


            // Redirect according to role
            setTimeout(
                function () {

                    window.location.href =
                        data.redirect;

                },
                400
            );


        } catch (error) {

            console.error(
                "Login error:",
                error
            );


            showMessage(
                error.message ||
                "Unable to connect to the server.",
                "error"
            );


            loginButton.disabled = false;

            loginButton.textContent =
                "Sign In";

        }

    }
);
