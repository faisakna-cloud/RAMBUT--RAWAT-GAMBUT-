"""CLI: kalibrasi (opsional) dan simulasi model untuk input PFVI."""
import argparse
from pathlib import Path
import pandas as pd
from model.tmat_model import simulate_daily
from model.optimization import optimize_site, select_optimal
from model.evaluation import evaluate_site


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='CSV date,site,rain_mm,ET0')
    parser.add_argument('--params', default='config/parameters.csv', help='Parameter hasil kalibrasi')
    parser.add_argument('--observations', help='CSV date,site,periode,GWL_mean_m')
    parser.add_argument('--calibrate', action='store_true', help='Jalankan NSGA-II, bukan parameter tersimpan')
    parser.add_argument('--output', default='outputs/tmat_daily.csv')
    args = parser.parse_args()
    df = pd.read_csv(args.input, parse_dates=['date'])
    if args.calibrate:
        if not args.observations:
            parser.error('--calibrate memerlukan --observations')
        obs = pd.read_csv(args.observations, parse_dates=['date'])
        pareto = pd.concat([optimize_site(df, obs, site) for site in ('UF', 'DF', 'DB')], ignore_index=True)
        Path('outputs').mkdir(exist_ok=True)
        pareto.to_csv('outputs/pareto.csv', index=False)
        params_df = select_optimal(pareto)
        Path(args.params).parent.mkdir(parents=True, exist_ok=True)
        params_df.to_csv(args.params, index=False)
    else:
        params_df = pd.read_csv(args.params)
    outputs, evaluations = [], []
    for site in sorted(df.site.unique()):
        row = params_df[params_df.site == site]
        if len(row) != 1:
            raise ValueError(f'Parameter harus tepat satu baris untuk {site}')
        params = {k: float(row.iloc[0][k]) for k in ('Sy', 'WF_below', 'WF_above')}
        sim = simulate_daily(df[df.site == site].drop(columns='site'), params)
        sim.insert(1, 'site', site)
        outputs.append(sim)
        if args.observations:
            obs = pd.read_csv(args.observations, parse_dates=['date'])
            evaluations.append(evaluate_site(sim, obs, site))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(outputs, ignore_index=True).to_csv(out, index=False)
    print(f'TMAT harian tersimpan: {out}')
    if evaluations:
        evaluation_file = out.with_name('evaluation.csv')
        pd.concat(evaluations, ignore_index=True).to_csv(evaluation_file, index=False)
        print(f'Evaluasi tersimpan: {evaluation_file}')


if __name__ == '__main__':
    main()
