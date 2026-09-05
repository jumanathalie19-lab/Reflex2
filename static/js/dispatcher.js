
// ============================================================
// REFLEX DISPATCHER DASHBOARD
// ============================================================
//
// Authentication:
//     GET  /api/me
//
// Deliveries:
//     GET  /deliveries
//
// Riders:
//     GET  /riders
//
// Assignment:
//     POST /deliveries/<delivery_id>/assign
//
// ============================================================


// ============================================================
// MODAL
// ============================================================

let modalCloseCallback = null;


function showModal(title, message, type = "success", onClose = null) {
    const modal = document.getElementById("messageModal");
    const modalTitle = document.getElementById("modalTitle");
    const modalMessage = document.getElementById("modalMessage");
    const modalIcon = document.getElementById("modalIcon");

    if (!modal || !modalTitle || !modalMessage || !modalIcon) {
        alert(message);

        if (typeof onClose === "function") {
            onClose();
        }

        return;
    }

    modalTitle.textContent = title;
    modalMessage.textContent = message;

    if (type === "success") {
        modalIcon.textContent = "✓";
        modalIcon.className = "modal-icon success";
    } else {
        modalIcon.textContent = "!";
        modalIcon.className = "modal-icon error";
    }

    modalCloseCallback =
        typeof onClose === "function"
            ? onClose
            : null;

    modal.classList.add("show");
    modal.setAttribute("aria-hidden", "false");
}


async function closeModal() {
    const modal =
        document.getElementById("messageModal");

    if (!modal) {
        return;
    }

    modal.classList.remove("show");
    modal.setAttribute("aria-hidden", "true");

    const callback = modalCloseCallback;

    modalCloseCallback = null;

    if (typeof callback === "function") {
        try {
            await callback();
        } catch (error) {
            console.error(
                "Modal close callback error:",
                error
            );
        }
    }
}


// ============================================================
// LOAD CURRENT DISPATCHER
// ============================================================

async function loadDispatcher() {
    const nameElement =
        document.getElementById("dispatcherName");

    const idElement =
        document.getElementById("dispatcherId");

    const welcomeElement =
        document.getElementById("dispatcherWelcome");

    try {
        const response =
            await fetch("/api/me");

        const data =
            await response.json();

        if (!response.ok || !data.authenticated) {
            window.location.href = "/login";
            return;
        }

        const user = data.user;

        // ----------------------------------------------------
        // Verify Dispatcher role
        // ----------------------------------------------------

        if (user.role !== "Dispatcher") {
            window.location.href = "/dashboard";
            return;
        }

        // ----------------------------------------------------
        // Display dispatcher information
        // ----------------------------------------------------

        if (nameElement) {
            nameElement.textContent =
                user.name;
        }

        if (idElement) {
            idElement.textContent =
                user.user_id;
        }

        if (welcomeElement) {
            welcomeElement.textContent =
                `Welcome, ${user.name}`;
        }

    } catch (error) {
        console.error(
            "Unable to load dispatcher:",
            error
        );

        if (nameElement) {
            nameElement.textContent =
                "Unable to load";
        }

        if (idElement) {
            idElement.textContent =
                "Unavailable";
        }

        if (welcomeElement) {
            welcomeElement.textContent =
                "Unable to load dispatcher information.";
        }
    }
}


// ============================================================
// LOAD OPEN DELIVERIES
// ============================================================

