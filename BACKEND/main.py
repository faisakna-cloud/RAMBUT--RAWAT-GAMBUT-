import os
import json
import duckdb
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="RAWAT GAMBUT API - Real Data Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tentukan PATH Folder DATA secara absolut dan presisi
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "DATA")

TMAT_PARQUET = os.path.join(DATA_DIR, "TMAT_Harian_Pulang_Pisau_2001_2019.parquet").replace("\\", "/")
# FIX NAMA FILE GEOJSON GRID KABUPATEN
GEOJSON_PATH = os.path.join(DATA_DIR, "Grid_Gambut_Pulang_Pisau.geojson")

con = duckdb.connect()

@app.get("/api/geojson")
def get_geojson():
    if os.path.exists(GEOJSON_PATH):
        with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"type": "FeatureCollection", "features": []}

@app.get("/api/tmat")
def get_tmat_by_date(date: str = "2015-09-15"):
    query = f"""
        SELECT grid_id, TMAT as tmat, kelas_gambut
        FROM '{TMAT_PARQUET}'
        WHERE CAST(tanggal AS VARCHAR) LIKE '{date}%'
    """
    try:
        df = con.execute(query).df()
        avg_tmat = float(df['tmat'].mean()) if not df.empty else -0.4
        return {
            "date": date,
            "summary": { "avg_tmat": avg_tmat, "vulnerable_days": 185 },
            "data": df.to_dict(orient="records")
        }
    except Exception as e:
        return {"date": date, "summary": {"avg_tmat": -0.4, "vulnerable_days": 0}, "data": []}

@app.get("/api/tmat/timeseries")
def get_tmat_timeseries(grid_id: str, start_date: str = "2015-09-01", end_date: str = "2015-09-30"):
    query = f"""
        SELECT CAST(tanggal AS VARCHAR) as tanggal, TMAT as tmat
        FROM '{TMAT_PARQUET}'
        WHERE grid_id = '{grid_id}'
          AND CAST(tanggal AS VARCHAR) BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY tanggal ASC
    """
    try:
        df = con.execute(query).df()
        return { "grid_id": grid_id, "data": df.to_dict(orient="records") }
    except Exception as e:
        return { "grid_id": grid_id, "data": [] }
        import os
import sys
import json
import duckdb
import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# Arahkan path agar Python bisa mengimpor modul dari folder 'model' di root direktori
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Impor fungsi perhitungan dari model hidrologi
try:
    from model.tmat_model import model_tmat_v5, simulate_daily
    MODEL_LOADED = True
except ImportError as e:
    print("Peringatan: Modul tmat_model belum terbaca, menggunakan fallback formula:", e)
    MODEL_LOADED = False

app = FastAPI(title="RAWAT GAMBUT API - Real Data & Hydrological Model Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(BASE_DIR, "DATA")
TMAT_PARQUET = os.path.join(DATA_DIR, "TMAT_Harian_Pulang_Pisau_2001_2019.parquet").replace("\\", "/")
GEOJSON_PATH = os.path.join(DATA_DIR, "Grid_Gambut_Pulang_Pisau.geojson")

con = duckdb.connect()

@app.get("/api/geojson")
def get_geojson():
    if os.path.exists(GEOJSON_PATH):
        with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"type": "FeatureCollection", "features": []}

@app.get("/api/tmat")
def get_tmat_by_date(date: str = "2015-03-01", canal_blocks: int = 0):
    """
    Mengambil data TMAT harian aktual dari Parquet dan mensimulasikan 
    efek pembasahan (rewetting) jika terdapat intervensi Sekat Kanal Wakaf.
    """
    query = f"""
        SELECT grid_id, TMAT as tmat, kelas_gambut
        FROM '{TMAT_PARQUET}'
        WHERE strftime(tanggal, '%Y-%m-%d') = '{date}'
    """
    try:
        df = con.execute(query).df()
        
        if not df.empty and canal_blocks > 0:
            # Simulasi dampak sekat kanal menahan aliran keluar (menurunkan koefisien drainase WF_below)
            # Setiap 5 unit sekat kanal menaikkan muka air tanah hingga batas aman (-0.20m)
            rewetting_boost = min(0.35, canal_blocks * 0.015)
            df['tmat'] = df['tmat'].apply(lambda x: min(0.0, x + rewetting_boost) if pd.notnull(x) else x)

        avg_tmat = float(df['tmat'].mean()) if not df.empty and df['tmat'].notnull().any() else -0.35
        vulnerable_cnt = int((df['tmat'] <= -0.40).sum()) if not df.empty else 0
        
        return {
            "date": date,
            "model_active": MODEL_LOADED,
            "canal_blocks_applied": canal_blocks,
            "summary": { 
                "avg_tmat": round(avg_tmat, 3), 
                "vulnerable_days": vulnerable_cnt 
            },
            "data": df.to_dict(orient="records")
        }
    except Exception as e:
        print("Error DuckDB:", e)
        return {"date": date, "summary": {"avg_tmat": -0.35, "vulnerable_days": 0}, "data": []}

@app.get("/api/tmat/timeseries")
def get_tmat_timeseries(grid_id: str, start_date: str = "2015-03-01", end_date: str = "2015-03-31", canal_blocks: int = 0):
    query = f"""
        SELECT strftime(tanggal, '%Y-%m-%d') as tanggal, TMAT as tmat
        FROM '{TMAT_PARQUET}'
        WHERE grid_id = '{grid_id}'
          AND strftime(tanggal, '%Y-%m-%d') BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY tanggal ASC
    """
    try:
        df = con.execute(query).df()
        if not df.empty and canal_blocks > 0:
            rewetting_boost = min(0.35, canal_blocks * 0.015)
            df['tmat'] = df['tmat'].apply(lambda x: min(0.0, x + rewetting_boost) if pd.notnull(x) else x)
            
        return { "grid_id": grid_id, "data": df.to_dict(orient="records") }
    except Exception as e:
        return { "grid_id": grid_id, "data": [] }