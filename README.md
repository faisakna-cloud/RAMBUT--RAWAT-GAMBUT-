# RAMBUT — Model TMAT v5 (Python)

Port dari kode R model_tmat_v5 untuk integrasi **TMAT → PFVI → prioritas patroli**.

## Input
CSV berkolom `date,site,rain_mm,ET0`, tanggal ISO YYYY-MM-DD, satu baris per hari per lokasi. `rain_mm` dan `ET0` dalam mm/hari. Data tiap lokasi harus harian kontinu. ET0 Hargreaves–Samani dihitung **sebelum** menjalankan modul ini; perhitungan ET0 dari CHIRTS belum disertakan.

## Persamaan
- `below = ET0 + WF_below`
- `sementara = WTD_sebelumnya + (P - below)/(1000*Sy)`
- Bila `sementara > 0`, hitung ulang dengan `ET0 + WF_above`, lalu batasi `WTD <= 0`.
- Jika tidak, gunakan `sementara`.

Keluaran `tmat_m` bertanda negatif di bawah permukaan. Implementasi mengikuti kode R yang dilampirkan, bukan penilaian independen atas validitas fisik persamaannya.

## Instalasi
```bash
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Simulasi tanpa optimasi
Salin `config/parameters.example.csv` menjadi `config/parameters.csv`, **ganti nilai contoh dengan parameter optimal hasil R** (jangan pakai nilai contoh untuk produk ilmiah), lalu:
```bash
python run_model.py --input data/sample/example_input.csv --params config/parameters.csv --output outputs/tmat_daily.csv
```

## Optimasi (memerlukan observasi)
Data observasi: `date,site,periode,GWL_mean_m` dengan `periode` = `Kalibrasi` atau `Validasi`.
```bash
python run_model.py --input data/raw/input_daily.csv --observations data/raw/observations.csv --calibrate --params config/parameters.csv
```
NSGA-II menggunakan 100 individu dan 200 generasi; solusi numerik tidak dijamin identik dengan paket R `mco` meskipun objektif dan batas parameter sama. Data DB dibatasi sampai 2014-12-31 untuk kalibrasi dan evaluasi seperti kode R.

## Output untuk PFVI
`outputs/tmat_daily.csv`: `date,site,rain_mm,ET0,tmat_m,ET_aktual,ET_WF`.
Untuk grid spasial, tambahkan `latitude,longitude` atau `grid_id` saat menyiapkan input dan jalankan simulasi terpisah per grid. Parameter grid perlu ditentukan dan diuji; jangan otomatis menyamakan parameter lokasi UF/DF/DB dengan seluruh provinsi.

## GitHub
Commit kode, README, tes, contoh input kecil, dan parameter **terverifikasi**. Jangan commit file NetCDF besar, observasi terbatas, token, atau `.env`. Simpan raster/NetCDF historis di penyimpanan terpisah, lalu gunakan output TMAT untuk modul PFVI.

## Plot (opsional)
Gunakan `model.plots.plot_pareto(pareto, selected)` dan `model.plots.plot_observed_vs_model(simulations, observations)` untuk menyimpan grafik PNG. Grafik tidak dibuat otomatis saat menjalankan CLI.

## Batasan
- Modul ini menghitung TMAT **per lokasi**, belum membaca NetCDF langsung atau memproses raster spasial penuh.
- Rumus PFVI tidak ada dalam kode R yang diberikan, sehingga **belum diimplementasikan**. Output `tmat_m` disiapkan sebagai masukan untuk modul PFVI setelah formulanya dikonfirmasi.
- Contoh parameter dalam `config/parameters.example.csv` hanyalah placeholder, **bukan** parameter hasil optimasi.
- Bandingkan output Python dan R pada input serta parameter yang identik sebelum digunakan untuk analisis ilmiah atau dashboard publik.