async function loadOpenDeliveries() {
    const container =
        document.getElementById("deliveries");

    if (!container) {
        return;
    }

    container.innerHTML =
        "<p>Loading...</p>";

    try {
        const [
            deliveriesRes,
            ridersRes
        ] = await Promise.all([
            fetch("/deliveries"),
            fetch("/riders")
        ]);

        // ----------------------------------------------------
        // Authentication failure
        // ----------------------------------------------------

        if (
            deliveriesRes.status === 401 ||
            deliveriesRes.status === 403
        ) {
            window.location.href = "/dashboard";
            return;
        }

        if (
            ridersRes.status === 401 ||
            ridersRes.status === 403
        ) {
            window.location.href = "/dashboard";
            return;
        }

        const deliveries =
            await deliveriesRes.json();

        const riders =
            await ridersRes.json();

        // ----------------------------------------------------
        // API errors
        // ----------------------------------------------------

        if (!deliveriesRes.ok) {
            throw new Error(
                deliveries.error ||
                "Unable to load deliveries"
            );
        }

        if (!ridersRes.ok) {
            throw new Error(
                riders.error ||
                "Unable to load riders"
            );
        }

        renderDeliveries(
            deliveries,
            riders
        );

    } catch (error) {
        console.error(
            "Load deliveries error:",
            error
        );

        container.innerHTML =
            "<p class='error'>Unable to load deliveries.</p>";
    }
}


// ============================================================
// RENDER DELIVERIES
// ============================================================

function renderDeliveries(
    deliveries,
    riders
) {
    const container =
        document.getElementById("deliveries");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    // --------------------------------------------------------
    // No open deliveries
    // --------------------------------------------------------

    if (
        !Array.isArray(deliveries) ||
        deliveries.length === 0
    ) {
        container.innerHTML =
            "<p class='empty-hint'>" +
            "No open deliveries right now." +
            "</p>";

        return;
    }

    // --------------------------------------------------------
    // Create rider options
    // --------------------------------------------------------

    const riderOptions =
        Array.isArray(riders)
            ? riders
                .map(rider => `
                    <option value="${escapeHtml(rider.user_id)}">
                        ${escapeHtml(rider.name)}
                    </option>
                `)
                .join("")
            : "";

    // --------------------------------------------------------
    // Render every delivery
    // --------------------------------------------------------

    deliveries.forEach(delivery => {
        const deliveryId =
            Number(delivery.delivery_id);

        const item =
            document.createElement("div");

        item.className =
            "delivery";

        item.innerHTML = `
            <strong>
                Delivery #${escapeHtml(delivery.delivery_id)}
            </strong>

            <p>
                Customer:
                ${escapeHtml(delivery.customer_name)}
            </p>

            <p>
                Phone:
                ${escapeHtml(delivery.customer_phone)}
            </p>

            <p>
                Address:
                ${escapeHtml(delivery.delivery_address)}
            </p>

            <p>
                Item:
                ${escapeHtml(delivery.item_description)}
            </p>

            <div class="assign-row">

                <select
                    id="rider-select-${deliveryId}"
                >
                    <option value="">
                        Choose a rider...
                    </option>

                    ${riderOptions}
                </select>

                <button
                    type="button"
                    onclick="assignDelivery(${deliveryId})"
                >
                    Assign
                </button>

            </div>

            <p
                id="result-${deliveryId}"
                class="result"
            ></p>
        `;

        container.appendChild(item);
    });
}


// ============================================================
// ASSIGN DELIVERY
// ============================================================

