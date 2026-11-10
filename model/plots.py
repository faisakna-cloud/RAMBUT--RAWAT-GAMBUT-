"""Visualisasi pengganti ggplot pada kode R (opsional)."""
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from .evaluation import hitung_metrik


def plot_pareto(pareto, selected, output='outputs/pareto.png'):
    sites = sorted(pareto.site.unique())
    fig, axes = plt.subplots(1, len(sites), figsize=(5 * len(sites), 4), squeeze=False)
    for ax, site in zip(axes[0], sites):
        p = pareto[pareto.site == site]
        s = selected[selected.site == site]
        ax.scatter(p.Abs_PBIAS, p.KGE, alpha=.7, label='Pareto')
        ax.scatter(s.Abs_PBIAS, s.KGE, color='red', label='Terpilih')
        ax.axvline(10, linestyle='--', color='red')
        ax.set(title=site, xlabel='|PBIAS| (%)', ylabel='KGE')
        ax.legend()
    fig.tight_layout()
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_observed_vs_model(simulations, observations, output='outputs/tmat_validation.png'):
    df = observations.copy()
    df['date'] = pd.to_datetime(df['date'])
    sim = simulations.copy()
    sim['date'] = pd.to_datetime(sim['date'])
    merged = df.merge(sim[['site', 'date', 'tmat_m']], on=['site', 'date'], how='inner')
    merged = merged[(merged.site != 'DB') | (merged.date <= '2014-12-31')]
    sites = sorted(merged.site.unique())
    periods = [p for p in ['Kalibrasi', 'Validasi'] if p in merged.periode.unique()]
    fig, axes = plt.subplots(len(sites), len(periods), figsize=(7 * len(periods), 3 * len(sites)), squeeze=False)
    for i, site in enumerate(sites):
        for j, period in enumerate(periods):
            ax = axes[i, j]
            p = merged[(merged.site == site) & (merged.periode == period)].sort_values('date')
            ax.plot(p.date, p.GWL_mean_m, linewidth=.7, label='Observasi')
            ax.plot(p.date, p.tmat_m, linewidth=.7, label='Model')
            met = hitung_metrik(p.GWL_mean_m, p.tmat_m)
            ax.set(title=f'{site} – {period}', ylabel='TMAT (m)')
            ax.text(.02, .03, f"r={met['r']:.3f}\nKGE={met['KGE']:.3f}\nPBIAS={met['PBIAS']:.2f}%", transform=ax.transAxes, va='bottom', fontsize=8)
            ax.legend()
    fig.tight_layout()
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)
