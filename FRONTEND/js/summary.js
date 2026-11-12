// Menghitung & Mengembalikan Kategori PFAI
function getPfaiCategory(tmat) {
    if (tmat <= -0.70) return { status: "SANGAT BAHAYA (EKSTREM)", color: "text-rose-500" };
    if (tmat <= -0.50) return { status: "BAHAYA / TINGGI", color: "text-amber-500" };
    if (tmat <= -0.30) return { status: "WASPADA / SEDANG", color: "text-yellow-400" };
    return { status: "AMAN (Basah)", color: "text-emerald-400" };
}

// Update Panel Ringkasan Wilayah Secara Utuh
function updateSummaryPanel(summaryData) {
    if (!summaryData) return;
    
    if (summaryData.avg_tmat !== undefined) {
        document.getElementById('avg-tmat').innerText = `${summaryData.avg_tmat} m`;
    }
    if (summaryData.kritis_grids !== undefined) {
        document.getElementById('vulnerable-days').innerText = `${summaryData.kritis_grids} Grid Kritis`;
    }
}

// Update Panel saat Grid Spesifik Diklik
function updateGridDetailPanel(gridId, kelas, val) {
    const pfai = getPfaiCategory(val);
    
    document.getElementById('loc-name').innerText = `Grid ${gridId} (${kelas})`;
    document.getElementById('avg-tmat').innerText = `${typeof val === 'number' ? val.toFixed(2) : val} m`;
    
    const pfaiEl = document.getElementById('pfai-status');
    if (pfaiEl) {
        pfaiEl.innerText = pfai.status;
        pfaiEl.className = `font-bold ${pfai.color}`;
    }

    document.getElementById('ndbai-val').innerText = (kelas === 'DB') ? "0.62 (Kanal Sekunder Pekat)" : "0.31 (Rendah / Hutan)";
    document.getElementById('pop-density').innerText = (kelas === 'DB') ? "210 jiwa/km²" : "85 jiwa/km²";
}