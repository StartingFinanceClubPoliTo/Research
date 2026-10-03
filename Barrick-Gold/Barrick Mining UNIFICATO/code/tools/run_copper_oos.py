"""Chronological copper refits and next-available-date conditional IV scoring.

Only origin options enter fitting; target forwards/rates condition scoring.
All four models share target support. Persistence stays inside the origin
surface hull. Losses retain both date-equal and pooled aggregations. Licensed
surfaces/residuals remain in data/raw/ib_local; public outputs are aggregates.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import time
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import QhullError
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'paper_audit/pricing'))
# The audited OOS module imports Sampling/BnS from its original team package.
# Append the dependency directory so audited pricing modules keep precedence.
sys.path.append(str(ROOT/'parity/sources/team-8-current/src'))
from Heston import Heston
from Bates import Bates
from Hawkes import ExactHawkesCalibration
from barrick_unified.copper import copper_surface
from barrick_unified.ib_gold_surface import normalized_call_surface,black76_implied_vol
from barrick_unified.ib_gold_adapter import sha256_file
from barrick_unified.ib_gold_calibration import (Team8Modules,calibrate_black76,add_parameter_diagnostics,
    model_diagnostics,price_model_calls,_weighted_objective)
from oos_validation import project_model_state

MODELS=['Black-76','Heston-forward','Bates-Poisson-forward','Full-Bates-Hawkes-forward']
MODEL_KEYS=dict(zip(MODELS,['bs','heston','bates','hawkes']))
MODULES=Team8Modules(Bates,None,ExactHawkesCalibration)


def fit_models(surface,seed,maxiter=35,popsize=6):
    results={}
    results[MODELS[0]]=calibrate_black76(surface)
    hp=Heston.calibrate_heston(surface,1.,q=0.,maxiter=maxiter,popsize=popsize,
                              seed=seed,return_report=True).as_dict();hp['model']=MODELS[1]
    sigma=results[MODELS[0]]['values'][0]
    nested=np.array([sigma*sigma,2.,sigma*sigma,.01,0.])
    loss=_weighted_objective(MODELS[1],nested,surface,MODULES,256)
    if loss<hp['objective']:
        hp.update(values=nested.tolist(),objective=loss,success=True,message='Retained nearly constant variance boundary')
    results[MODELS[1]]=hp
    bp=Bates.calibrate_bates(surface,1.,q=0.,maxiter=maxiter,popsize=popsize,seed=seed+1,
        return_report=True,heston_seed=hp['values']).as_dict();bp['model']=MODELS[2]
    results[MODELS[2]]=bp
    hz=ExactHawkesCalibration.calibrate_heston(surface,1.,q=0.,bates_seed=bp['values'],
        maxiter=max(15,maxiter//2),popsize=popsize,seed=seed+2,
        global_cos_N=128,local_cos_N=256,min_branching=0.)
    results[MODELS[3]]={'model':MODELS[3],'parameter_names':['v0','kappa','theta','xi','rho',
        'lambda0','lambda_bar','branching_ratio','beta','mu_J','sigma_J'],
        'values':hz.x.tolist(),'objective':float(hz.fun),'success':bool(hz.success),'message':str(hz.message)}
    for model,p in list(results.items()):
        p=add_parameter_diagnostics(p)
        pars=p['parameters']
        if 'kappa' in pars:
            p['feller_gap']=2*pars['kappa']*pars['theta']-pars.get('xi',pars.get('sigma'))**2
        if not np.isfinite(p['values']).all() or not np.isfinite(p['objective']) or p.get('feller_gap',0)<-1e-7:
            raise RuntimeError('Invalid fitted candidate '+model)
        results[model]=p
    return results


def persistence(origin,target):
    x=np.column_stack([origin['T'],np.log(origin['K'])])
    y=np.column_stack([target['T'],np.log(target['K'])])
    scale=np.ptp(x,axis=0)
    if (scale<=1e-12).any():return np.full(len(target),np.nan)
    try:return np.asarray(LinearNDInterpolator(x/scale,origin.implied_vol,fill_value=np.nan)(y/scale))
    except (QhullError,ValueError):return np.full(len(target),np.nan)


def score(origin_date,target_date,origin,target,results):
    gap=(pd.Timestamp(target_date)-pd.Timestamp(origin_date)).days
    if gap<=0:raise ValueError('Target must strictly follow origin')
    predicted={}
    for model,payload in results.items():
        pars=project_model_state(MODEL_KEYS[model],payload['parameters'],gap/365.25)
        values=np.array([pars[k] for k in payload['parameter_names']])
        prices=price_model_calls(model,values,target,MODULES,256)
        iv=[]
        for row,price in zip(target.itertuples(index=False),prices):
            try:iv.append(black76_implied_vol(float(price),1.,row.K,row.T,0.,'C'))
            except ValueError:iv.append(np.nan)
        predicted[model]=np.array(iv)
    observed=target.implied_vol.to_numpy()
    common=np.isfinite(observed)&np.isfinite(np.column_stack(list(predicted.values()))).all(axis=1)
    pers=persistence(origin,target);common_pers=common&np.isfinite(pers)
    mean_iv=float(origin.implied_vol.mean())
    rows=[];residuals=target[['option_con_id','option_expiry','K','T','implied_vol']].copy()
    residuals['origin_date']=origin_date;residuals['target_date']=target_date
    residuals['persistence_iv']=pers;residuals['mean_benchmark_iv']=mean_iv
    residuals['common_model_support']=common;residuals['common_persistence_support']=common_pers
    for model,pred in predicted.items():
        residuals[model+'_iv']=pred
        a=(observed[common]-pred[common])**2
        b=(observed[common]-mean_iv)**2
        c=(observed[common_pers]-pred[common_pers])**2
        d=(observed[common_pers]-pers[common_pers])**2
        rows.append({'origin_date':origin_date,'target_date':target_date,'gap_days':gap,'model':model,
            'target_rows':len(target),'common_n':int(common.sum()),'persistence_n':int(common_pers.sum()),
            'mse_iv':float(a.mean()) if len(a) else np.nan,
            'rmse_iv_bp':float(np.sqrt(a.mean())*1e4) if len(a) else np.nan,
            'mean_benchmark_mse_iv':float(b.mean()) if len(b) else np.nan,
            'model_mse_on_persistence_support_iv':float(c.mean()) if len(c) else np.nan,
            'persistence_mse_iv':float(d.mean()) if len(d) else np.nan})
    return rows,residuals


def summarize(metrics):
    rows=[]
    for model,g in metrics.groupby('model',sort=False):
        for bench,loss,benchmark,ncol in [('origin_mean','mse_iv','mean_benchmark_mse_iv','common_n'),
            ('persistence','model_mse_on_persistence_support_iv','persistence_mse_iv','persistence_n')]:
            q=g[g[ncol]>0].dropna(subset=[loss,benchmark])
            if q.empty:continue
            a=q[loss].to_numpy();b=q[benchmark].to_numpy();n=q[ncol].to_numpy()
            rows.append({'model':model,'benchmark':bench,'dates':len(q),'observations':int(n.sum()),
                'mean_daily_rmse_bp':float(np.sqrt(a).mean()*1e4),'root_mean_daily_mse_bp':float(np.sqrt(a.mean())*1e4),
                'date_equal_oos_r2':float(1-a.sum()/b.sum()) if b.sum()>0 else np.nan,
                'pooled_oos_r2':float(1-np.dot(a,n)/np.dot(b,n)) if np.dot(b,n)>0 else np.nan})
    return pd.DataFrame(rows)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--panel-dir',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--watch',action='store_true')
    p.add_argument('--maxiter',type=int,default=35)
    p.add_argument('--popsize',type=int,default=6)
    args=p.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    source_hash=sha256_file(Path(__file__))
    # Row-level output stays below the already ignored raw tree.
    local=args.panel_dir/'oos_local';local.mkdir(exist_ok=True)
    spec=importlib.util.spec_from_file_location('copper_oos_rates',ROOT/'parity/sources/team-8-current/src/rates.py')
    rates=importlib.util.module_from_spec(spec);sys.modules[spec.name]=rates;spec.loader.exec_module(rates)
    history_path=ROOT/'paper_audit/team8_data/data/processed/usd_treasury_history.csv'
    history=rates.load_rate_history(history_path)
    gold_calendar=json.loads((ROOT/'data/processed/team8/oos_20260902/run_manifest.json').read_text())['surface_dates']
    calendar=json.loads((args.panel_dir/'panel_manifest.json').read_text())['planned_dates']
    if calendar!=sorted(set(calendar)) or not set(calendar).issubset(gold_calendar):
        raise ValueError('Historical pilot must be a unique chronological subset of the frozen gold dates')
    surfaces={};params={};coverage=[];metric_rows=[];scored=set();processed=set()
    def save_progress(status):
        pd.DataFrame(coverage).to_csv(args.output_dir/'origin_target_coverage.csv',index=False)
        if metric_rows:
            metrics=pd.DataFrame(metric_rows);metrics.to_csv(args.output_dir/'date_metrics.csv',index=False)
            summarize(metrics).to_csv(args.output_dir/'model_summary.csv',index=False)
        manifest={'status':status,'calendar':calendar,'processed_dates':sorted(processed),'admitted_dates':sorted(surfaces),
           'gold_reference_calendar':gold_calendar,'reference_dates_not_planned':sorted(set(gold_calendar)-set(calendar)),
           'scope':'Historical copper pilot; completeness refers to planned dates, not the entire gold calendar',
           'origin_target_pairs':len(scored),'forecast_design':'conditional next-admitted-date IV repricing; structural parameters origin-only, projected variance/intensity; target matching HG forwards and as-of NSS condition scoring',
           'threshold':{'min_actual_quotes':64,'min_expiries':3,'min_dte':75,'max_age_seconds':120,'max_relative_spread':.20},
           'rate_history_sha256':sha256_file(history_path),'optimizer':{'maxiter':args.maxiter,'popsize':args.popsize},
           'source_code_sha256':source_hash,
           'panel_manifest_sha256':sha256_file(args.panel_dir/'panel_manifest.json'),
           'sampling':'all eligible origin quotes from approx100 uniformly spaced requests; not the gold CC64 sample',
           'acquisition_selection':json.loads((args.panel_dir/'panel_manifest.json').read_text())['selection'],
           'limitations':['Currently discoverable contract universe has survivorship limits','Constant-volatility de-Americanization approximation','Conditional repricing is not a physical price forecast'],
           'updated_at_utc':datetime.now(timezone.utc).isoformat(),
           'files':{f.name:sha256_file(f) for f in args.output_dir.iterdir() if f.is_file() and f.name!='run_manifest.json'}}
        (args.output_dir/'run_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    while True:
        progress=False
        for date in calendar:
            if date in processed:continue
            folder=args.panel_dir/date;mp=folder/'run_manifest.json'
            if not mp.exists():break
            acquisition=json.loads(mp.read_text())
            if acquisition.get('acquisition_status')!='COMPLETE':break
            for name,digest in acquisition['files'].items():
                if sha256_file(folder/name)!=digest:
                    raise RuntimeError('Historical acquisition hash mismatch: '+str(folder/name))
            rawpath=folder/'hg_futures_option_bid_ask.csv'
            try:raw=pd.read_csv(rawpath)
            except pd.errors.EmptyDataError:raw=pd.DataFrame()
            row={'date':date,'raw_quotes':len(raw),'eligible_quotes':0,'expiries':0,'dense_admitted':False,
                 'raw_sha256':sha256_file(rawpath),'response_timeouts':acquisition.get('response_timeout_count',0)}
            if len(raw):
                fit,curve,curve_date=rates.nss_fit_for_date(date,history)
                assert curve_date<=pd.Timestamp(date)
                audit,metadata=copper_surface(raw,rate_curve=lambda t:rates.nss_rates(t,fit),
                    rate_metadata={**fit.to_dict(),'curve_date':str(curve_date.date()),'no_lookahead':True})
                audit.loc[audit.maturity_years_act36525*365.25<75,'exclusion_reason']='below_75_dte'
                eligible=audit[audit.exclusion_reason.eq('eligible')]
                row.update(eligible_quotes=len(eligible),expiries=eligible.option_expiry.nunique(),
                           dense_admitted=len(eligible)>=64 and eligible.option_expiry.nunique()>=3,
                           curve_date=str(curve_date.date()))
                cdir=local/'calibrations'/date;cdir.mkdir(parents=True,exist_ok=True)
                audit.to_csv(cdir/'quote_audit.csv',index=False)
                if row['dense_admitted']:
                    surface=normalized_call_surface(audit);surfaces[date]=surface
                    surface.to_csv(cdir/'copper_calibration_surface.csv',index=False)
                    cp=cdir/'copper_parameters.json'
                    if cp.exists():
                        prior=json.loads((cdir/'run_manifest.json').read_text())
                        if prior['input_sha256']!=sha256_file(rawpath):
                            raise RuntimeError('Origin input changed; use a new OOS local directory')
                        if prior['files']['copper_parameters.json']!=sha256_file(cp):
                            raise RuntimeError('Origin calibration hash mismatch')
                        results=json.loads(cp.read_text())
                    else:
                        seed=int(date.replace('-',''))
                        results=fit_models(surface,seed,args.maxiter,args.popsize)
                        cp.write_text(json.dumps(results,indent=2),encoding='utf-8')
                    params[date]=results
                    calibration_metrics=[]
                    for model,result in results.items():
                        _,scores=model_diagnostics(model,result,surface,MODULES)
                        scores['split']='training';calibration_metrics.append(scores)
                    pd.DataFrame(calibration_metrics).to_csv(cdir/'copper_model_metrics.csv',index=False)
                    metadata.update(status='ORIGIN_ONLY_FULL_COPPER_FIT',market_date=date+'T20:00:00Z',
                        input_sha256=sha256_file(rawpath),training_rows=len(surface),reserved_rows=0,
                        holdout_scope='Temporal validation reported separately; no same-date reserved strikes in these origin fits')
                    metadata['files']={f.name:sha256_file(f) for f in cdir.iterdir() if f.is_file() and f.name!='run_manifest.json'}
                    (cdir/'run_manifest.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
            coverage.append(row);processed.add(date);progress=True
            admitted=sorted(surfaces)
            if len(admitted)>=2:
                origin,target=admitted[-2:];pair=(origin,target)
                if pair not in scored:
                    rows,residuals=score(origin,target,surfaces[origin],surfaces[target],params[origin])
                    metric_rows.extend(rows);scored.add(pair)
                    residuals.to_csv(local/f'{origin}_to_{target}_forecasts.csv',index=False)
                    print(f'[OOS] {origin} -> {target}: {rows[0]["common_n"]} common contracts',flush=True)
            print(f'[DATE] {date}: {len(raw)} raw, {row["eligible_quotes"]} eligible, admitted={row["dense_admitted"]}',flush=True)
            save_progress('RUNNING')
        panel_mp=args.panel_dir/'panel_manifest.json'
        panel_finished=panel_mp.exists() and json.loads(panel_mp.read_text()).get('status')=='COMPLETE'
        if len(processed)==len(calendar) or panel_finished or not args.watch:break
        if not progress:time.sleep(5)
    status='COMPLETE' if len(scored)>=1 and len(processed)==len(calendar) else 'INSUFFICIENT_OR_INCOMPLETE_TEMPORAL_PANEL'
    save_progress(status)
    if metric_rows:
        metrics=pd.DataFrame(metric_rows);summary=summarize(metrics)
        fig,ax=plt.subplots(figsize=(10,5))
        for model,g in metrics.groupby('model',sort=False):
            g=g.sort_values('target_date');delta=g.mean_benchmark_mse_iv-g.mse_iv
            ax.plot(pd.to_datetime(g.target_date),np.cumsum(delta),label=model)
        ax.axhline(0,color='black',linewidth=.8);ax.legend(fontsize=8)
        ax.set_ylabel('Cumulative date-equal MSE improvement vs origin mean IV')
        ax.set_title('Copper: conditional rolling next-date surface validation')
        fig.autofmt_xdate();fig.tight_layout();fig.savefig(args.output_dir/'cumulative_oos.png',dpi=180);plt.close(fig)
        print(summary.to_string(index=False),flush=True)
        save_progress(status)
    else:print('[NO OOS] No chronological pair of admitted dense copper surfaces',flush=True)


if __name__=='__main__':main()
