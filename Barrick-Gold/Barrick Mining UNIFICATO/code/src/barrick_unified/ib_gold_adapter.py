"""IB API adapter for historical COMEX gold futures-option snapshots.

The adapter deliberately stops at an audited bid/ask dataset.  Surface fitting,
implied-volatility inversion, model calibration, and figure generation are
separate approval-gated stages.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import asyncio
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd

from .team8_rate_curve import (
    MANUAL_CURVE_DATE,
    MANUAL_YIELD_MATURITIES,
    MANUAL_YIELDS,
    manual_curve_frame,
)


def parse_utc_timestamp(value: str) -> datetime:
    """Parse an ISO timestamp and require an explicit timezone."""

    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("snapshot timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def select_standard_monthly_chains(
    futures_and_chains: Iterable[tuple[Any, Sequence[Any]]],
    snapshot: datetime,
    max_maturities: int = 12,
) -> list[tuple[Any, Any, str]]:
    """Select distinct standard COMEX ``OG`` expiries after ``snapshot``."""

    snapshot_date = snapshot.date().strftime("%Y%m%d")
    candidates: list[tuple[str, str, Any, Any]] = []
    for future, chains in futures_and_chains:
        for chain in chains:
            if str(getattr(chain, "exchange", "")) != "COMEX":
                continue
            if str(getattr(chain, "tradingClass", "")) != "OG":
                continue
            for expiry in getattr(chain, "expirations", ()):
                expiry_text = str(expiry)
                if expiry_text > snapshot_date:
                    candidates.append(
                        (expiry_text, str(getattr(future, "lastTradeDateOrContractMonth", "")), future, chain)
                    )
    selected: list[tuple[Any, Any, str]] = []
    seen: set[str] = set()
    for expiry, _, future, chain in sorted(candidates, key=lambda row: (row[0], row[1])):
        if expiry in seen:
            continue
        seen.add(expiry)
        selected.append((future, chain, expiry))
        if len(selected) >= int(max_maturities):
            break
    return selected


def select_strikes(
    strikes: Iterable[float],
    forward: float,
    log_moneyness_limit: float = 0.20,
    max_strikes: int = 25,
) -> list[float]:
    """Choose an evenly spread, exchange-listed strike set around the forward."""

    values = sorted(
        {
            float(strike)
            for strike in strikes
            if math.isfinite(float(strike))
            and float(strike) > 0.0
            and abs(math.log(float(strike) / float(forward))) <= float(log_moneyness_limit)
        }
    )
    if len(values) <= int(max_strikes):
        return values
    indices = np.linspace(0, len(values) - 1, int(max_strikes)).round().astype(int)
    return [values[index] for index in sorted(set(indices.tolist()))]


def last_valid_bid_ask(ticks: Sequence[Any], snapshot: datetime) -> dict[str, Any] | None:
    """Return the last positive bid/ask observation not later than ``snapshot``."""

    snapshot_utc = snapshot.astimezone(timezone.utc)
    valid: list[tuple[datetime, Any]] = []
    for tick in ticks:
        timestamp = getattr(tick, "time", None)
        bid = float(getattr(tick, "priceBid", math.nan))
        ask = float(getattr(tick, "priceAsk", math.nan))
        if timestamp is None or timestamp.tzinfo is None:
            continue
        timestamp = timestamp.astimezone(timezone.utc)
        if timestamp <= snapshot_utc and bid > 0.0 and ask >= bid:
            valid.append((timestamp, tick))
    if not valid:
        return None
    timestamp, tick = max(valid, key=lambda row: row[0])
    bid = float(tick.priceBid)
    ask = float(tick.priceAsk)
    return {
        "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z"),
        "bid": bid,
        "ask": ask,
        "mid": 0.5 * (bid + ask),
        "bid_size": float(getattr(tick, "sizeBid", math.nan)),
        "ask_size": float(getattr(tick, "sizeAsk", math.nan)),
        "age_seconds": (snapshot_utc - timestamp).total_seconds(),
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


@dataclass(frozen=True)
class IBGoldSnapshotConfig:
    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 92
    snapshot_utc: str = "2026-09-02T20:00:00Z"
    max_maturities: int = 9
    max_strikes: int = 25
    log_moneyness_limit: float = 0.20
    rights: tuple[str, ...] = ("C", "P")
    use_rth: bool = True


class IBGoldFuturesOptionProvider:
    """Read-only historical collector for standard COMEX Gold options."""

    def __init__(self, config: IBGoldSnapshotConfig, ib: Any | None = None) -> None:
        self.config = config
        self._ib = ib

    @property
    def snapshot(self) -> datetime:
        return parse_utc_timestamp(self.config.snapshot_utc)

    def _connect(self) -> tuple[Any, bool]:
        if self._ib is not None:
            return self._ib, False
        from ib_insync import IB

        ib = IB()
        ib.connect(
            self.config.host,
            int(self.config.port),
            clientId=int(self.config.client_id),
            readonly=True,
            timeout=15,
        )
        if not ib.isConnected():
            raise RuntimeError("IB API connection failed")
        return ib, True

    @staticmethod
    def _historical_bid_ask(ib: Any, contract: Any, snapshot: datetime) -> list[Any]:
        return ib.reqHistoricalTicks(
            contract,
            startDateTime="",
            endDateTime=snapshot,
            numberOfTicks=1,
            whatToShow="BID_ASK",
            useRth=True,
            ignoreSize=False,
        )

    @staticmethod
    def _historical_bid_ask_batch(
        ib: Any,
        contracts: Sequence[Any],
        snapshot: datetime,
        batch_size: int = 20,
    ) -> dict[int, list[Any]]:
        """Request independent contracts concurrently in pacing-safe chunks."""

        results: dict[int, list[Any]] = {}
        for start in range(0, len(contracts), int(batch_size)):
            chunk = list(contracts[start : start + int(batch_size)])
            responses = ib.run(
                asyncio.gather(
                    *[
                        ib.reqHistoricalTicksAsync(
                            contract,
                            startDateTime="",
                            endDateTime=snapshot,
                            numberOfTicks=1,
                            whatToShow="BID_ASK",
                            useRth=True,
                            ignoreSize=False,
                        )
                        for contract in chunk
                    ]
                )
            )
            results.update(
                {
                    int(contract.conId): list(ticks)
                    for contract, ticks in zip(chunk, responses, strict=True)
                }
            )
        return results

    def collect(self) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
        from ib_insync import Future, FuturesOption

        ib, owns_connection = self._connect()
        errors: list[dict[str, Any]] = []

        def record_error(req_id: int, code: int, message: str, contract: Any) -> None:
            if int(code) in {2104, 2106, 2158}:
                return
            errors.append(
                {
                    "req_id": int(req_id),
                    "code": int(code),
                    "message": str(message),
                    "contract": str(getattr(contract, "localSymbol", "")),
                }
            )

        ib.errorEvent += record_error
        try:
            details = ib.reqContractDetails(Future("GC", "", "COMEX", currency="USD"))
            futures = sorted(
                (
                    detail.contract
                    for detail in details
                    if str(detail.contract.lastTradeDateOrContractMonth)[:8]
                    > self.snapshot.strftime("%Y%m%d")
                ),
                key=lambda contract: str(contract.lastTradeDateOrContractMonth),
            )
            futures_and_chains = [
                (
                    future,
                    ib.reqSecDefOptParams(
                        future.symbol, "COMEX", future.secType, future.conId
                    ),
                )
                for future in futures
            ]
            selected = select_standard_monthly_chains(
                futures_and_chains, self.snapshot, self.config.max_maturities
            )
            if not selected:
                raise RuntimeError("No standard COMEX Gold option maturities were found")

            quote_rows: list[dict[str, Any]] = []
            audit_rows: list[dict[str, Any]] = []
            for maturity_index, (future, chain, option_expiry) in enumerate(selected, start=1):
                future_ticks = self._historical_bid_ask(ib, future, self.snapshot)
                future_quote = last_valid_bid_ask(future_ticks, self.snapshot)
                if future_quote is None:
                    audit_rows.append(
                        {
                            "future": future.localSymbol,
                            "option_expiry": option_expiry,
                            "status": "missing_future_bid_ask",
                        }
                    )
                    continue
                strikes = select_strikes(
                    chain.strikes,
                    future_quote["mid"],
                    self.config.log_moneyness_limit,
                    self.config.max_strikes,
                )
                requested = [
                    FuturesOption(
                        "GC",
                        option_expiry,
                        strike,
                        right,
                        "COMEX",
                        multiplier=str(chain.multiplier),
                        currency="USD",
                        tradingClass=str(chain.tradingClass),
                    )
                    for right in self.config.rights
                    for strike in strikes
                ]
                qualified = ib.qualifyContracts(*requested)
                qualified_keys = {
                    (str(contract.right), float(contract.strike)): contract
                    for contract in qualified
                }
                ticks_by_con_id = self._historical_bid_ask_batch(
                    ib, qualified, self.snapshot
                )
                for requested_contract in requested:
                    key = (str(requested_contract.right), float(requested_contract.strike))
                    contract = qualified_keys.get(key)
                    if contract is None:
                        audit_rows.append(
                            {
                                "future": future.localSymbol,
                                "option_expiry": option_expiry,
                                "right": key[0],
                                "strike": key[1],
                                "status": "qualification_failed",
                            }
                        )
                        continue
                    ticks = ticks_by_con_id.get(int(contract.conId), [])
                    quote = last_valid_bid_ask(ticks, self.snapshot)
                    status = "ok" if quote is not None else "missing_option_bid_ask"
                    audit_rows.append(
                        {
                            "future": future.localSymbol,
                            "future_con_id": int(future.conId),
                            "option_expiry": option_expiry,
                            "option_local_symbol": contract.localSymbol,
                            "option_con_id": int(contract.conId),
                            "right": contract.right,
                            "strike": float(contract.strike),
                            "status": status,
                        }
                    )
                    if quote is None:
                        continue
                    expiry_time = datetime.strptime(option_expiry, "%Y%m%d").replace(
                        hour=20, tzinfo=timezone.utc
                    )
                    quote_rows.append(
                        {
                            "provider": "IB API",
                            "instrument_family": "COMEX Gold futures option",
                            "snapshot_utc": self.snapshot.isoformat().replace("+00:00", "Z"),
                            "future_local_symbol": future.localSymbol,
                            "future_con_id": int(future.conId),
                            "future_expiry": str(future.lastTradeDateOrContractMonth)[:8],
                            "future_quote_timestamp_utc": future_quote["timestamp_utc"],
                            "future_bid": future_quote["bid"],
                            "future_ask": future_quote["ask"],
                            "future_mid": future_quote["mid"],
                            "future_quote_age_seconds": future_quote["age_seconds"],
                            "option_local_symbol": contract.localSymbol,
                            "option_con_id": int(contract.conId),
                            "option_expiry": option_expiry,
                            "maturity_years_act36525": (
                                expiry_time - self.snapshot
                            ).total_seconds() / (365.25 * 86400.0),
                            "trading_class": contract.tradingClass,
                            "multiplier": float(contract.multiplier),
                            "right": contract.right,
                            "strike": float(contract.strike),
                            "log_moneyness_k_over_f": math.log(
                                float(contract.strike) / future_quote["mid"]
                            ),
                            "quote_timestamp_utc": quote["timestamp_utc"],
                            "quote_age_seconds": quote["age_seconds"],
                            "bid": quote["bid"],
                            "ask": quote["ask"],
                            "mid": quote["mid"],
                            "bid_size": quote["bid_size"],
                            "ask_size": quote["ask_size"],
                            "price_method": "historical_bid_ask_midpoint",
                        }
                    )
                print(
                    f"[IB] maturity {maturity_index}/{len(selected)} "
                    f"{option_expiry} on {future.localSymbol}: "
                    f"{sum(row['option_expiry'] == option_expiry for row in quote_rows)} valid quotes",
                    flush=True,
                )

            quotes = pd.DataFrame(quote_rows)
            audit = pd.DataFrame(audit_rows)
            if quotes.empty:
                raise RuntimeError("IB returned no valid Gold futures-option bid/ask quotes")
            metadata = {
                "provider": "IB API",
                "connection": {
                    "host": self.config.host,
                    "port": int(self.config.port),
                    "client_id": int(self.config.client_id),
                    "readonly": True,
                },
                "instrument": "COMEX Gold futures options",
                "underlying_policy": "option-specific COMEX GC futures contract",
                "option_chain_policy": "standard monthly OG expiries",
                "snapshot_utc": self.snapshot.isoformat().replace("+00:00", "Z"),
                "market_date": self.snapshot.date().isoformat(),
                "use_rth": bool(self.config.use_rth),
                "max_maturities": int(self.config.max_maturities),
                "max_strikes_per_maturity": int(self.config.max_strikes),
                "log_moneyness_limit": float(self.config.log_moneyness_limit),
                "rights": list(self.config.rights),
                "valid_quotes": int(len(quotes)),
                "requested_or_audited_contracts": int(len(audit)),
                "maturities_with_quotes": int(quotes["option_expiry"].nunique()),
                "rate_curve": {
                    "source": "manual_user_supplied",
                    "curve_date": MANUAL_CURVE_DATE,
                    "maturities_years": MANUAL_YIELD_MATURITIES.tolist(),
                    "par_yields_decimal": MANUAL_YIELDS.tolist(),
                    "fit_status": "not_run_in_acquisition_stage",
                },
                "downstream_status": {
                    "surface": "not_run",
                    "implied_volatility": "not_run",
                    "model_calibration": "not_run",
                    "figures": "not_run",
                },
                "ib_errors": errors,
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
            return quotes, audit, metadata
        finally:
            try:
                ib.errorEvent -= record_error
            except Exception:
                pass
            if owns_connection:
                ib.disconnect()


def write_snapshot(
    output_dir: Path,
    quotes: pd.DataFrame,
    audit: pd.DataFrame,
    metadata: dict[str, Any],
) -> Path:
    """Write one local-only acquisition package and its file hashes."""

    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite existing raw run: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    quote_path = output_dir / "gc_futures_option_bid_ask.csv"
    audit_path = output_dir / "gc_futures_option_request_audit.csv"
    curve_path = output_dir / "manual_yield_curve_2026-09-02.csv"
    manifest_path = output_dir / "run_manifest.json"
    quotes.to_csv(quote_path, index=False)
    audit.to_csv(audit_path, index=False)
    manual_curve_frame().to_csv(curve_path, index=False)
    metadata = dict(metadata)
    metadata["files"] = {
        path.name: {"sha256": sha256_file(path), "bytes": path.stat().st_size}
        for path in (quote_path, audit_path, curve_path)
    }
    manifest_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return manifest_path
