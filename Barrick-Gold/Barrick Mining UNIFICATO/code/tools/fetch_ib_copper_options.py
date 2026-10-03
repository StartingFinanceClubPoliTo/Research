"""Acquire about 100 widely spaced copper option quotes, read-only and local-only.

Default market date matches the frozen gold experiment. Expired contracts that
IB no longer lists are not reconstructed. Each option's underlying is checked
against IB contract details before requesting its historical forward quote.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from ib_insync import IB, Future, FuturesOption

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from barrick_unified.ib_gold_adapter import last_valid_bid_ask, parse_utc_timestamp, sha256_file, select_strikes


def spaced_indices(n: int, count: int) -> list[int]:
    return sorted(set(np.linspace(0, n - 1, min(n, count)).round().astype(int).tolist())) if n else []


def collect(args):
    snapshot = parse_utc_timestamp(args.snapshot_utc)
    ib = IB()
    ib.RequestTimeout = 30
    ib.connect('127.0.0.1', args.port, clientId=args.client_id, readonly=True, timeout=15)
    errors, audits, rows = [], [], []
    def error(req, code, message, contract):
        if code not in {2104, 2106, 2158}:
            errors.append({'request': req, 'code': code, 'message': message,
                           'contract': getattr(contract, 'localSymbol', '')})
    ib.errorEvent += error
    try:
        futures = sorted([d.contract for d in ib.reqContractDetails(Future('HG', '', 'COMEX', currency='USD'))],
                         key=lambda f: f.lastTradeDateOrContractMonth)
        future_by_id = {f.conId: f for f in futures}
        candidates = {}
        for f in futures:
            days = (datetime.strptime(f.lastTradeDateOrContractMonth[:8], '%Y%m%d').replace(tzinfo=timezone.utc) - snapshot).days
            if days <= 0 or days > 800:
                continue
            for chain in ib.reqSecDefOptParams('HG', 'COMEX', 'FUT', f.conId):
                if chain.exchange != 'COMEX' or chain.tradingClass != 'HXE':
                    continue
                for expiry in sorted(chain.expirations):
                    expiry_dt = datetime.strptime(expiry, '%Y%m%d').replace(hour=20, tzinfo=timezone.utc)
                    maturity = (expiry_dt - snapshot).total_seconds() / (365.25 * 86400)
                    if 0.08 <= maturity <= args.max_dte / 365.25:
                        candidates.setdefault(expiry, (f, chain, maturity))
        expiries = sorted(candidates)
        selected = [expiries[i] for i in spaced_indices(len(expiries), args.maturities)]
        if not selected:
            raise RuntimeError('No listed HXE maturities available for this historical snapshot')
        forward_cache = {}
        def forward_quote(f):
            if f.conId not in forward_cache:
                ticks = ib.reqHistoricalTicks(f, '', snapshot, 1, 'BID_ASK', False, False)
                forward_cache[f.conId] = last_valid_bid_ask(ticks, snapshot)
            return forward_cache[f.conId]
        for expiry in selected:
            f, chain, maturity = candidates[expiry]
            fq = forward_quote(f)
            if fq is None:
                audits.append({'option_expiry': expiry, 'status': 'missing_forward'})
                continue
            strikes = select_strikes(chain.strikes, fq['mid'], args.log_moneyness_limit, args.strikes)
            requests = [FuturesOption('HG', expiry, k, 'P' if k < fq['mid'] else 'C',
                                      'COMEX', multiplier=chain.multiplier, currency='USD', tradingClass='HXE') for k in strikes]
            for start in range(0, len(requests), 6):
                chunk = requests[start:start + 6]
                details_sets = ib.run(asyncio.gather(*[ib.reqContractDetailsAsync(c) for c in chunk]))
                qualified = []
                for requested, details in zip(chunk, details_sets):
                    matches = [d for d in details if d.contract.right == requested.right and d.contract.strike == requested.strike
                               and d.contract.lastTradeDateOrContractMonth[:8] == expiry]
                    if len(matches) != 1:
                        audits.append({'option_expiry': expiry, 'strike': requested.strike, 'right': requested.right, 'status': 'ambiguous_or_missing_contract'})
                        continue
                    d = matches[0]
                    actual_f = future_by_id.get(d.underConId)
                    if actual_f is None:
                        audits.append({'option_expiry': expiry, 'strike': requested.strike, 'status': 'unknown_underlying'})
                        continue
                    actual_fq = forward_quote(actual_f)
                    if actual_fq is None:
                        continue
                    qualified.append((d.contract, actual_f, actual_fq))
                ticks_sets = ib.run(asyncio.gather(*[ib.reqHistoricalTicksAsync(c, '', snapshot, 1, 'BID_ASK', False, False)
                                                    for c, _, _ in qualified]))
                for (c, actual_f, actual_fq), ticks in zip(qualified, ticks_sets):
                    q = last_valid_bid_ask(ticks, snapshot)
                    audits.append({'option_expiry': expiry, 'strike': c.strike, 'right': c.right,
                                   'option_con_id': c.conId, 'underlying_con_id': actual_f.conId,
                                   'status': 'ok' if q else 'missing_historical_bid_ask'})
                    if q is None:
                        continue
                    rows.append({'provider': 'IB API', 'instrument_family': 'COMEX Copper futures option',
                                 'snapshot_utc': args.snapshot_utc, 'quote_unit': 'USD/lb',
                                 'future_local_symbol': actual_f.localSymbol, 'future_con_id': actual_f.conId,
                                 'future_expiry': actual_f.lastTradeDateOrContractMonth[:8],
                                 'future_quote_timestamp_utc': actual_fq['timestamp_utc'],
                                 'future_bid': actual_fq['bid'], 'future_ask': actual_fq['ask'], 'future_mid': actual_fq['mid'],
                                 'future_quote_age_seconds': actual_fq['age_seconds'],
                                 'option_local_symbol': c.localSymbol, 'option_con_id': c.conId,
                                 'option_expiry': expiry, 'maturity_years_act36525': maturity,
                                 'trading_class': c.tradingClass, 'multiplier': float(c.multiplier), 'right': c.right,
                                 'strike': c.strike, 'log_moneyness_k_over_f': math.log(c.strike / actual_fq['mid']),
                                 'quote_timestamp_utc': q['timestamp_utc'], 'quote_age_seconds': q['age_seconds'],
                                 'bid': q['bid'], 'ask': q['ask'], 'mid': q['mid'],
                                 'price_method': 'historical_bid_ask_midpoint', 'underlying_verified': True,
                                 'exercise_style': 'American'})
            print(f'[COPPER] {expiry}: {sum(r["option_expiry"] == expiry for r in rows)} quotes', flush=True)
        return pd.DataFrame(rows), pd.DataFrame(audits), {'provider': 'IB API', 'readonly': True,
            'snapshot_utc': args.snapshot_utc, 'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
            'sampling': {'method': 'uniform across listed expiries and strikes in log-moneyness band; one OTM right',
                         'target_quotes': args.maturities * args.strikes, 'maturities': selected,
                         'log_moneyness_limit': args.log_moneyness_limit, 'historically_expired_contracts_not_reconstructed': True},
            'underlying_policy': 'verified IB ContractDetails.underConId for each option',
            'exercise_style': 'American; European model approximation requires an explicit audit',
            'quote_unit': 'USD/lb', 'ib_errors': errors, 'valid_quotes': len(rows)}
    finally:
        ib.disconnect()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port', type=int, default=7497)
    p.add_argument('--client-id', type=int, default=104)
    p.add_argument('--snapshot-utc', default='2026-09-02T20:00:00Z')
    p.add_argument('--maturities', type=int, default=8)
    p.add_argument('--strikes', type=int, default=12)
    p.add_argument('--max-dte', type=int, default=730)
    p.add_argument('--log-moneyness-limit', type=float, default=0.20)
    p.add_argument('--output-dir', type=Path, required=True)
    args = p.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise FileExistsError('Refusing to overwrite an acquisition run')
    quotes, audit, metadata = collect(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in [('hg_futures_option_bid_ask.csv', quotes), ('hg_request_audit.csv', audit)]:
        frame.to_csv(args.output_dir / name, index=False)
    metadata['files'] = {name: {'sha256': sha256_file(args.output_dir / name)} for name in
                         ['hg_futures_option_bid_ask.csv', 'hg_request_audit.csv']}
    (args.output_dir / 'run_manifest.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(f'[DONE] {len(quotes)} real copper quotes; {args.output_dir}', flush=True)
    if quotes.empty:
        raise RuntimeError('No historical quotes returned; inspect saved request audit')


if __name__ == '__main__':
    main()
