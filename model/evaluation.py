import numpy as np
import pandas as pd


def hitung_metrik(obs, model):
    o, m = np.asarray(obs, float), np.asarray(model, float)
    valid = np.isfinite(o) & np.isfinite(m)
    o, m = o[valid], m[valid]
    if len(o) < 2 or np.std(o, ddof=1) == 0 or np.std(m, ddof=1) == 0 or abs(np.mean(o)) < 1e-10:
        return {'r': np.nan, 'KGE': np.nan, 'PBIAS': np.nan}
    r = np.corrcoef(o, m)[0, 1]
    alpha = np.std(m, ddof=1) / np.std(o, ddof=1)
    beta = np.mean(m) / np.mean(o)
    kge = 1 - np.sqrt((r-1)**2 + (alpha-1)**2 + (beta-1)**2)
    pbias = 100 * np.sum(m-o) / np.sum(o)
    return {'r': r, 'KGE': kge, 'PBIAS': pbias}


def evaluate_site(sim, observations, site):
    obs = observations[observations.site == site].copy()
    obs['date'] = pd.to_datetime(obs['date'])
    if site == 'DB':
        obs = obs[obs.date <= '2014-12-31']
    merged = obs.merge(sim[['date', 'tmat_m']], on='date', how='inner')
    rows = []
    for period, part in merged.groupby('periode'):
        metrics = hitung_metrik(part.GWL_mean_m, part.tmat_m)
        rows.append({'site': site, 'periode': period, 'N': len(part), **metrics})
    return pd.DataFrame(rows)
