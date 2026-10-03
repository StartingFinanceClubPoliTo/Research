"""Small serial availability check: distinguish missing/stale ticks from timeouts."""
from pathlib import Path
import argparse
import asyncio
from datetime import datetime,timezone
import json
import sys
import pandas as pd
from ib_insync import IB,Contract
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from barrick_unified.ib_gold_adapter import last_valid_bid_ask,parse_utc_timestamp,sha256_file

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--dates',default='2026-07-09,2026-08-03,2026-09-01')
    args=p.parse_args()
    rawpath=ROOT/'data/raw/ib_local/20261003-acquired-hg-20260902-spaced112/hg_futures_option_bid_ask.csv'
    raw=pd.read_csv(rawpath)
    # Fixed contracts for availability ONLY; not a retrospective calibration sample.
    g=raw[raw.option_expiry.astype(str).eq('20270126')]
    call=g[g.right.eq('C')].sort_values('strike').iloc[0]
    put=g[g.right.eq('P')].sort_values('strike').iloc[-1]
    contracts=[('matched_future',Contract(conId=int(call.future_con_id),secType='FUT',exchange='COMEX',currency='USD')),
               ('call',Contract(conId=int(call.option_con_id),secType='FOP',exchange='COMEX',currency='USD')),
               ('put',Contract(conId=int(put.option_con_id),secType='FOP',exchange='COMEX',currency='USD'))]
    results=[]
    ib=IB();ib.connect('127.0.0.1',7497,clientId=104,readonly=True,timeout=15)
    async def request(c,snapshot):
        return await asyncio.wait_for(ib.reqHistoricalTicksAsync(c,'',snapshot,1,'BID_ASK',False,False),timeout=40)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    def save():
        args.output.write_text(json.dumps({'provider':'IB API','readonly':True,'source_registry_sha256':sha256_file(rawpath),
            'scope':'Availability probes only; neither a dense panel nor OOS evidence',
            'results':results,'updated_at_utc':datetime.now(timezone.utc).isoformat()},indent=2),encoding='utf-8')
    try:
        for date in args.dates.split(','):
            snapshot=parse_utc_timestamp(date+'T20:00:00Z')
            for kind,c in contracts:
                record={'date':date,'kind':kind,'contract_id':c.conId}
                try:
                    ticks=ib.run(request(c,snapshot))
                    q=last_valid_bid_ask(ticks,snapshot)
                    record.update(status='quote_returned' if q else 'no_valid_quote',quote=q)
                    if q:
                        record['passes_120s_freshness']=q['age_seconds']<=120
                except asyncio.TimeoutError:
                    record['status']='response_timeout_not_evidence_of_absence'
                results.append(record);save()
                print('[PROBE]',json.dumps(record),flush=True)
                ib.sleep(2.1)
    finally:
        ib.disconnect()

if __name__=='__main__':main()
