document.addEventListener("DOMContentLoaded", function () {
    const statusText = document.getElementById("status");
    const lockButton = document.getElementById("lock");
    const unlockButton = document.getElementById("unlock");

    const SERVER_URL = "http://";

    async function fetchScooterStatus() {
        try {
            const response = await fetch(`${SERVER_URL}/status`);
            const data = await response.json();
            statusText.innerText = data.locked ? "Locked" : "Unlocked";
        } catch (error) {
            console.error("Error fetching scooter status:", error);
            statusText.innerText = "Error fetching status";
        }
    }

    async function sendCommand(action) {
        try {
            const response = await fetch(`${SERVER_URL}/${action}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                }
            });
            if (response.ok) {
                fetchScooterStatus(); // Update UI after request
            } else {
                console.error("Error updating scooter status");
            }
        } catch (error) {
            console.error("Error sending request:", error);
        }
    }

    lockButton.addEventListener("click", () => sendCommand("lock"));
    unlockButton.addEventListener("click", () => sendCommand("unlock"));

    fetchScooterStatus(); // Load initial scooter status
});