async function assignDelivery(deliveryId) {
    const riderSelect =
        document.getElementById(
            `rider-select-${deliveryId}`
        );

    const resultEl =
        document.getElementById(
            `result-${deliveryId}`
        );

    if (!riderSelect || !resultEl) {
        console.error(
            "Assignment elements not found:",
            deliveryId
        );

        return;
    }

    const riderId =
        riderSelect.value;

    // --------------------------------------------------------
    // Validate rider
    // --------------------------------------------------------

    if (!riderId) {
        showModal(
            "Rider Required",
            "Please choose a rider before assigning the delivery.",
            "error"
        );

        return;
    }

    resultEl.textContent =
        "Assigning...";

    riderSelect.disabled = true;

    const assignButton =
        riderSelect.parentElement.querySelector(
            "button"
        );

    if (assignButton) {
        assignButton.disabled = true;
    }

    try {
        const response =
            await fetch(
                `/deliveries/${deliveryId}/assign`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        rider_id:
                            parseInt(
                                riderId,
                                10
                            )
                    })
                }
            );

        const data =
            await response.json();

        // ----------------------------------------------------
        // Authentication failure
        // ----------------------------------------------------

        if (response.status === 401) {
            window.location.href =
                "/login";

            return;
        }

        if (response.status === 403) {
            window.location.href =
                "/dashboard";

            return;
        }

        // ----------------------------------------------------
        // Assignment failed
        // ----------------------------------------------------

        if (!response.ok) {
            resultEl.textContent =
                `Failed: ${
                    data.error ||
                    "Unable to assign delivery"
                }`;

            riderSelect.disabled = false;

            if (assignButton) {
                assignButton.disabled = false;
            }

            showModal(
                "Assignment Failed",
                data.error ||
                    "Unable to assign the delivery.",
                "error"
            );

            return;
        }

        // ----------------------------------------------------
        // Assignment successful
        // ----------------------------------------------------

        resultEl.textContent =
            "Delivery assigned successfully.";

        // ----------------------------------------------------
        // Show success modal
        //
        // The delivery list will refresh regardless of
        // whether the dispatcher closes the modal using:
        //     - OK
        //     - X
        //     - Clicking outside
        //     - Escape
        // ----------------------------------------------------

        showModal(
            "Delivery Assigned",
            `Delivery #${deliveryId} has been assigned successfully. ` +
                "The customer notification has been sent.",
            "success",
            async () => {
                await loadOpenDeliveries();
            }
        );

    } catch (error) {
        console.error(
            "Assignment error:",
            error
        );

        resultEl.textContent =
            "Unable to reach the server.";

        riderSelect.disabled = false;

        if (assignButton) {
            assignButton.disabled = false;
        }

        showModal(
            "Connection Error",
            "Unable to reach the server. Please try again.",
            "error"
        );
    }
}


// ============================================================
// HTML ESCAPE HELPER
// ============================================================

function escapeHtml(value) {
    if (
        value === null ||
        value === undefined
    ) {
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
// LOGOUT
// ============================================================

async function logout() {
    const logoutButton =
        document.getElementById(
            "logoutButton"
        );

    if (logoutButton) {
        logoutButton.disabled = true;

        logoutButton.textContent =
            "Logging out...";
    }

    try {
        const response =
            await fetch(
                "/logout",
                {
                    method: "POST"
                }
            );

        if (response.ok) {
            window.location.href =
                "/login";

            return;
        }

        console.error(
            "Logout failed."
        );

    } catch (error) {
        console.error(
            "Logout error:",
            error
        );
    }

    if (logoutButton) {
        logoutButton.disabled = false;

        logoutButton.textContent =
            "Logout";
    }
}


// ============================================================
// INITIALIZE
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {
        loadDispatcher();

        loadOpenDeliveries();

        // ----------------------------------------------------
        // Logout
        // ----------------------------------------------------

        const logoutButton =
            document.getElementById(
                "logoutButton"
            );

        if (logoutButton) {
            logoutButton.addEventListener(
                "click",
                logout
            );
        }

        // ----------------------------------------------------
        // Modal close buttons
        // ----------------------------------------------------

        const modalCloseButton =
            document.getElementById(
                "modalCloseButton"
            );

        const modalOkButton =
            document.getElementById(
                "modalOkButton"
            );

        if (modalCloseButton) {
            modalCloseButton.addEventListener(
                "click",
                closeModal
            );
        }

        if (modalOkButton) {
            modalOkButton.addEventListener(
                "click",
                closeModal
            );
        }

        // ----------------------------------------------------
        // Close when clicking outside modal
        // ----------------------------------------------------

        const modal =
            document.getElementById(
                "messageModal"
            );

        if (modal) {
            modal.addEventListener(
                "click",
                event => {
                    if (
                        event.target === modal
                    ) {
                        closeModal();
                    }
                }
            );
        }

        // ----------------------------------------------------
        // Close with Escape key
        // ----------------------------------------------------

        document.addEventListener(
            "keydown",
            event => {
                if (
                    event.key === "Escape"
                ) {
                    closeModal();
                }
            }
        );
    }
);
