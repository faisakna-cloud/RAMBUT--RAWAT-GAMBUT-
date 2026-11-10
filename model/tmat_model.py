"""Port langsung dari model_tmat_v5 R. WTD dalam meter, P/ET/WF dalam mm/hari."""
import numpy as np
import pandas as pd


def model_tmat_v5(hujan, ET0, wtd_awal=-0.5, Sy=0.48, WF_below=1.0, WF_above=45.0):
    rain = np.asarray(hujan, dtype=float)
    et = np.asarray(ET0, dtype=float)
    if rain.ndim != 1 or et.ndim != 1 or len(rain) != len(et):
        raise ValueError('hujan dan ET0 harus array 1D dengan panjang sama')
    if not (np.isfinite(rain).all() and np.isfinite(et).all() and np.isfinite(wtd_awal)):
        raise ValueError('Input mengandung NA atau nilai tidak valid')
    if Sy <= 0 or WF_below <= 0 or WF_above < WF_below:
        raise ValueError('Parameter model tidak valid')
    n = len(rain)
    wtd = np.empty(n)
    loss = np.empty(n)
    kondisi = float(wtd_awal)
    for i in range(n):
        below = et[i] + WF_below
        sementara = kondisi + (rain[i] - below) / (1000.0 * Sy)
        if sementara > 0:
            kehilangan = et[i] + WF_above
            baru = min(kondisi + (rain[i] - kehilangan) / (1000.0 * Sy), 0.0)
        else:
            kehilangan = below
            baru = sementara
        wtd[i] = baru
        loss[i] = kehilangan
        kondisi = baru
    return pd.DataFrame({'WTD': wtd, 'ET_aktual': et, 'ET_WF': loss})


def simulate_daily(data, params, wtd_awal=-0.5):
    """Data harus memiliki date, rain_mm, ET0; keluaran siap untuk PFVI."""
    required = {'date', 'rain_mm', 'ET0'}
    if not required.issubset(data.columns):
        raise ValueError(f'Kolom wajib: {sorted(required)}')
    df = data.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    if df.date.duplicated().any():
        raise ValueError('Tanggal duplikat')
    if (df.date.diff().dropna() != pd.Timedelta(days=1)).any():
        raise ValueError('Input harus harian kontinu; periksa tanggal hilang')
    result = model_tmat_v5(df.rain_mm, df.ET0, wtd_awal=wtd_awal, **params)
    return pd.concat([df, result.rename(columns={'WTD': 'tmat_m'})], axis=1)
