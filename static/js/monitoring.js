// monitoring.js
// Polls the /monitoring/status endpoint every 2 seconds to update
// the result label without reloading the page.

(function () {
  function updateStatus() {
    fetch("/monitoring/status")
      .then(r => r.json())
      .then(data => {
        const label = document.getElementById("resultLabel");
        if (!label) return;
        label.textContent = data.result || "—";
        label.className = "fw-bold " + (
          data.result.includes("UNKNOWN")    ? "text-danger"  :
          data.result.includes("RECOGNIZED") ? "text-success" : "text-muted"
        );
        // Reload recent events section every 10 seconds
      })
      .catch(() => {});
  }

  // Poll every 2 seconds while the monitoring page is open
  setInterval(updateStatus, 2000);
})();
