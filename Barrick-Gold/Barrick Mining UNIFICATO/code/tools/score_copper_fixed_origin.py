"""Robustness: freeze the first admitted copper fit across later pilot dates."""
from pathlib import Path
import argparse
import json
import pandas as pd
from run_copper_oos import score, summarize
from barrick_unified.ib_gold_adapter import sha256_file

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--panel-dir', type=Path, required=True)
    p.add_argument('--rolling-dir', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    a = p.parse_args()
    if a.output_dir.exists() and any(a.output_dir.iterdir()):
        raise FileExistsError('Use a new fixed-origin run directory')
    a.output_dir.mkdir(parents=True, exist_ok=True)
    rolling_path = a.rolling_dir / 'run_manifest.json'
    rolling = json.loads(rolling_path.read_text())
    if rolling['status'] != 'COMPLETE':
        raise ValueError('Finish the declared historical pilot before fixed-origin scoring')
    dates = rolling['admitted_dates']
    if len(dates) < 2:
        raise ValueError('Need at least two admitted historical surfaces')
    origin = dates[0]
    local = a.panel_dir / 'oos_local'
    cdir = local / 'calibrations' / origin
    origin_surface = pd.read_csv(cdir / 'copper_calibration_surface.csv')
    params = json.loads((cdir / 'copper_parameters.json').read_text())
    forecast_dir = local / 'fixed_origin' / origin
    forecast_dir.mkdir(parents=True, exist_ok=True)
    all_metrics = []
    inputs = {}
    for date in dates:
        folder = local / 'calibrations' / date
        manifest = json.loads((folder / 'run_manifest.json').read_text())
        for name, digest in manifest['files'].items():
            if sha256_file(folder / name) != digest:
                raise RuntimeError('Calibration integrity failure: ' + date + ' ' + name)
        inputs[date] = sha256_file(folder / 'run_manifest.json')
        if date == origin:
            continue
        target = pd.read_csv(folder / 'copper_calibration_surface.csv')
        metrics, forecasts = score(origin, date, origin_surface, target, params)
        all_metrics.extend(metrics)
        forecasts.to_csv(forecast_dir / f'{origin}_to_{date}_forecasts.csv', index=False)
    metrics = pd.DataFrame(all_metrics)
    metrics.to_csv(a.output_dir / 'date_metrics.csv', index=False)
    summary = summarize(metrics)
    summary.to_csv(a.output_dir / 'model_summary.csv', index=False)
    manifest = {'status': 'COMPLETE', 'scope': 'Fixed-first-origin robustness on the same preliminary historical pilot',
        'origin_date': origin, 'admitted_dates': dates, 'origin_target_pairs': len(dates)-1,
        'forecast_design': 'First admitted fit frozen; variance/intensity projected to each later date; actual target forwards/as-of rates condition scoring',
        'rolling_manifest_sha256': sha256_file(rolling_path), 'calibration_manifest_sha256': inputs,
        'source_code_sha256': sha256_file(Path(__file__)),
        'limitations': rolling['limitations'] + ['Targets overlap the rolling sample; this is a robustness check, not an independent second dataset'],
        'files': {f.name: sha256_file(f) for f in a.output_dir.iterdir() if f.is_file()}}
    (a.output_dir / 'run_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(summary.to_string(index=False))

if __name__ == '__main__':
    main()
