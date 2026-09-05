
// ============================================================
// REFLEX RETAILER
// Delivery submission + logout
// ============================================================

const form = document.getElementById("deliveryForm");
const message = document.getElementById("message");


// ============================================================
// SUBMIT DELIVERY
// ============================================================

form.addEventListener("submit", async function (event) {

    event.preventDefault();

    const deliveryData = {
        customer_name: document
            .getElementById("customer_name")
            .value
            .trim(),

        customer_phone: document
            .getElementById("customer_phone")
            .value
            .trim(),

        delivery_address: document
            .getElementById("delivery_address")
            .value
            .trim(),

        item_description: document
            .getElementById("item_description")
            .value
            .trim()
    };

    message.textContent = "Submitting delivery request...";

    try {

        const response = await fetch("/deliveries", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            credentials: "same-origin",

            body: JSON.stringify(deliveryData)
        });

        const result = await response.json();

        if (response.ok) {

            message.textContent =
                `Delivery request submitted successfully! ` +
                `(Delivery #${result.delivery_id})`;

            form.reset();

        } else {

            message.textContent =
                result.message ||
                result.error ||
                "Failed to submit delivery request.";
        }

    } catch (error) {

        console.error("Delivery error:", error);

        message.textContent =
            "Could not connect to the Reflex server.";
    }
});


// ============================================================
// LOGOUT
// ============================================================

async function logout() {

    const logoutButton =
        document.getElementById("logoutButton");

    if (logoutButton) {

        logoutButton.disabled = true;
        logoutButton.textContent = "Logging out...";
    }

    try {

        const response = await fetch("/logout", {
            method: "POST",
            credentials: "same-origin"
        });

        if (response.ok) {

            // Clear the current page from browser history
            // so the user cannot simply return to the dashboard.
            window.location.replace("/login");

            return;
        }

        console.error("Logout failed.");

        if (logoutButton) {
            logoutButton.disabled = false;
            logoutButton.textContent = "Logout";
        }

    } catch (error) {

        console.error("Logout error:", error);

        if (logoutButton) {
            logoutButton.disabled = false;
            logoutButton.textContent = "Logout";
        }
    }
}


// ============================================================
// PAGE EVENTS
// ============================================================

document.addEventListener("DOMContentLoaded", function () {

    const logoutButton =
        document.getElementById("logoutButton");

    if (logoutButton) {
        logoutButton.addEventListener("click", logout);
    }

});
