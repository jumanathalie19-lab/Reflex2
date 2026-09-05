
// ============================================================
// REFLEX RIDER DASHBOARD
// Rider identity comes from the logged-in Flask session.
// ============================================================

let currentRiderId = null;


// ============================================================
// LOAD LOGGED-IN RIDER
// ============================================================

async function loadRider() {
    const nameElement = document.getElementById("riderName");
    const idElement = document.getElementById("riderId");
    const phoneElement = document.getElementById("riderPhone");
    const welcomeElement = document.getElementById("riderWelcome");

    try {
        const response = await fetch("/api/me");

        const data = await response.json();

        // ----------------------------------------------------
        // Check authentication
        // ----------------------------------------------------

        if (!response.ok || !data.authenticated) {
            window.location.href = "/login";
            return;
        }

        const user = data.user;

        // ----------------------------------------------------
        // Make sure the logged-in user is a Rider
        // ----------------------------------------------------

        if (user.role !== "Rider") {
            window.location.href = "/dashboard";
            return;
        }

        // ----------------------------------------------------
        // Store rider identity
        // ----------------------------------------------------

        currentRiderId = user.user_id;

        if (nameElement) {
            nameElement.textContent = user.name;
        }

        if (idElement) {
            idElement.textContent = user.user_id;
        }

        if (phoneElement) {
            phoneElement.textContent = user.phone;
        }

        if (welcomeElement) {
            welcomeElement.textContent = `Welcome, ${user.name}`;
        }

        // ----------------------------------------------------
        // Load deliveries after rider identity is confirmed
        // ----------------------------------------------------

        await loadMyDeliveries();

    } catch (error) {
        console.error("Unable to load rider:", error);

        if (nameElement) {
            nameElement.textContent = "Unable to load";
        }

        if (idElement) {
            idElement.textContent = "Unavailable";
        }

        if (phoneElement) {
            phoneElement.textContent = "Unavailable";
        }

        if (welcomeElement) {
            welcomeElement.textContent =
                "Unable to load rider information.";
        }

        const container = document.getElementById("deliveries");

        if (container) {
            container.innerHTML =
                "<p class='error'>Unable to load rider information.</p>";
        }
    }
}


// ============================================================
// LOAD RIDER'S ACTIVE DELIVERIES
// ============================================================

async function loadMyDeliveries() {
    const container = document.getElementById("deliveries");

    if (!container) {
        console.error("Deliveries container not found.");
        return;
    }

    // --------------------------------------------------------
    // Make sure rider information has been loaded
    // --------------------------------------------------------

    if (!currentRiderId) {
        container.innerHTML =
            "<p class='error'>Rider information is not available.</p>";
        return;
    }

    container.innerHTML = "<p>Loading deliveries...</p>";

    try {
        /*
         * IMPORTANT:
         *
         * rider_id is NOT included in this request.
         *
         * The Flask backend gets the rider ID from:
         *
         * session["user_id"]
         *
         * This prevents a rider from changing the ID in the
         * browser and accessing another rider's deliveries.
         */

        const response = await fetch(
            "/deliveries/mine?status=active"
        );

        const data = await response.json();

        // ----------------------------------------------------
        // Authentication error
        // ----------------------------------------------------

        if (response.status === 401) {
            window.location.href = "/login";
            return;
        }

        // ----------------------------------------------------
        // Permission error
        // ----------------------------------------------------

        if (response.status === 403) {
            window.location.href = "/dashboard";
            return;
        }

        // ----------------------------------------------------
        // Other server errors
        // ----------------------------------------------------

        if (!response.ok) {
            container.innerHTML =
                `<p class="error">${escapeHtml(
                    data.error || "Could not load deliveries."
                )}</p>`;

            return;
        }

        // ----------------------------------------------------
        // Make sure backend returned an array
        // ----------------------------------------------------

        if (!Array.isArray(data)) {
            throw new Error("Invalid deliveries response.");
        }

        // ----------------------------------------------------
        // Display deliveries
        // ----------------------------------------------------

        renderDeliveries(data);

    } catch (error) {
        console.error("Load deliveries error:", error);

        container.innerHTML =
            "<p class='error'>Unable to reach the server.</p>";
    }
}


// ============================================================
// RENDER DELIVERIES
// ============================================================

