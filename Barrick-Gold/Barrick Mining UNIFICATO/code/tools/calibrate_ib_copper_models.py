"""Audit copper quotes, reserve strikes, and fit four conditional option models."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy.optimize import OptimizeResult
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
# Use the safeguarded, audited pricing engines rather than the old frozen fits.
sys.path.insert(0, str(ROOT / 'paper_audit' / 'pricing'))
from Heston import Heston
from Bates import Bates
from Hawkes import ExactHawkesCalibration
from barrick_unified.copper import copper_surface
from barrick_unified.ib_gold_surface import normalized_call_surface
from barrick_unified.ib_gold_adapter import sha256_file
from barrick_unified.ib_gold_calibration import (Team8Modules, calibrate_black76,
    add_parameter_diagnostics, deterministic_strike_holdout, model_diagnostics,
    price_model_calls, _weighted_objective)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--maxiter', type=int, default=35)
    p.add_argument('--popsize', type=int, default=6)
    args = p.parse_args()
    out = args.output_dir
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Refusing to overwrite a calibrated copper run')
    out.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(args.input)
    audit, metadata = copper_surface(raw)
    audit.to_csv(out / 'quote_and_american_audit.csv', index=False)
    surface = normalized_call_surface(audit)
    surface.to_csv(out / 'copper_calibration_surface.csv', index=False)
    train, holdout = deterministic_strike_holdout(surface)
    if len(surface) < 50 or surface.option_expiry.nunique() < 4 or len(holdout) < 8:
        raise RuntimeError(f'Insufficient eligible coverage: {len(surface)} quotes, {surface.option_expiry.nunique()} expiries')
    # Cross-calendar monotonicity is not a hard restriction across DIFFERENT HG futures.
    # Record within-expiry midpoint violations, without repairing observed quotes.
    shape = []
    for expiry, group in surface.groupby('option_expiry'):
        group = group.sort_values('K')
        slope = np.diff(group.price) / np.diff(group.K)
        shape.append({'expiry': str(expiry), 'rows': len(group),
                      'midpoint_monotonicity_violations': int((slope > 1e-8).sum()),
                      'midpoint_convexity_violations': int((np.diff(slope) < -1e-8).sum())})
    metadata['within_expiry_shape_diagnostics'] = shape
    metadata['calendar_policy'] = 'No cross-expiry calendar monotonicity imposed on different deliverable futures'
    train.to_csv(out / 'training_strikes.csv', index=False)
    holdout.to_csv(out / 'reserved_strikes.csv', index=False)
    modules = Team8Modules(Bates, None, ExactHawkesCalibration)
    results = {}
    def save(model, payload):
        payload = add_parameter_diagnostics(payload)
        pars = payload['parameters']
        if 'sigma' in pars and 'kappa' in pars:
            payload['feller_gap'] = 2 * pars['kappa'] * pars['theta'] - pars['sigma']**2
        # Validate finite, Feller-admissible parameters before downstream simulation.
        if not np.isfinite(payload['values']).all() or payload.get('feller_gap', 0) < -1e-7:
            raise RuntimeError(f'Invalid fitted parameter candidate for {model}')
        results[model] = payload
        (out / 'copper_parameters.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
        print(f'[FIT] {model}: objective={payload["objective"]:.8g}; {payload["message"]}', flush=True)
    print(f'[SURFACE] {len(surface)} eligible; {len(train)} training; {len(holdout)} reserved', flush=True)
    save('Black-76', calibrate_black76(train))
    hp = Heston.calibrate_heston(train, 1., q=0., maxiter=args.maxiter, popsize=args.popsize,
                                seed=20261003, return_report=True).as_dict()
    hp['model'] = 'Heston-forward'
    # Include the exact constant-volatility boundary with a tiny admissible xi.
    sigma = results['Black-76']['values'][0]
    nested = np.array([sigma*sigma, 2., sigma*sigma, .01, 0.])
    loss = _weighted_objective('Heston-forward', nested, train, modules, 256)
    if loss < hp['objective']:
        hp.update(values=nested.tolist(), objective=loss, message='Retained nearly constant-variance Black-76 boundary', success=True)
    save('Heston-forward', hp)
    bp = Bates.calibrate_bates(train, 1., q=0., maxiter=args.maxiter, popsize=args.popsize,
                              seed=20261004, return_report=True, heston_seed=hp['values']).as_dict()
    bp['model'] = 'Bates-Poisson-forward'
    save('Bates-Poisson-forward', bp)
    hz = ExactHawkesCalibration.calibrate_heston(train, 1., q=0., bates_seed=bp['values'],
             maxiter=max(15, args.maxiter // 2), popsize=args.popsize, seed=20261005,
             global_cos_N=128, local_cos_N=256, min_branching=0.)
    names = ['v0','kappa','theta','xi','rho','lambda0','lambda_bar','branching_ratio','beta','mu_J','sigma_J']
    save('Full-Bates-Hawkes-forward', {'model': 'Full-Bates-Hawkes-forward', 'parameter_names': names,
         'values': hz.x.tolist(), 'objective': float(hz.fun), 'success': bool(hz.success),
         'message': str(hz.message), 'evaluations': int(getattr(hz, 'nfev', 0))})
    metrics, diagnostics = [], []
    for model, result in results.items():
        for split, frame in [('training', train), ('reserved_strikes', holdout)]:
            diag, summary = model_diagnostics(model, result, frame, modules)
            diag['split'] = split
            summary['split'] = split
            metrics.append(summary)
            diagnostics.append(diag)
    pd.DataFrame(metrics).to_csv(out / 'copper_model_metrics.csv', index=False)
    pd.concat(diagnostics).to_csv(out / 'copper_model_residuals.csv', index=False)
    metadata.update({'status': 'CONDITIONAL_COPPER_OPTION_CALIBRATION', 'instrument': 'COMEX HG/HXE',
         'market_date': str(raw.snapshot_utc.iloc[0]), 'training_rows': len(train), 'reserved_rows': len(holdout),
         'holdout_scope': 'Interpolation across reserved strikes; NOT temporal out-of-sample validation',
         'input_path': str(args.input), 'input_sha256': sha256_file(args.input),
         'pricing_source': 'paper_audit/pricing: audited candidate retention and nested limits',
         'optimizer': {'maxiter': args.maxiter, 'popsize': args.popsize, 'seeds': [20261003,20261004,20261005]},
         'generated_at_utc': datetime.now(timezone.utc).isoformat(),
         'files': {f.name: sha256_file(f) for f in out.iterdir() if f.is_file()}})
    (out / 'run_manifest.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(pd.DataFrame(metrics)[['model','split','observations','iv_rmse_bp']].to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
