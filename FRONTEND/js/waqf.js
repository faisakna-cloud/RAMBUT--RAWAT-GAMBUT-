// Kalkulator Alokasi Dana Wakaf
function calculateWaqf() {
    const areaSlider = document.getElementById('areaSlider');
    if (!areaSlider) return;

    const ha = areaSlider.value;
    document.getElementById('areaVal').innerText = `${ha} Ha`;
    
    const blocks = Math.ceil(ha / 20);
    const patrols = Math.ceil(ha / 50);
    const total = (blocks * 12000000) + (patrols * 7500000);

    document.getElementById('canalBlocks').innerText = `${blocks} Unit`;
    document.getElementById('patrolUnits').innerText = `${patrols} Tim`;
    document.getElementById('totalWaqf').innerText = `Rp ${total.toLocaleString('id-ID')}`;
}

// Inisialisasi saat script dimuat
document.addEventListener('DOMContentLoaded', () => {
    calculateWaqf();
});