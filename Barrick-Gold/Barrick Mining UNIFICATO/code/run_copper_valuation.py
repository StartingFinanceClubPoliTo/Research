"""Paired gold-only vs gold+copper conditional operating-value experiment.

Run after fetch_ib_copper_options.py and calibrate_ib_copper_models.py.
Reports aggregate USD million, with a finite five-year primary horizon; it does
not report corporate equity value, per-share targets, or investment signals.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy.stats import norm, rankdata
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from barrick_unified.copper import attributable_copper_margin
from barrick_unified.ib_gold_adapter import sha256_file
from barrick_unified.multimodel_valuation import run_multimodel_valuation, load_team8_path_module, MODEL_ORDER
from barrick_unified.valuation import simulate_valuation_from_gold_paths

COPPER_MODELS = dict(zip(MODEL_ORDER, ['Black-76','Heston-forward','Bates-Poisson-forward','Full-Bates-Hawkes-forward']))


def simulate_copper(module, model, parameters, start, drift, dt, n, seed):
    p = parameters['parameters']
    if model == 'black_scholes':
        return module.simulate_gbm_paths(start, drift, p['sigma'], dt, n, seed)
    hp = [p[k] for k in ['v0','kappa','theta']] + [p.get('xi', p.get('sigma')), p['rho']]
    if model == 'heston':
        return module.simulate_heston_paths(start, drift, hp, dt, n, seed)[0]
    if model == 'bates_poisson':
        return module.simulate_bates_paths(start, drift, hp + [p['lambd'],p['mu_J'],p['sigma_J']], dt, n, seed)[0]
    return module.simulate_full_hawkes_paths(start, drift, p, dt, n, seed)[0]


def couple_by_terminal_scores(gold, copper, rho, seed):
    """Sensitivity copula via whole-path permutation; preserves copper marginals.

    rho is a terminal Gaussian-score assumption, not a Brownian-driver estimate.
    The primary rho=0 run keeps the independently generated paths unchanged.
    """
    if rho == 0:
        return copper
    n = len(gold)
    gold_score = norm.ppf((rankdata(gold[:, -1]) - .5) / n)
    score = rho * gold_score + np.sqrt(1 - rho*rho) * np.random.default_rng(seed).standard_normal(n)
    assigned = np.empty_like(copper)
    assigned[np.argsort(score)] = copper[np.argsort(copper[:, -1])]
    return assigned


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--calibration-dir', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--paths', type=int, default=8192)
    p.add_argument('--gold-config', type=Path, default=ROOT / 'config/multimodel_valuation_20260902_team8_refresh.json',
                   help='Frozen gold experiment to pair with copper; use the audited configuration for the Paper')
    p.add_argument('--oos-dir', type=Path, help='Attach actual temporal validation aggregates, when available')
    p.add_argument('--fixed-oos-dir', type=Path, help='Attach fixed-first-origin robustness alongside rolling OOS')
    args = p.parse_args()
    out = args.output_dir
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Refusing to overwrite an operating-value experiment')
    out.mkdir(parents=True, exist_ok=True)
    params = json.loads((args.calibration_dir / 'copper_parameters.json').read_text())
    calibration = json.loads((args.calibration_dir / 'run_manifest.json').read_text())
    for name, digest in calibration.get('files', {}).items():
        if sha256_file(args.calibration_dir / name) != digest:
            raise RuntimeError('Copper calibration hash mismatch: ' + name)
    if pd.Timestamp(calibration['market_date']).date() != pd.Timestamp('2026-09-02').date():
        raise ValueError('Copper snapshot must match this frozen September 2 gold experiment')
    temporal = {'status': 'NOT_ATTACHED', 'interpretation': 'Reserved strikes do not establish temporal OOS validation'}
    if args.oos_dir:
        evidence_path = args.oos_dir / 'run_manifest.json'
        evidence = json.loads(evidence_path.read_text())
        for name, digest in evidence['files'].items():
            if sha256_file(args.oos_dir / name) != digest:
                raise RuntimeError('Temporal evidence hash mismatch: ' + name)
        temporal = {'status': evidence['status'], 'origin_target_pairs': evidence['origin_target_pairs'],
            'admitted_dates': evidence['admitted_dates'], 'evidence_manifest_sha256': sha256_file(evidence_path),
            'forecast_design': evidence['forecast_design'], 'limitations': evidence['limitations'],
            'interpretation': 'Conditional temporal IV repricing evidence; does not validate physical prices or corporate cash flows'}
        (out / 'copper_temporal_validation.json').write_text(json.dumps(temporal, indent=2), encoding='utf-8')
        if (args.oos_dir / 'model_summary.csv').exists():
            pd.read_csv(args.oos_dir / 'model_summary.csv').to_csv(out / 'copper_temporal_model_summary.csv', index=False)
    if args.fixed_oos_dir:
        if not args.oos_dir:
            raise ValueError('Attach rolling evidence before fixed-origin robustness')
        fixed_path = args.fixed_oos_dir / 'run_manifest.json'
        fixed = json.loads(fixed_path.read_text())
        if fixed['rolling_manifest_sha256'] != sha256_file(args.oos_dir / 'run_manifest.json'):
            raise RuntimeError('Fixed-origin evidence references a different rolling run')
        for name, digest in fixed['files'].items():
            if sha256_file(args.fixed_oos_dir / name) != digest:
                raise RuntimeError('Fixed-origin evidence hash mismatch: ' + name)
        temporal['fixed_origin_robustness'] = {'origin_date': fixed['origin_date'],
            'origin_target_pairs': fixed['origin_target_pairs'], 'scope': fixed['scope'],
            'evidence_manifest_sha256': sha256_file(fixed_path), 'limitations': fixed['limitations']}
        pd.read_csv(args.fixed_oos_dir / 'model_summary.csv').to_csv(out / 'copper_fixed_origin_model_summary.csv', index=False)
        (out / 'copper_temporal_validation.json').write_text(json.dumps(temporal, indent=2), encoding='utf-8')
    ops_path = ROOT / 'config/copper_operating_20260902.json'
    ops = json.loads(ops_path.read_text())
    gold_config_path = args.gold_config
    gold_config = json.loads(gold_config_path.read_text())
    gold_config['simulation']['n_simulations'] = args.paths
    gold = run_multimodel_valuation(ROOT, gold_config)
    module = load_team8_path_module(ROOT / gold_config['gold_price_layer']['team8_source_dir'])
    nsteps = 260
    dt = .25 * gold.inputs.n_quarters / nsteps
    snapshot = pd.Timestamp(calibration['market_date'])
    aggregate_path = args.calibration_dir / 'copper_forward_delivery_anchors.csv'
    if aggregate_path.exists():
        anchors = pd.read_csv(aggregate_path)
        if anchors.future_delivery_years.duplicated().any():
            raise ValueError('Duplicate copper future-delivery anchors')
        forwards = anchors.set_index('future_delivery_years').forward_usd_per_lb.sort_index()
    else:
        surface = pd.read_csv(args.calibration_dir / 'copper_calibration_surface.csv')
        delivery_dates = pd.to_datetime(surface.future_expiry.astype(str), format='%Y%m%d', utc=True) + pd.Timedelta(hours=20)
        surface['future_delivery_years'] = (delivery_dates - snapshot).dt.total_seconds() / (365.25 * 86400)
        forwards = surface.groupby('future_delivery_years').future_mid.mean().sort_index()
    if len(forwards) == 0 or not np.isfinite(forwards.to_numpy()).all() or (forwards <= 0).any() or (forwards.index <= 0).any():
        raise ValueError('Copper delivery anchors must have positive maturities and levels')
    start = float(forwards.iloc[0])
    tenor = np.r_[0., forwards.index.to_numpy()]
    levels = np.r_[start, forwards.to_numpy()]
    times = np.arange(nsteps + 1) * dt
    # Match observed HG delivery anchors; hold last observed level beyond support.
    targets = np.exp(np.interp(times, tenor, np.log(levels)))
    drift = np.diff(np.log(targets)) / dt
    pd.DataFrame({'time_years': times, 'conditional_forward_anchor_usd_per_lb': targets,
                  'beyond_observed_support': times > tenor[-1]}).to_csv(out / 'copper_forward_anchor.csv', index=False)
    sales = np.repeat(np.array([m['sales_kt'] for m in ops['mines']])[:, None], gold.inputs.n_quarters, axis=1)
    costs = np.repeat(np.array([m['cost_of_sales_usd_per_lb'] for m in ops['mines']])[:, None], gold.inputs.n_quarters, axis=1)
    summaries, quantiles, mine_rows, path_diagnostics = [], [], [], []
    primary_arrays = {}
    for model_id in MODEL_ORDER:
        gold_paths = gold.models[model_id].quarterly_gold_paths
        copper_fine = simulate_copper(module, model_id, params[COPPER_MODELS[model_id]], start, drift,
                                     dt, args.paths, 20262003)
        copper_paths = copper_fine[:, np.arange(13, 261, 13)]
        if not np.isfinite(copper_paths).all() or (copper_paths <= 0).any():
            raise RuntimeError('Non-finite or non-positive copper simulation')
        for q in range(gold.inputs.n_quarters):
            sample = copper_paths[:,q]
            expected = targets[(q + 1) * 13]
            se = sample.std(ddof=1) / np.sqrt(args.paths)
            path_diagnostics.append({'model': model_id, 'forward_quarter': q + 1,
                'target_conditional_mean_usd_per_lb': expected, 'sample_mean_usd_per_lb': sample.mean(),
                'sample_mean_se': se, 'mean_deviation_se_units': (sample.mean() - expected) / se,
                'zero_or_nonfinite_paths': 0})
        for rho in [0., -.5, .5]:
            coupled = couple_by_terminal_scores(gold_paths, copper_paths, rho, 20263003)
            margin, by_mine = attributable_copper_margin(coupled, sales, costs)
            for terminal in ['none', 'signed']:
                base = simulate_valuation_from_gold_paths(gold.inputs, gold_paths, gold.wacc_shocks, terminal)
                combined = simulate_valuation_from_gold_paths(gold.inputs, gold_paths, gold.wacc_shocks, terminal, margin)
                assert np.array_equal(base.annual_wacc, combined.annual_wacc)
                np.testing.assert_allclose(combined.annual_component_margin_usd_mn,
                    base.annual_component_margin_usd_mn + margin.reshape(args.paths, 5, 4).sum(axis=2))
                delta = combined.enterprise_value_proxy_usd_mn - base.enterprise_value_proxy_usd_mn
                label = 'finite_5y_primary' if terminal == 'none' else 'signed_perpetuity_sensitivity'
                summaries.append({'model': model_id, 'scope': label, 'terminal_score_rho_assumption': rho,
                    'paths': args.paths, 'gold_only_mean_usd_mn': base.enterprise_value_proxy_usd_mn.mean(),
                    'gold_plus_copper_mean_usd_mn': combined.enterprise_value_proxy_usd_mn.mean(),
                    'paired_copper_increment_mean_usd_mn': delta.mean(),
                    'gold_plus_copper_median_usd_mn': np.median(combined.enterprise_value_proxy_usd_mn),
                    'gold_plus_copper_sd_usd_mn': combined.enterprise_value_proxy_usd_mn.std(ddof=1),
                    'mc_mean_increment_se_usd_mn': delta.std(ddof=1) / np.sqrt(args.paths)})
                for pct in [5,25,50,75,95]:
                    quantiles.append({'model': model_id, 'scope': label, 'rho': rho, 'percentile': pct,
                        'gold_only_usd_mn': np.percentile(base.enterprise_value_proxy_usd_mn, pct),
                        'gold_plus_copper_usd_mn': np.percentile(combined.enterprise_value_proxy_usd_mn, pct),
                        'paired_copper_increment_usd_mn': np.percentile(delta, pct)})
                if terminal == 'none' and rho == 0:
                    primary_arrays[model_id] = (base.enterprise_value_proxy_usd_mn, combined.enterprise_value_proxy_usd_mn)
            if rho == 0:
                for index, mine in enumerate(ops['mines']):
                    for q in range(gold.inputs.n_quarters):
                        mine_rows.append({'model': model_id, 'mine': mine['mine'], 'forward_quarter': q + 1,
                            'sales_attributable_kt_scenario': sales[index,q], 'cost_usd_per_lb_scenario': costs[index,q],
                            'mean_copper_price_usd_per_lb': coupled[:,q].mean(),
                            'mean_cos_margin_usd_mn': by_mine[:,index,q].mean()})
        print(f'[VALUE] {model_id}: completed paired gold+copper scenarios', flush=True)
    summary = pd.DataFrame(summaries)
    summary.to_csv(out / 'gold_plus_copper_summary.csv', index=False)
    pd.DataFrame(quantiles).to_csv(out / 'gold_plus_copper_quantiles.csv', index=False)
    pd.DataFrame(mine_rows).to_csv(out / 'copper_mine_quarter_scenarios.csv', index=False)
    pd.DataFrame(path_diagnostics).to_csv(out / 'copper_path_mean_diagnostics.csv', index=False)
    # Publish only aggregate calibration scores alongside valuation results.
    metrics = pd.read_csv(args.calibration_dir / 'copper_model_metrics.csv')
    metrics.to_csv(out / 'copper_model_metrics.csv', index=False)
    primary = summary[(summary.scope == 'finite_5y_primary') & (summary.terminal_score_rho_assumption == 0)]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    x = np.arange(len(primary))
    axes[0].bar(x - .18, primary.gold_only_mean_usd_mn / 1000, .36, label='Gold only')
    axes[0].bar(x + .18, primary.gold_plus_copper_mean_usd_mn / 1000, .36, label='Gold + copper')
    axes[0].set_xticks(x, ['Black-76/GBM','Heston','Bates','Hawkes'], rotation=15)
    axes[0].set_ylabel('Mean 5-year operating-value proxy (USD bn)')
    axes[0].legend()
    axes[1].bar(x, primary.paired_copper_increment_mean_usd_mn / 1000, color='#b87333')
    axes[1].set_xticks(x, ['Black-76/GBM','Heston','Bates','Hawkes'], rotation=15)
    axes[1].set_ylabel('Paired mean copper increment (USD bn)')
    fig.suptitle('Conditional gold + copper experiment | no terminal value | independent price scenarios')
    fig.tight_layout()
    fig.savefig(out / 'gold_plus_copper_comparison.png', dpi=180)
    plt.close(fig)
    fig, axis = plt.subplots(figsize=(8, 4.5))
    splits = list(metrics.split.unique())
    width = .72 / len(splits)
    for index, split in enumerate(splits):
        rows = metrics[metrics.split == split].set_index('model').reindex(list(COPPER_MODELS.values()))
        offset = (index - (len(splits) - 1) / 2) * width
        axis.bar(np.arange(4) + offset, rows.iv_rmse_bp, width, label=split.replace('_', ' '))
    axis.set_xticks(np.arange(4), ['Black-76','Heston','Bates','Hawkes'])
    axis.set_ylabel('Implied-volatility RMSE (basis points)')
    axis.set_title(f"Copper: {calibration['training_rows']} fitted quotes, {calibration['reserved_rows']} reserved strikes\nConditional American-equivalent IV; temporal evidence reported separately")
    axis.legend()
    fig.tight_layout()
    fig.savefig(out / 'copper_model_validation.png', dpi=180)
    plt.close(fig)
    manifest = {'status': 'CONDITIONAL_OPERATING_VALUE_PROXY_NOT_CORPORATE_FAIR_VALUE',
       'market_snapshot': calibration['market_date'], 'generated_at_utc': datetime.now(timezone.utc).isoformat(),
       'copper_calibration_dir': str(args.calibration_dir), 'calibration_manifest_sha256': sha256_file(args.calibration_dir / 'run_manifest.json'),
       'copper_operating_config_sha256': sha256_file(ops_path), 'gold_experiment_config_sha256': sha256_file(gold_config_path),
       'gold_experiment_config': str(gold_config_path),
       'gold_base_config_sha256': sha256_file(ROOT / gold_config['base_valuation_config']),
       'gold_common_input_hashes': gold.common_input_hashes, 'gold_wacc_shocks_sha256': gold.wacc_shocks_sha256,
       'gold_parameter_sha256': {model_id: sha256_file(gold.models[model_id].parameter_path) for model_id in MODEL_ORDER},
       'source_code_sha256': {str(path.relative_to(ROOT)): sha256_file(path) for path in [
           Path(__file__).resolve(), ROOT / 'src/barrick_unified/copper.py',
           ROOT / 'src/barrick_unified/valuation.py', ROOT / 'src/barrick_unified/multimodel_valuation.py',
           ROOT / gold_config['gold_price_layer']['team8_source_dir'] / 'path_simulation.py']},
       'paths': args.paths, 'copper_price_seed': 20262003, 'dependence_seed': 20263003,
       'primary_horizon': 'Five years, no terminal value', 'sensitivity_terminal': 'Signed perpetuity using inherited growth/ROIC/WACC assumptions',
       'copper_curve': {'start_usd_per_lb': start, 'last_observed_maturity_years': float(tenor[-1]),
          'construction': 'log-linear matched-HG forward anchors at actual future delivery dates; last level held flat beyond observed support',
          'spot_forecast': False},
       'dependence': 'rho=0 independent; +/-0.5 terminal Gaussian-score copula sensitivities, whole-path permutation preserving copper marginal paths; no estimated Brownian correlation',
       'ops': ops, 'american_approximation': calibration['american_approximation'],
       'temporal_validation': temporal,
       'gold_baseline_preservation': 'Frozen parameters and common gold/WACC paths; compare the same terminal policy and aggregate pathwise before percentiles',
       'limitations': ops['limitations'] + ['European stochastic models fitted to constant-volatility American-equivalent quotes', 'Reserved-strike validation is not temporal OOS', 'Tax/growth/ROIC margin transform is not reconciled copper cash flow', 'Frozen gold baseline uses company-wide Q1-Q2 actuals followed by an eight-mine forecast; actual/forecast asset scope is not yet reconciled'],
       'files': {f.name: sha256_file(f) for f in out.iterdir() if f.is_file()}}
    (out / 'run_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(primary.to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
