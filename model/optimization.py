"""NSGA-II via pymoo; objektif sama dengan mco::nsga2 pada kode R."""
import numpy as np
import pandas as pd
from .tmat_model import simulate_daily
from .evaluation import hitung_metrik


def optimize_site(input_data, observations, site, popsize=100, generations=200, seed=123):
    from pymoo.core.problem import ElementwiseProblem
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.optimize import minimize

    df = input_data[input_data.site == site].copy()
    obs = observations[(observations.site == site) & (observations.periode == 'Kalibrasi')].copy()
    obs['date'] = pd.to_datetime(obs['date'])
    if site == 'DB':
        obs = obs[obs.date <= '2014-12-31']
    if obs.date.duplicated().any():
        raise ValueError(f'Observasi tanggal duplikat: {site}')
    if len(obs.merge(df[['date']], on='date')) < 2:
        raise ValueError(f'Data kalibrasi tidak cukup: {site}')

    class WTDProblem(ElementwiseProblem):
        def __init__(self):
            super().__init__(n_var=3, n_obj=2, xl=np.array([.30, .1, 10.]), xu=np.array([.60, 10., 100.]))
        def _evaluate(self, x, out, *args, **kwargs):
            sy, wf_below, wf_above = x
            if wf_above < wf_below:
                out['F'] = [1e6, 1e6]
                return
            try:
                sim = simulate_daily(df, {'Sy': sy, 'WF_below': wf_below, 'WF_above': wf_above})
                joined = obs.merge(sim[['date', 'tmat_m']], on='date', how='inner')
                metrics = hitung_metrik(joined.GWL_mean_m, joined.tmat_m)
                vals = [1-metrics['KGE'], abs(metrics['PBIAS'])]
                out['F'] = vals if np.isfinite(vals).all() else [1e6, 1e6]
            except (ValueError, KeyError):
                out['F'] = [1e6, 1e6]

    result = minimize(WTDProblem(), NSGA2(pop_size=popsize), ('n_gen', generations), seed=seed, verbose=False)
    if result.X is None:
        raise RuntimeError(f'Tidak ada solusi NSGA-II: {site}')
    pareto = pd.DataFrame(np.atleast_2d(result.X), columns=['Sy', 'WF_below', 'WF_above'])
    objective = np.atleast_2d(result.F)
    pareto.insert(0, 'site', site)
    pareto['KGE'] = 1-objective[:, 0]
    pareto['Abs_PBIAS'] = objective[:, 1]
    pareto = pareto.replace([np.inf, -np.inf], np.nan).dropna().drop_duplicates()
    pareto = pareto[(pareto.KGE > -1e5) & (pareto.Abs_PBIAS < 1e5)]
    return pareto


def select_optimal(pareto):
    rows = []
    for site, group in pareto.groupby('site'):
        valid = group[group.Abs_PBIAS <= 10]
        if len(valid):
            selected = valid.sort_values(['KGE', 'Abs_PBIAS'], ascending=[False, True]).iloc[0].to_dict()
            selected['Memenuhi_PBIAS'] = True
        else:
            selected = group.sort_values(['Abs_PBIAS', 'KGE'], ascending=[True, False]).iloc[0].to_dict()
            selected['Memenuhi_PBIAS'] = False
        rows.append(selected)
    return pd.DataFrame(rows)
