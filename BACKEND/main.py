from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

app = FastAPI(title="RAWAT GAMBUT API Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CSV_FILE = "toy_dataset_1grid.csv"

def calculate_et0(tmax: float, tmin: float, ra: float = 15.0) -> float:
    tmean = (tmax + tmin) / 2.0
    tdiff = max(tmax - tmin, 0.0)
    et0 = 0.0023 * (tmean + 17.8) * (tdiff ** 0.5) * ra
    return round(et0, 2)

@app.get("/")
def root():
    return {"status": "Active", "message": "Backend Server RAWAT GAMBUT Siap Berjalan"}

@app.get("/api/v1/simulate")
def run_simulation(specific_yield: float = 0.15, initial_tmat: float = -0.30):
    if not os.path.exists(CSV_FILE):
        return {"error": "Toy dataset belum dibuat. Jalankan extract_toy_data.py dulu!"}

    df = pd.read_csv(CSV_FILE)
    
    dates, baseline_tmat_list, simulated_tmat_list = [], [], []
    current_baseline_tmat = initial_tmat
    current_sim_tmat = initial_tmat

    for idx, row in df.iterrows():
        tmax, tmin, precip = float(row["tmax"]), float(row["tmin"]), float(row["precip_chirps"])
        et0 = calculate_et0(tmax, tmin)

        delta_water_m = (precip - et0) / 1000.0
        
        current_baseline_tmat = min(current_baseline_tmat + (delta_water_m / 0.15), 0.0)
        current_sim_tmat = min(current_sim_tmat + (delta_water_m / specific_yield), 0.0)

        dates.append(str(row["date"]))
        baseline_tmat_list.append(round(current_baseline_tmat, 3))
        simulated_tmat_list.append(round(current_sim_tmat, 3))

    final_tmat = simulated_tmat_list[-1]
    status = "Rentan Terbakar (Kritis)" if final_tmat < -0.4 else "Aman (Terbasahi)"
    action = "Prioritas Patroli Lapangan (MPA / DMPG)" if final_tmat < -0.4 else "Pemantauan Rutin"
    alert_level = "HIGH" if final_tmat < -0.4 else "LOW"

    patrol_cost = 50000000
    waqf_yield_amount = 1000000000 * 0.0425
    funding_gap = max(patrol_cost - waqf_yield_amount, 0)

    return {
        "grid_info": {"location": "Kotawaringin Timur", "latitude": -2.21, "longitude": 113.92},
        "simulation_parameters": {"specific_yield": specific_yield, "initial_tmat": initial_tmat},
        "timeseries": {"dates": dates, "baseline_tmat": baseline_tmat_list, "simulated_tmat": simulated_tmat_list},
        "summary": {"final_tmat_m": final_tmat, "status": status, "action_required": action, "alert_level": alert_level},
        "waqf_scenario": {"patrol_cost_idr": patrol_cost, "waqf_yield_idr": waqf_yield_amount, "funding_gap_idr": funding_gap}
    }