function renderDeliveries(deliveries) {
    const container = document.getElementById("deliveries");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    // --------------------------------------------------------
    // No active deliveries
    // --------------------------------------------------------

    if (!Array.isArray(deliveries) || deliveries.length === 0) {
        container.innerHTML =
            "<p class='empty-hint'>No active deliveries right now.</p>";

        return;
    }

    // --------------------------------------------------------
    // Create delivery cards
    // --------------------------------------------------------

    deliveries.forEach(delivery => {
        const item = document.createElement("div");

        item.className = "delivery";

        item.innerHTML = `
            <strong>
                Delivery #${escapeHtml(delivery.delivery_id)}
            </strong>

            <p>
                <strong>Customer:</strong>
                ${escapeHtml(delivery.customer_name)}
            </p>

            <p>
                <strong>Phone:</strong>
                ${escapeHtml(delivery.customer_phone)}
            </p>

            <p>
                <strong>Address:</strong>
                ${escapeHtml(delivery.delivery_address)}
            </p>

            <p>
                <strong>Item:</strong>
                ${escapeHtml(delivery.item_description)}
            </p>

            <p>
                <strong>Status:</strong>
                <span class="status-badge">
                    ${escapeHtml(delivery.status)}
                </span>
            </p>

            ${renderActionForStatus(delivery)}

            <p
                id="result-${escapeHtml(delivery.delivery_id)}"
                class="result">
            </p>
        `;

        container.appendChild(item);
    });
}


// ============================================================
// DETERMINE AVAILABLE ACTION
// ============================================================

function renderActionForStatus(delivery) {

    // --------------------------------------------------------
    // ASSIGNED
    //
    // Rider can move the delivery to PICKED_UP.
    // --------------------------------------------------------

    if (delivery.status === "ASSIGNED") {
        return `
            <button
                type="button"
                onclick="markPickedUp(${Number(delivery.delivery_id)})">
                Mark as Picked Up
            </button>
        `;
    }

    // --------------------------------------------------------
    // PICKED_UP
    //
    // Rider can confirm delivery using the demo QR code.
    // --------------------------------------------------------

    if (delivery.status === "PICKED_UP") {
        return `
            <div class="scan-row">

                <input
                    type="text"
                    id="qr-input-${Number(delivery.delivery_id)}"
                    placeholder="Enter QR code"
                    autocomplete="off"
                >

                <button
                    type="button"
                    onclick="scanConfirm(${Number(delivery.delivery_id)})">
                    Confirm Delivery
                </button>

            </div>

           
        `;
    }

    // --------------------------------------------------------
    // DELIVERED or unknown status
    // --------------------------------------------------------

    return "";
}


// ============================================================
// MARK DELIVERY AS PICKED UP
// ============================================================

async function markPickedUp(deliveryId) {
    const resultEl =
        document.getElementById(`result-${deliveryId}`);

    if (!resultEl) {
        return;
    }

    // --------------------------------------------------------
    // Check rider information
    // --------------------------------------------------------

    if (!currentRiderId) {
        resultEl.textContent =
            "Rider information is not available.";

        return;
    }

    resultEl.textContent = "Updating...";

    try {
        /*
         * rider_id is intentionally NOT sent.
         *
         * Flask gets the rider ID from:
         *
         * session["user_id"]
         */

        const response = await fetch(
            `/deliveries/${deliveryId}/status`,
            {
                method: "PATCH",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    status: "PICKED_UP"
                })
            }
        );

        const data = await response.json();

        // ----------------------------------------------------
        // Authentication error
        // ----------------------------------------------------

        if (response.status === 401) {
            window.location.href = "/login";
            return;
        }

        // ----------------------------------------------------
        // Permission error
        // ----------------------------------------------------

        if (response.status === 403) {
            window.location.href = "/dashboard";
            return;
        }

        // ----------------------------------------------------
        // Server rejected request
        // ----------------------------------------------------

        if (!response.ok) {
            resultEl.textContent =
                `Failed: ${
                    data.error ||
                    "Unable to update delivery."
                }`;

            return;
        }

        // ----------------------------------------------------
        // Successful update
        // ----------------------------------------------------

        resultEl.textContent =
            "Delivery marked as picked up.";

        /*
         * Refresh the delivery list.
         *
         * The delivery will remain visible because it is now
         * PICKED_UP, but the QR confirmation action will appear.
         */

        await loadMyDeliveries();

    } catch (error) {
        console.error("Mark picked up error:", error);

        resultEl.textContent =
            "Unable to reach the server.";
    }
}


// ============================================================
// CONFIRM DELIVERY USING QR CODE
// ============================================================

