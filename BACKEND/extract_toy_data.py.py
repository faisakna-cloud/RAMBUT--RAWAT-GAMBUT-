import os
import glob
import xarray as xr
import pandas as pd
import numpy as np

TARGET_LAT = -2.21
TARGET_LON = 113.92

# Path mengarah ke folder DATA/Tmax dan DATA/Tmin
DATA_DIR = os.path.join("..", "DATA")
tmax_dir = os.path.join(DATA_DIR, "Tmax")
tmin_dir = os.path.join(DATA_DIR, "Tmin")

print("Mencari file NetCDF...")
tmax_files = glob.glob(os.path.join(tmax_dir, "*.nc"))
tmin_files = glob.glob(os.path.join(tmin_dir, "*.nc"))

if not tmax_files or not tmin_files:
    print("⚠️ File .nc tidak ditemukan di Tmax/Tmin. Membuat dataset dummy untuk testing...")
    dates = pd.date_range(start="2026-01-01", periods=30, freq="D")
    df_toy = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "tmax": np.random.uniform(31.0, 34.5, size=len(dates)),
        "tmin": np.random.uniform(23.0, 25.5, size=len(dates)),
        "precip_chirps": np.random.choice([0.0, 0.0, 5.2, 12.0, 0.0, 25.4], size=len(dates))
    })
else:
    print(f"Menemukan {len(tmax_files)} file Tmax dan {len(tmin_files)} file Tmin. Memproses...")
    ds_tmax = xr.open_mfdataset(tmax_files)
    ds_tmin = xr.open_mfdataset(tmin_files)

    sub_tmax = ds_tmax.sel(lat=TARGET_LAT, lon=TARGET_LON, method="nearest")
    sub_tmin = ds_tmin.sel(lat=TARGET_LAT, lon=TARGET_LON, method="nearest")

    df_tmax = sub_tmax.to_dataframe().reset_index()
    df_tmin = sub_tmin.to_dataframe().reset_index()

    df_toy = pd.DataFrame({
        "date": df_tmax["time"].dt.strftime("%Y-%m-%d"),
        "tmax": df_tmax.iloc[:, -1],
        "tmin": df_tmin.iloc[:, -1],
        "precip_chirps": 5.0
    })

output_csv = "toy_dataset_1grid.csv"
df_toy.to_csv(output_csv, index=False)
print(f"✅ SUKSES! File '{output_csv}' berhasil dibuat.")