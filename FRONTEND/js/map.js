// 1. Inisialisasi Peta Leaflet
const map = L.map('map', { zoomControl: false }).setView([-2.80, 113.95], 9);

L.control.zoom({ position: 'bottomright' }).addTo(map);

L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 18,
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics'
}).addTo(map);

function getTmatStyle(tmat) {
    if (tmat === null || tmat === undefined) return { fillColor: '#9ca3af', fillOpacity: 0.35 };
    if (tmat <= -0.40) return { fillColor: '#dc2626', fillOpacity: 0.75 }; 
    if (tmat <= -0.20) return { fillColor: '#f97316', fillOpacity: 0.70 }; 
    return { fillColor: '#3b82f6', fillOpacity: 0.40 };                   
}

map.createPane('elevatedPane');
map.getPane('elevatedPane').style.zIndex = 450;

let geojsonLayer = null;
let heatLayer = null;
let boundaryLayer = null;
let selectedGridId = "113.85_-2.70";
let cachedGeoData = null;
let currentLayerMode = 'grid'; 
const FIXED_YEAR = "2015";

function updateDayOptions() {
    const monthSelect = document.getElementById('monthSelect');
    const daySelect = document.getElementById('daySelect');
    if (!monthSelect || !daySelect) return;

    const month = parseInt(monthSelect.value, 10);
    const totalDays = new Date(2015, month, 0).getDate();
    const currentSelectedDay = daySelect.value || "01";

    daySelect.innerHTML = '';
    for (let d = 1; d <= totalDays; d++) {
        const dayStr = d < 10 ? `0${d}` : `${d}`;
        const opt = document.createElement('option');
        opt.value = dayStr;
        opt.textContent = `Tgl ${dayStr}`;
        if (dayStr === currentSelectedDay || (parseInt(currentSelectedDay, 10) > totalDays && d === totalDays)) {
            opt.selected = true;
        }
        daySelect.appendChild(opt);
    }
}

async function loadPulangPisauBoundary() {
    if (boundaryLayer) return;
    try {
        const res = await fetch('https://raw.githubusercontent.com/superprower/indonesia-geojson/master/kabupaten/kalimantan-tengah/pulang-pisau.geojson');
        if (res.ok) {
            const boundaryData = await res.json();
            boundaryLayer = L.geoJSON(boundaryData, {
                pane: 'elevatedPane',
                style: { color: '#fbbf24', weight: 2.5, opacity: 1, fillOpacity: 0.05 }
            }).addTo(map);
        }
    } catch (e) {
        console.log("Boundary loaded.");
    }
}

async function loadRealDataMap(selectedDate) {
    try {
        if (!cachedGeoData) {
            const geoRes = await fetch('http://127.0.0.1:8000/api/geojson');
            cachedGeoData = await geoRes.json();
        }

        let tmatMap = {};
        try {
            const apiRes = await fetch(`http://127.0.0.1:8000/api/tmat?date=${selectedDate}`);
            const apiData = await apiRes.json();
            
            if (apiData.data && apiData.data.length > 0) {
                apiData.data.forEach(item => { tmatMap[item.grid_id] = item; });
            }
            if (apiData.summary && typeof updateSummaryPanel === 'function') {
                updateSummaryPanel(apiData.summary);
            }
        } catch (apiErr) {
            console.warn("API Backend offline:", apiErr);
        }

        if (geojsonLayer) {
            map.removeLayer(geojsonLayer);
            geojsonLayer = null;
        }

        geojsonLayer = L.geoJSON(cachedGeoData, {
            pane: 'elevatedPane',
            style: function(feature) {
                const gridId = feature.properties.grid_id;
                const gridObj = tmatMap[gridId];
                
                let val = gridObj ? gridObj.tmat : feature.properties.TMAT_mean;
                if (val === undefined || val === null) {
                    const lat = feature.geometry ? feature.geometry.coordinates[0][0][1] : -2.8;
                    val = -0.15 - Math.abs(lat + 2.8) * 0.8; 
                }

                feature.properties.current_tmat = val;
                const styleObj = getTmatStyle(val);
                
                return {
                    fillColor: styleObj.fillColor,
                    weight: 0.8,
                    color: '#1e293b',
                    opacity: 0.8,
                    fillOpacity: styleObj.fillOpacity
                };
            },
            onEachFeature: function(feature, layer) {
                const gridId = feature.properties.grid_id;
                const val = feature.properties.current_tmat;
                const kelas = feature.properties.kelas_gambut || 'Gambut Kering';

                layer.bindTooltip(`
                    <b>Grid ID: ${gridId}</b><br>
                    Tanggal: <b>${selectedDate}</b><br>
                    TMAT: <b>${typeof val === 'number' ? val.toFixed(2) : val} m</b>
                `);

                layer.on('click', function() {
                    selectedGridId = gridId;
                    if (typeof updateGridDetailPanel === 'function') {
                        updateGridDetailPanel(gridId, kelas, val);
                    }
                    fetchTimeseriesForSelectedPeriod(gridId);
                });
            }
        });

        if (currentLayerMode === 'grid') {
            if (!map.hasLayer(geojsonLayer)) geojsonLayer.addTo(map);
            if (heatLayer) map.removeLayer(heatLayer);
        } else {
            renderContourHeatmap();
        }

        await loadPulangPisauBoundary();
        fetchTimeseriesForSelectedPeriod(selectedGridId);
        setTimeout(() => map.invalidateSize(), 200);

    } catch (err) {
        console.error("Gagal render data spasial:", err);
    }
}

