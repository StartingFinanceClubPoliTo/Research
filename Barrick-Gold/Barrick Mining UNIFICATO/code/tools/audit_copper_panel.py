"""Check actual historical copper coverage before allowing a temporal OOS run."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from barrick_unified.copper import copper_surface
from barrick_unified.ib_gold_adapter import sha256_file
from barrick_unified.ib_gold_surface import normalized_call_surface


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--panel-dir',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location('copper_historical_rates',ROOT/'parity/sources/team-8-current/src/rates.py')
    rates=importlib.util.module_from_spec(spec);sys.modules[spec.name]=rates;spec.loader.exec_module(rates)
    history_path=ROOT/'paper_audit/team8_data/data/processed/usd_treasury_history.csv'
    history=rates.load_rate_history(history_path)
    calendar=json.loads((ROOT/'data/processed/team8/oos_20260902/run_manifest.json').read_text())['surface_dates']
    planned=json.loads((args.panel_dir/'panel_manifest.json').read_text())['planned_dates']
    rows=[];file_hashes={}
    for date in calendar:
        folder=args.panel_dir/date
        path=folder/'hg_futures_option_bid_ask.csv'
        row={'date':date,'acquisition_status':'NOT_ACQUIRED' if date in planned else 'NOT_PLANNED_IN_PILOT','raw_quotes':0,'eligible_quotes':0,
             'eligible_expiries':0,'dense_admitted':False,'response_timeouts':np.nan}
        if not path.exists():
            rows.append(row);continue
        file_hashes[str(path)]=sha256_file(path)
        mp=folder/'run_manifest.json'
        manifest=json.loads(mp.read_text()) if mp.exists() else {}
        row['acquisition_status']='RETURNED_DATA' if manifest.get('valid_quotes',0)>0 else 'NO_QUOTES_RETRIEVED'
        row['response_timeouts']=sum(e.get('code')=='response_timeout' for e in manifest.get('ib_errors',[]))
        try:raw=pd.read_csv(path)
        except pd.errors.EmptyDataError:raw=pd.DataFrame()
        row['raw_quotes']=len(raw)
        if raw.empty:
            rows.append(row);continue
        fit,curve,curve_date=rates.nss_fit_for_date(date,history)
        assert curve_date<=pd.Timestamp(date)
        audit,metadata=copper_surface(raw,rate_curve=lambda t:rates.nss_rates(t,fit),
            rate_metadata={**fit.to_dict(),'curve_date':str(curve_date.date()),'no_lookahead':True})
        audit.loc[audit.maturity_years_act36525*365.25<75,'exclusion_reason']='below_75_dte'
        eligible=audit[audit.exclusion_reason.eq('eligible')]
        local=args.panel_dir/'quality_surfaces'/date
        local.mkdir(parents=True,exist_ok=True)
        audit.to_csv(local/'quote_audit.csv',index=False)
        if len(eligible):
            normalized_call_surface(audit).to_csv(local/'copper_surface.csv',index=False)
        row.update(eligible_quotes=len(eligible),eligible_expiries=eligible.option_expiry.nunique(),
            dense_admitted=len(eligible)>=64 and eligible.option_expiry.nunique()>=3,
            curve_date=str(curve_date.date()),nss_rmse_bp=fit.rmse_bps,
            exclusions=json.dumps(audit.exclusion_reason.value_counts().to_dict()))
        rows.append(row)
        print(f'[QUALITY] {date}: {len(raw)} raw -> {len(eligible)} eligible; dense={row["dense_admitted"]}',flush=True)
    frame=pd.DataFrame(rows)
    frame.to_csv(args.output_dir/'historical_coverage.csv',index=False)
    admitted=frame[frame.dense_admitted].date.tolist()
    m={'status':'READY_FOR_TEMPORAL_OOS' if len(admitted)>=2 else 'INSUFFICIENT_DENSE_HISTORY_FOR_TEMPORAL_OOS',
       'gold_reference_dates':len(calendar),'planned_dates':len(planned),
       'acquired_dates':int(frame.acquisition_status.isin(['RETURNED_DATA','NO_QUOTES_RETRIEVED']).sum()),
       'scope':'Coverage of the declared copper pilot, with unplanned gold reference dates explicitly separated',
       'admitted_dates':admitted,'possible_next_admitted_date_pairs':max(0,len(admitted)-1),
       'threshold':{'minimum_actual_quotes':64,'minimum_expiries':3,'minimum_dte':75,'max_age_seconds':120,'max_relative_spread':.20},
       'interpretation':'Retrieval failure or unacquired dates do not establish historical data absence. No OOS scores may be reported without eligible chronological pairs.',
       'date_specific_rates':{'source':str(history_path),'sha256':sha256_file(history_path),'selection':'latest curve date <= observation date'},
       'inputs':file_hashes,'files':{'historical_coverage.csv':sha256_file(args.output_dir/'historical_coverage.csv')}}
    (args.output_dir/'coverage_manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
    print(json.dumps({k:m[k] for k in ['status','acquired_dates','admitted_dates','possible_next_admitted_date_pairs']}),flush=True)

if __name__=='__main__':main()