async function scanConfirm(deliveryId) {
    const resultEl =
        document.getElementById(`result-${deliveryId}`);

    const qrInput =
        document.getElementById(`qr-input-${deliveryId}`);

    // --------------------------------------------------------
    // Make sure QR elements exist
    // --------------------------------------------------------

    if (!resultEl || !qrInput) {
        console.error(
            "QR confirmation elements not found for delivery:",
            deliveryId
        );

        return;
    }

    // --------------------------------------------------------
    // Get entered/scanned QR code
    // --------------------------------------------------------

    const qrCode = qrInput.value.trim();

    if (!qrCode) {
        resultEl.textContent =
            "Enter the QR code first.";

        qrInput.focus();

        return;
    }

    resultEl.textContent = "Confirming...";

    // Disable input while request is being processed.
    qrInput.disabled = true;

    const scanButton =
        qrInput.parentElement.querySelector("button");

    if (scanButton) {
        scanButton.disabled = true;
    }

    try {
        /*
         * rider_id is NOT sent from the browser.
         *
         * Flask identifies the logged-in rider using:
         *
         * session["user_id"]
         */

        const response = await fetch(
            `/deliveries/${deliveryId}/qr-confirm`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    qr_code: qrCode
                })
            }
        );

        const data = await response.json();

        // ----------------------------------------------------
        // Authentication error
        // ----------------------------------------------------

        if (response.status === 401) {
            window.location.href = "/login";
            return;
        }

        // ----------------------------------------------------
        // Permission error
        // ----------------------------------------------------

        if (response.status === 403) {
            window.location.href = "/dashboard";
            return;
        }

        // ----------------------------------------------------
        // QR confirmation failed
        // ----------------------------------------------------

        if (!response.ok) {
            /*
             * A failed scan does NOT change the delivery status.
             *
             * The delivery remains PICKED_UP and the rider can
             * try the QR code again.
             */

            resultEl.textContent =
                `Scan failed: ${
                    data.error ||
                    "Invalid QR code"
                }. Please try again.`;

            qrInput.disabled = false;

            if (scanButton) {
                scanButton.disabled = false;
            }

            qrInput.focus();

            return;
        }

        // ----------------------------------------------------
        // Successful QR confirmation
        // ----------------------------------------------------

        resultEl.textContent =
            "Delivery confirmed successfully!";

        /*
         * The backend has now changed the status:
         *
         * PICKED_UP → DELIVERED
         *
         * Therefore the delivery will disappear from the
         * active deliveries list after refreshing.
         */

        await loadMyDeliveries();

    } catch (error) {
        console.error("QR confirmation error:", error);

        resultEl.textContent =
            "Unable to reach the server.";

        qrInput.disabled = false;

        if (scanButton) {
            scanButton.disabled = false;
        }
    }
}


// ============================================================
// LOGOUT
// ============================================================

async function logout() {
    const logoutButton =
        document.getElementById("logoutButton");

    // --------------------------------------------------------
    // Disable button while logging out
    // --------------------------------------------------------

    if (logoutButton) {
        logoutButton.disabled = true;
        logoutButton.textContent = "Logging out...";
    }

    try {
        const response = await fetch(
            "/logout",
            {
                method: "POST"
            }
        );

        // ----------------------------------------------------
        // Logout successful
        // ----------------------------------------------------

        if (response.ok) {
            window.location.href = "/login";
            return;
        }

        console.error("Logout failed.");

    } catch (error) {
        console.error("Logout error:", error);
    }

    // --------------------------------------------------------
    // Restore logout button if logout failed
    // --------------------------------------------------------

    if (logoutButton) {
        logoutButton.disabled = false;
        logoutButton.textContent = "Logout";
    }
}


// ============================================================
// HTML ESCAPING
// ============================================================

function escapeHtml(value) {
    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// ============================================================
// PAGE INITIALIZATION
// ============================================================

document.addEventListener("DOMContentLoaded", () => {

    // --------------------------------------------------------
    // Load logged-in rider
    // --------------------------------------------------------

    loadRider();

    // --------------------------------------------------------
    // Refresh deliveries button
    // --------------------------------------------------------

    const refreshButton =
        document.getElementById(
            "refreshDeliveriesButton"
        );

    if (refreshButton) {
        refreshButton.addEventListener(
            "click",
            loadMyDeliveries
        );
    }

    // --------------------------------------------------------
    // Logout button
    // --------------------------------------------------------

    const logoutButton =
        document.getElementById("logoutButton");

    if (logoutButton) {
        logoutButton.addEventListener(
            "click",
            logout
        );
    }
});