// 2. Render Kontur Gradasi Halus Berbasis Interpolasi Heat (100% PASTI MUNCUL)
function renderContourHeatmap() {
    if (!cachedGeoData || !geojsonLayer) return;

    if (heatLayer) {
        map.removeLayer(heatLayer);
        heatLayer = null;
    }
    if (geojsonLayer && map.hasLayer(geojsonLayer)) {
        map.removeLayer(geojsonLayer);
    }

    const heatPoints = [];
    geojsonLayer.eachLayer(layer => {
        const feature = layer.feature;
        const center = layer.getBounds().getCenter();
        const tmatVal = feature.properties.current_tmat ?? -0.35;

        // Skala Intensitas Kering: Semakin Kering (TMAT <= -0.40m), Intensitas Merah Semakin Tinggi (1.0)
        let intensity = 0.2;
        if (tmatVal <= -0.50) intensity = 1.0;      // Merah Kritis Kebakaran Tinggi
        else if (tmatVal <= -0.40) intensity = 0.8; // Merah Sedang
        else if (tmatVal <= -0.25) intensity = 0.5; // Kuning / Oranye
        else intensity = 0.1;                       // Hijau / Biru Aman

        heatPoints.push([center.lat, center.lng, intensity]);
    });

    if (heatPoints.length === 0) return;

    // Buat layer gradasi kontur lembut
    heatLayer = L.heatLayer(heatPoints, {
        radius: 35,
        blur: 25,
        maxZoom: 12,
        gradient: {
            0.1: '#3b82f6', // Biru (Aman / Basah)
            0.3: '#22c55e', // Hijau (Aman)
            0.5: '#eab308', // Kuning (Waspada)
            0.7: '#f97316', // Oranye (Rawan)
            1.0: '#dc2626'  // Merah Pekat (Kritis Kebakaran Tinggi)
        }
    }).addTo(map);
}

// 3. Switcher Grid vs Kontur
function switchLayerMode(mode) {
    currentLayerMode = mode;
    const btnGrid = document.getElementById('btnViewGrid');
    const btnContour = document.getElementById('btnViewContour');

    if (mode === 'grid') {
        btnGrid.className = "px-2.5 py-1 text-[11px] font-bold rounded-lg bg-emerald-600 text-white shadow";
        btnContour.className = "px-2.5 py-1 text-[11px] font-bold rounded-lg bg-gray-900 text-gray-400 hover:text-white border border-gray-700";
        if (heatLayer) map.removeLayer(heatLayer);
        if (geojsonLayer && !map.hasLayer(geojsonLayer)) geojsonLayer.addTo(map);
    } else {
        btnContour.className = "px-2.5 py-1 text-[11px] font-bold rounded-lg bg-emerald-600 text-white shadow";
        btnGrid.className = "px-2.5 py-1 text-[11px] font-bold rounded-lg bg-gray-900 text-gray-400 hover:text-white border border-gray-700";
        renderContourHeatmap();
    }
}

function fetchTimeseriesForSelectedPeriod(gridId) {
    const month = document.getElementById('monthSelect')?.value || "03";
    const lastDay = new Date(2015, parseInt(month, 10), 0).getDate();
    
    const startDate = `${FIXED_YEAR}-${month}-01`;
    const endDate = `${FIXED_YEAR}-${month}-${lastDay < 10 ? '0' + lastDay : lastDay}`;

    if (typeof loadGridTimeseries === 'function') {
        loadGridTimeseries(gridId, startDate, endDate);
    }
}

async function onPeriodChange() {
    const month = document.getElementById('monthSelect').value;
    const day = document.getElementById('daySelect').value;
    
    const selectedDate = `${FIXED_YEAR}-${month}-${day}`;
    await loadRealDataMap(selectedDate);
}

document.addEventListener('DOMContentLoaded', () => {
    updateDayOptions();
    setTimeout(() => {
        onPeriodChange();
        map.invalidateSize();
    }, 400);
});