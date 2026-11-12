let tmatChart;

// Render Grafik TMAT
function renderChart(labels, dataPoints, title = 'Kabupaten Pulang Pisau') {
    const chartEl = document.getElementById('tmatChart');
    if (!chartEl) return;
    
    const ctx = chartEl.getContext('2d');
    if (tmatChart) tmatChart.destroy();
    
    tmatChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `TMAT (Meter) - ${title}`,
                data: dataPoints,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                fill: true,
                tension: 0.2,
                borderWidth: 2,
                pointRadius: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { 
                    ticks: { color: '#9ca3af', maxTicksLimit: 10 }, 
                    grid: { color: '#374151' } 
                },
                y: { 
                    min: -1.2, 
                    max: 0.1, 
                    ticks: { 
                        color: '#9ca3af',
                        callback: function(v) { return Number(v).toFixed(2) + ' m'; }
                    }, 
                    grid: { color: '#374151' } 
                }
            },
            plugins: { legend: { labels: { color: '#e5e7eb' } } }
        }
    });
}

// Fetch data timeseries per Grid dari API Backend
async function loadGridTimeseries(gridId, startDate = "2015-09-01", endDate = "2015-09-30") {
    try {
        const res = await fetch(`http://127.0.0.1:8000/api/tmat/timeseries?grid_id=${gridId}&start_date=${startDate}&end_date=${endDate}`);
        const data = await res.json();
        
        if (data.timeseries && data.timeseries.length > 0) {
            const dates = data.timeseries.map(d => String(d.tanggal).split('T')[0].split(' ')[0]);
            const tmats = data.timeseries.map(d => d.tmat);
            renderChart(dates, tmats, `Grid ID: ${gridId}`);
        }
    } catch (err) {
        console.error("Gagal memuat grafik grid:", err);
    }
}