document.addEventListener('DOMContentLoaded', () => {
    const btnNormal = document.getElementById('btn-normal');
    const btnAnomaly = document.getElementById('btn-anomaly');
    const trafficBody = document.getElementById('traffic-body');
    const totalScannedEl = document.getElementById('total-scanned');
    const totalAnomaliesEl = document.getElementById('total-anomalies');

    let totalScanned = 0;
    let totalAnomalies = 0;

    async function simulateTraffic(forceAnomaly = false) {
        btnNormal.disabled = true;
        btnAnomaly.disabled = true;

        try {
            const response = await fetch('/api/detect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    simulate: true,
                    force_anomaly: forceAnomaly
                })
            });
            const data = await response.json();

            if (!response.ok || data.status !== 'success') {
                throw new Error(data.error || 'Could not process traffic.');
            }
            updateDashboard(data);
        } catch (error) {
            console.error('Traffic simulation failed:', error);
            alert(`Error processing traffic: ${error.message}`);
        } finally {
            btnNormal.disabled = false;
            btnAnomaly.disabled = false;
        }
    }

    function addCell(row, value) {
        const cell = document.createElement('td');
        cell.textContent = value;
        row.appendChild(cell);
        return cell;
    }

    function formatNumber(value) {
        const number = Number(value);
        return Number.isFinite(number) ? number.toLocaleString() : '0';
    }

    function updateDashboard(data) {
        const { prediction, features_used: features } = data;
        const isAnomaly = prediction === 'Anomaly';

        totalScanned++;
        if (isAnomaly) totalAnomalies++;
        totalScannedEl.textContent = totalScanned;
        totalAnomaliesEl.textContent = totalAnomalies;

        const row = document.createElement('tr');
        row.className = 'row-enter';
        addCell(row, new Date().toLocaleTimeString());
        addCell(row, String(features.protocol_type || 'unknown').toUpperCase());
        addCell(row, String(features.service || 'unknown'));
        addCell(row, formatNumber(features.src_bytes));
        addCell(row, formatNumber(features.dst_bytes));

        const statusCell = addCell(row, '');
        const badge = document.createElement('span');
        badge.className = `badge ${isAnomaly ? 'anomaly' : 'normal'}`;
        badge.textContent = prediction;
        statusCell.appendChild(badge);

        trafficBody.prepend(row);
        if (trafficBody.children.length > 10) {
            trafficBody.removeChild(trafficBody.lastElementChild);
        }
    }

    btnNormal.addEventListener('click', () => simulateTraffic(false));
    btnAnomaly.addEventListener('click', () => simulateTraffic(true));
});
