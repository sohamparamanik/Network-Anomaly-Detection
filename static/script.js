document.addEventListener('DOMContentLoaded', () => {
    const btnNormal = document.getElementById('btn-normal');
    const btnAnomaly = document.getElementById('btn-anomaly');
    const trafficBody = document.getElementById('traffic-body');
    const totalScannedEl = document.getElementById('total-scanned');
    const totalAnomaliesEl = document.getElementById('total-anomalies');

    let totalScanned = 0;
    let totalAnomalies = 0;

    async function simulateTraffic(forceAnomaly = false) {
        try {
            btnNormal.disabled = true;
            btnAnomaly.disabled = true;

            const response = await fetch('/api/detect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    simulate: true,
                    force_anomaly: forceAnomaly
                })
            });

            const data = await response.json();

            if (data.status === 'success') {
                updateDashboard(data);
            } else {
                console.error('Error from server:', data.error);
                alert('Error processing traffic: ' + data.error);
            }
        } catch (error) {
            console.error('Network error:', error);
        } finally {
            btnNormal.disabled = false;
            btnAnomaly.disabled = false;
        }
    }

    function updateDashboard(data) {
        const { prediction, features_used } = data;
        const isAnomaly = prediction === 'Anomaly';

        // Update stats
        totalScanned++;
        if (isAnomaly) totalAnomalies++;

        totalScannedEl.textContent = totalScanned;
        totalAnomaliesEl.textContent = totalAnomalies;

        // Add row to table
        const row = document.createElement('tr');
        row.className = 'row-enter';

        const timestamp = new Date().toLocaleTimeString();
        
        row.innerHTML = `
            <td>${timestamp}</td>
            <td><span style="opacity: 0.8">${features_used.protocol_type.toUpperCase()}</span></td>
            <td>${features_used.service}</td>
            <td>${features_used.src_bytes.toLocaleString()}</td>
            <td>${features_used.dst_bytes.toLocaleString()}</td>
            <td>
                <span class="badge ${isAnomaly ? 'anomaly' : 'normal'}">
                    ${prediction}
                </span>
            </td>
        `;

        if (trafficBody.firstChild) {
            trafficBody.insertBefore(row, trafficBody.firstChild);
        } else {
            trafficBody.appendChild(row);
        }

        // Keep max 10 rows
        if (trafficBody.children.length > 10) {
            trafficBody.removeChild(trafficBody.lastChild);
        }
    }

    btnNormal.addEventListener('click', () => simulateTraffic(false));
    btnAnomaly.addEventListener('click', () => simulateTraffic(true));
});
