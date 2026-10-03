"""Reconstruct a chronological copper option panel with ~100 locations per date.

Selection uses only each origin's matched forward and calendar, not September
quotes. The currently discoverable contract catalogue has survivorship limits;
unavailable expired options are not reconstructed. Each dated package resumes
independently and retains all failed requests and source hashes locally.
"""
from __future__ import annotations
import argparse
import asyncio
from datetime import datetime, timezone
import json
import logging
import math
from pathlib import Path
import sys
import pandas as pd
from ib_insync import IB, Future, FuturesOption
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tools'))
from barrick_unified.ib_gold_adapter import last_valid_bid_ask, parse_utc_timestamp, sha256_file, select_strikes
from fetch_ib_copper_options import spaced_indices


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--calendar', type=Path, default=ROOT / 'data/processed/team8/oos_20260902/run_manifest.json')
    p.add_argument('--port', type=int, default=7497)
    p.add_argument('--client-id', type=int, default=104)
    p.add_argument('--min-dte', type=int, default=75)
    p.add_argument('--max-dte', type=int, default=300)
    p.add_argument('--maturities', type=int, default=8)
    p.add_argument('--strikes', type=int, default=14)
    p.add_argument('--quote-budget', type=int, help='Distribute this many uniformly spaced locations across each date\'s selected expiries')
    p.add_argument('--log-moneyness-limit', type=float, default=.16)
    p.add_argument('--date-limit', type=int)
    p.add_argument('--dates', help='Optional comma-separated availability-check dates from the gold calendar')
    args = p.parse_args()
    dates = json.loads(args.calendar.read_text())['surface_dates']
    if args.dates:
        requested_dates = sorted(set(args.dates.split(',')))
        if not set(requested_dates).issubset(dates):
            raise ValueError('Availability dates must belong to the frozen gold calendar')
        dates = requested_dates
    if args.date_limit:
        dates = dates[:args.date_limit]
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    logging.getLogger('ib_insync.wrapper').setLevel(logging.CRITICAL)
    ib = IB()
    ib.RequestTimeout = 45
    ib.connect('127.0.0.1', args.port, clientId=args.client_id, readonly=True, timeout=15)
    errors = []
    def record_error(req, code, msg, contract):
        if code not in {2104,2106,2158}:
            errors.append({'request': req, 'code': code, 'message': msg, 'contract': getattr(contract, 'localSymbol', '')})
    ib.errorEvent += record_error
    async def safe_request(request, label):
        try:
            return await asyncio.wait_for(request, timeout=40)
        except asyncio.TimeoutError:
            errors.append({'code':'response_timeout','message':label})
            print(f'[TIMEOUT] {label}',flush=True)
            return []
    completed = {}
    source_code_sha256 = sha256_file(Path(__file__))
    def checkpoint():
        (out / 'panel_manifest.json').write_text(json.dumps({
            'status': 'COMPLETE' if len(completed) == len(dates) else 'ACQUIRING',
            'provider': 'IB API', 'readonly': True, 'port': args.port, 'client_id': args.client_id,
            'calendar_source': str(args.calendar), 'calendar_sha256': sha256_file(args.calendar),
            'planned_dates': dates, 'dates': completed, 'source_code_sha256': source_code_sha256,
            'selection': {'min_dte': args.min_dte, 'max_dte': args.max_dte, 'maturities': args.maturities,
                          'strikes_per_maturity': args.strikes, 'log_moneyness_limit': args.log_moneyness_limit,
                          'quote_budget':args.quote_budget,
                          'method': 'uniform listed expiry/strike positions chosen at each date from contemporaneous matched forward'},
            'limitations': ['Currently discoverable surviving contract catalogue; not a complete point-in-time option universe',
                            'No expired option reconstruction; missing historical bid/ask remains missing'],
            'last_checkpoint_utc': datetime.now(timezone.utc).isoformat()}, indent=2), encoding='utf-8')
    checkpoint()
    try:
        futures = sorted([d.contract for d in ib.reqContractDetails(Future('HG','','COMEX',currency='USD'))],
                         key=lambda f:f.lastTradeDateOrContractMonth)
        future_by_id = {f.conId:f for f in futures}
        catalogue = {}
        for f in futures:
            expiry_dt = pd.Timestamp(f.lastTradeDateOrContractMonth[:8])
            if expiry_dt > pd.Timestamp(dates[-1]) + pd.Timedelta(days=args.max_dte + 90):
                continue
            for chain in ib.reqSecDefOptParams('HG','COMEX','FUT',f.conId):
                if chain.exchange == 'COMEX' and chain.tradingClass == 'HXE':
                    for expiry in sorted(chain.expirations):
                        catalogue.setdefault(expiry, (f, chain))
        (out / 'discoverable_catalogue.json').write_text(json.dumps({expiry:{
            'candidate_underlying_id': f.conId, 'future': f.localSymbol,
            'strikes': sorted(chain.strikes), 'multiplier': chain.multiplier}
            for expiry,(f,chain) in catalogue.items()},indent=2),encoding='utf-8')
        contract_cache = {}
        for date in dates:
            folder = out / date
            mp = folder / 'run_manifest.json'
            if mp.exists():
                m = json.loads(mp.read_text())
                if m.get('acquisition_status') == 'COMPLETE':
                    for name, value in m['files'].items():
                        if sha256_file(folder / name) != value:
                            raise RuntimeError(f'Corrupt existing package: {folder / name}')
                    completed[date] = {'valid_quotes':m['valid_quotes'], 'maturities':m['maturities_with_quotes'],
                                       'manifest_sha256':sha256_file(mp)}
                    checkpoint()
                    print(f'[RESUME] {date}: {m["valid_quotes"]} quotes',flush=True)
                    continue
            errors_start = len(errors)
            snapshot = parse_utc_timestamp(date + 'T20:00:00Z')
            eligible_expiries = [e for e in sorted(catalogue)
                if args.min_dte <= (datetime.strptime(e,'%Y%m%d').date()-snapshot.date()).days <= args.max_dte]
            selected = [eligible_expiries[i] for i in spaced_indices(len(eligible_expiries), args.maturities)]
            strikes_per_expiry=max(1,args.quote_budget//len(selected)) if args.quote_budget and selected else args.strikes
            candidates = {f.conId:f for e in selected for f in [catalogue[e][0]]}
            print(f'[START] {date}: {len(selected)} candidate expiries',flush=True)
            forward_ticks = ib.run(asyncio.gather(*[safe_request(ib.reqHistoricalTicksAsync(f,'',snapshot,1,'BID_ASK',False,False), date+' forward '+f.localSymbol)
                                                    for f in candidates.values()]))
            forwards = {f.conId:last_valid_bid_ask(ticks,snapshot) for f,ticks in zip(candidates.values(),forward_ticks)}
            audits, rows = [], []
            requests = []
            for expiry in selected:
                f, chain = catalogue[expiry]
                fq = forwards.get(f.conId)
                if fq is None:
                    audits.append({'option_expiry':expiry,'status':'missing_forward'})
                    continue
                for k in select_strikes(chain.strikes,fq['mid'],args.log_moneyness_limit,strikes_per_expiry):
                    right = 'P' if k < fq['mid'] else 'C'
                    key = (expiry,k,right)
                    requests.append((key,FuturesOption('HG',expiry,k,right,'COMEX',multiplier=chain.multiplier,currency='USD',tradingClass='HXE')))
            uncached = [(key,c) for key,c in requests if key not in contract_cache]
            for start in range(0,len(uncached),5):
                chunk = uncached[start:start+5]
                detail_sets = ib.run(asyncio.gather(*[safe_request(ib.reqContractDetailsAsync(c), date+' qualification '+str(key)) for key,c in chunk]))
                for (key,c),details in zip(chunk,detail_sets):
                    matches = [d for d in details if d.contract.right == c.right and d.contract.strike == c.strike
                               and d.contract.lastTradeDateOrContractMonth[:8] == key[0]]
                    contract_cache[key] = (matches[0].contract,matches[0].underConId) if len(matches)==1 else None
            qualified = []
            for key,c in requests:
                item = contract_cache[key]
                if item is None:
                    audits.append({'option_expiry':key[0],'strike':key[1],'right':key[2],'status':'qualification_failed'})
                    continue
                c, under_id = item
                f = future_by_id.get(under_id)
                if f is None:
                    audits.append({'option_expiry':key[0],'strike':key[1],'status':'unknown_underlying'})
                    continue
                if under_id not in forwards:
                    ticks = ib.run(safe_request(ib.reqHistoricalTicksAsync(f,'',snapshot,1,'BID_ASK',False,False),date+' actual forward '+f.localSymbol))
                    forwards[under_id] = last_valid_bid_ask(ticks,snapshot)
                fq = forwards[under_id]
                if fq is None:
                    continue
                # Recheck OTM against the ACTUAL verified underlying.
                if c.right != ('P' if c.strike < fq['mid'] else 'C'):
                    audits.append({'option_con_id':c.conId,'status':'actual_underlying_not_otm'})
                    continue
                qualified.append((c,f,fq))
            for start in range(0,len(qualified),5):
                chunk = qualified[start:start+5]
                ticks_sets = ib.run(asyncio.gather(*[safe_request(ib.reqHistoricalTicksAsync(c,'',snapshot,1,'BID_ASK',False,False),date+' option '+c.localSymbol)
                                                    for c,_,_ in chunk]))
                for (c,f,fq),ticks in zip(chunk,ticks_sets):
                    q = last_valid_bid_ask(ticks,snapshot)
                    audits.append({'option_con_id':c.conId,'underlying_con_id':f.conId,'option_expiry':c.lastTradeDateOrContractMonth[:8],
                                   'strike':c.strike,'right':c.right,'status':'ok' if q else 'missing_bid_ask'})
                    if q is None:
                        continue
                    expiry = c.lastTradeDateOrContractMonth[:8]
                    expiry_time = datetime.strptime(expiry,'%Y%m%d').replace(hour=20,tzinfo=timezone.utc)
                    rows.append({'provider':'IB API','instrument_family':'COMEX Copper futures option',
                        'snapshot_utc':date+'T20:00:00Z','quote_unit':'USD/lb','future_local_symbol':f.localSymbol,
                        'future_con_id':f.conId,'future_expiry':f.lastTradeDateOrContractMonth[:8],
                        'future_quote_timestamp_utc':fq['timestamp_utc'],'future_bid':fq['bid'],'future_ask':fq['ask'],
                        'future_mid':fq['mid'],'future_quote_age_seconds':fq['age_seconds'],
                        'option_local_symbol':c.localSymbol,'option_con_id':c.conId,'option_expiry':expiry,
                        'maturity_years_act36525':(expiry_time-snapshot).total_seconds()/(365.25*86400),
                        'trading_class':c.tradingClass,'multiplier':float(c.multiplier),'right':c.right,'strike':c.strike,
                        'log_moneyness_k_over_f':math.log(c.strike/fq['mid']),'quote_timestamp_utc':q['timestamp_utc'],
                        'quote_age_seconds':q['age_seconds'],'bid':q['bid'],'ask':q['ask'],'mid':q['mid'],
                        'price_method':'historical_bid_ask_midpoint','underlying_verified':True,'exercise_style':'American'})
                # Preserve recoverable partial acquisition on interruption.
                folder.mkdir(parents=True,exist_ok=True)
                pd.DataFrame(rows).to_csv(folder/'partial_quotes.csv',index=False)
                pd.DataFrame(audits).to_csv(folder/'partial_audit.csv',index=False)
                ib.sleep(2.1)
            folder.mkdir(parents=True,exist_ok=True)
            quotes = pd.DataFrame(rows)
            quotes.to_csv(folder/'hg_futures_option_bid_ask.csv',index=False)
            pd.DataFrame(audits).to_csv(folder/'hg_request_audit.csv',index=False)
            m = {'acquisition_status':'COMPLETE','provider':'IB API','snapshot_utc':date+'T20:00:00Z',
                 'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'valid_quotes':len(quotes),
                 'maturities_with_quotes':int(quotes.option_expiry.nunique()) if len(quotes) else 0,
                 'selected_expiries':selected,'quote_selection':'origin contemporaneous forward only',
                 'strikes_per_expiry':strikes_per_expiry,'quote_budget':args.quote_budget,
                 'catalogue_survivorship_caveat':True,'ib_errors':errors[errors_start:],
                 'response_timeout_count':sum(e.get('code')=='response_timeout' for e in errors[errors_start:]),
                 'availability_note':'Timeouts are retrieval failures, not evidence that the underlying historical data do not exist',
                 'files':{name:sha256_file(folder/name) for name in ['hg_futures_option_bid_ask.csv','hg_request_audit.csv']}}
            mp.write_text(json.dumps(m,indent=2),encoding='utf-8')
            completed[date] = {'valid_quotes':len(quotes),'maturities':m['maturities_with_quotes'],'manifest_sha256':sha256_file(mp)}
            checkpoint()
            print(f'[PANEL] {date}: {len(quotes)} quotes, {m["maturities_with_quotes"]} expiries; {len(completed)}/{len(dates)} dates',flush=True)
    finally:
        ib.disconnect()


if __name__ == '__main__':
    main()
