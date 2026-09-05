async function checkHealth() {
    const result = document.getElementById("health-result");

    try {
        const response = await fetch("/");
        if (response.ok) {
            result.textContent = "Reflex API is running.";
        } else {
            result.textContent = "API responded but reported a problem.";
        }
    } catch (error) {
        result.textContent = "Unable to connect to the API.";
    }
}

async function loadDeliveries() {
    const container = document.getElementById("deliveries");

    try {
        // Corrected: no /api prefix, and this endpoint only ever
        // returns OPEN deliveries (Nathalie's dispatcher-facing view) —
        // there's no "all deliveries with names" endpoint in the real
        // backend, so this page shows what's actually open right now.
        const response = await fetch("/deliveries");
        const deliveries = await response.json();

        container.innerHTML = "";

        if (deliveries.length === 0) {
            container.innerHTML = "<p>No open delivery requests.</p>";
            return;
        }

        deliveries.forEach(delivery => {
            const item = document.createElement("div");

            item.className = "delivery";

            // Corrected: the real response has no rider_name (no join
            // is done), and no rider is ever assigned on an OPEN
            // delivery anyway — so this always reads "Not assigned",
            // which is actually correct for this view.
            item.innerHTML = `
                <strong>Delivery #${delivery.delivery_id}</strong>
                <p>Customer: ${delivery.customer_name}</p>
                <p>Address: ${delivery.delivery_address}</p>
                <p>Item: ${delivery.item_description}</p>
                <p>Status: ${delivery.status}</p>
                <p>Rider: Not assigned</p>
            `;

            container.appendChild(item);
        });

    } catch (error) {
        container.innerHTML =
            "<p>Unable to load deliveries.</p>";
    }
}
