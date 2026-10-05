"""Observed COMEX Gold futures-option implied-volatility surface utilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm

from .team8_rate_curve import MANUAL_YIELD_MATURITIES, MANUAL_YIELDS


@dataclass(frozen=True)
class SurfaceFilterConfig:
    max_quote_age_seconds: float = 120.0
    max_relative_spread: float = 0.20
    min_implied_vol: float = 0.01
    max_implied_vol: float = 2.00
    chebyshev_maturities: int = 8
    chebyshev_moneyness: int = 8


def black76_price(
    forward: float,
    strike: float,
    maturity: float,
    rate: float,
    volatility: float,
    right: str,
) -> float:
    """Return the discounted Black-76 price in futures quote units."""

    discount = math.exp(-rate * maturity)
    if volatility <= 0.0 or maturity <= 0.0:
        intrinsic = max(forward - strike, 0.0) if right == "C" else max(strike - forward, 0.0)
        return discount * intrinsic
    root_t = math.sqrt(maturity)
    d1 = (
        math.log(forward / strike) + 0.5 * volatility * volatility * maturity
    ) / (volatility * root_t)
    d2 = d1 - volatility * root_t
    if right == "C":
        return discount * (forward * norm.cdf(d1) - strike * norm.cdf(d2))
    if right == "P":
        return discount * (strike * norm.cdf(-d2) - forward * norm.cdf(-d1))
    raise ValueError("right must be 'C' or 'P'")


def black76_implied_vol(
    price: float,
    forward: float,
    strike: float,
    maturity: float,
    rate: float,
    right: str,
    upper_volatility: float = 5.0,
) -> float:
    """Invert a valid Black-76 price with a bounded scalar root."""

    discount = math.exp(-rate * maturity)
    intrinsic = discount * (
        max(forward - strike, 0.0) if right == "C" else max(strike - forward, 0.0)
    )
    upper_price = discount * (forward if right == "C" else strike)
    tolerance = 1e-10 * max(1.0, upper_price)
    if price < intrinsic - tolerance or price >= upper_price - tolerance:
        raise ValueError("price violates Black-76 no-arbitrage bounds")
    if price <= intrinsic + tolerance:
        return 0.0

    objective = lambda sigma: black76_price(  # noqa: E731
        forward, strike, maturity, rate, sigma, right
    ) - price
    if objective(upper_volatility) < 0.0:
        raise ValueError("implied volatility exceeds the configured upper bracket")
    return float(brentq(objective, 1e-8, upper_volatility, xtol=1e-12, rtol=1e-12))


def fit_manual_nss() -> tuple[Any, dict[str, Any]]:
    """Fit the exact user-supplied rate nodes with ``calibrate_nss_ols``."""

    from nelson_siegel_svensson.calibrate import calibrate_nss_ols

    curve, status = calibrate_nss_ols(
        MANUAL_YIELD_MATURITIES.copy(), MANUAL_YIELDS.copy()
    )
    metadata = {
        "success": bool(status.success),
        "message": str(status.message),
        "objective": float(status.fun),
        "parameters": {
            "beta0": float(curve.beta0),
            "beta1": float(curve.beta1),
            "beta2": float(curve.beta2),
            "beta3": float(curve.beta3),
            "tau1": float(curve.tau1),
            "tau2": float(curve.tau2),
        },
    }
    return curve, metadata


def build_observed_surface(
    quotes: pd.DataFrame,
    config: SurfaceFilterConfig = SurfaceFilterConfig(),
    rate_curve: Any | None = None,
    rate_metadata: dict[str, Any] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Invert OTM bid/ask midpoints and return the row-level filter audit."""

    required = {
        "option_con_id", "option_expiry", "right", "strike", "future_mid",
        "maturity_years_act36525", "quote_age_seconds", "bid", "ask", "mid",
    }
    missing = sorted(required.difference(quotes.columns))
    if missing:
        raise ValueError(f"IB option data is missing columns: {missing}")

    surface = quotes.copy()
    numeric = (
        "strike", "future_mid", "maturity_years_act36525",
        "quote_age_seconds", "bid", "ask", "mid",
    )
    for column in numeric:
        surface[column] = pd.to_numeric(surface[column], errors="coerce")
    surface["moneyness_k_over_f"] = surface["strike"] / surface["future_mid"]
    surface["relative_spread"] = (surface["ask"] - surface["bid"]) / surface["mid"]
    if rate_curve is None:
        curve, nss = fit_manual_nss()
    else:
        curve, nss = rate_curve, dict(rate_metadata or {})
    surface["rate"] = np.asarray(
        curve(surface["maturity_years_act36525"].to_numpy(dtype=float)), dtype=float
    )
    surface["option_style_for_surface"] = "OTM"
    surface["exclusion_reason"] = "eligible"

    invalid_numeric = ~np.isfinite(surface[list(numeric)]).all(axis=1)
    surface.loc[invalid_numeric, "exclusion_reason"] = "invalid_numeric_input"
    active = surface["exclusion_reason"].eq("eligible")
    bad_quote = (surface["bid"] <= 0.0) | (surface["ask"] < surface["bid"])
    surface.loc[active & bad_quote, "exclusion_reason"] = "invalid_bid_ask"
    active = surface["exclusion_reason"].eq("eligible")
    stale = surface["quote_age_seconds"] > config.max_quote_age_seconds
    surface.loc[active & stale, "exclusion_reason"] = "stale_quote"
    active = surface["exclusion_reason"].eq("eligible")
    wide = surface["relative_spread"] > config.max_relative_spread
    surface.loc[active & wide, "exclusion_reason"] = "wide_relative_spread"
    active = surface["exclusion_reason"].eq("eligible")
    not_otm = ((surface["right"] == "C") & (surface["strike"] < surface["future_mid"])) | (
        (surface["right"] == "P") & (surface["strike"] >= surface["future_mid"])
    )
    surface.loc[active & not_otm, "exclusion_reason"] = "not_otm"

    surface["implied_vol"] = np.nan
    for index, row in surface.loc[surface["exclusion_reason"].eq("eligible")].iterrows():
        try:
            volatility = black76_implied_vol(
                float(row["mid"]), float(row["future_mid"]), float(row["strike"]),
                float(row["maturity_years_act36525"]), float(row["rate"]), str(row["right"]),
            )
        except ValueError:
            surface.at[index, "exclusion_reason"] = "black76_inversion_failed"
            continue
        if not (config.min_implied_vol <= volatility <= config.max_implied_vol):
            surface.at[index, "exclusion_reason"] = "implied_vol_out_of_range"
            continue
        surface.at[index, "implied_vol"] = volatility

    counts = {
        str(key): int(value)
        for key, value in surface["exclusion_reason"].value_counts().sort_index().items()
    }
    metadata = {
        "filter_config": asdict(config),
        "nss_fit": nss,
        "input_rows": int(len(surface)),
        "exclusion_counts": counts,
        "eligible_rows": int(surface["exclusion_reason"].eq("eligible").sum()),
    }
    return surface, metadata


def black76_normalized_vega(
    moneyness: float,
    maturity: float,
    volatility: float,
) -> float:
    """Vega divided by ``discount * forward`` for a Black-76 option."""

    root_t = math.sqrt(maturity)
    d1 = (-math.log(moneyness) + 0.5 * volatility**2 * maturity) / (
        volatility * root_t
    )
    return float(norm.pdf(d1) * root_t)


def normalized_call_surface(surface_audit: pd.DataFrame) -> pd.DataFrame:
    """Map OTM puts/calls on different GC futures to one forward-call surface.

    Prices and vegas are divided by ``discount * forward``. OTM puts are
    converted to call-equivalent prices by futures put-call parity. The output
    can therefore be priced with a unit forward, zero drift, and zero rate.
    """

    eligible = surface_audit.loc[
        surface_audit["exclusion_reason"].eq("eligible")
    ].copy()
    if eligible.empty:
        raise ValueError("surface audit contains no eligible rows")
    discount = np.exp(
        -eligible["rate"].to_numpy(dtype=float)
        * eligible["maturity_years_act36525"].to_numpy(dtype=float)
    )
    forward = eligible["future_mid"].to_numpy(dtype=float)
    moneyness = eligible["moneyness_k_over_f"].to_numpy(dtype=float)
    option_price = eligible["mid"].to_numpy(dtype=float)
    normalized_price = option_price / (discount * forward)
    put_mask = eligible["right"].astype(str).eq("P").to_numpy()
    normalized_price[put_mask] += 1.0 - moneyness[put_mask]
    eligible["K"] = moneyness
    eligible["T"] = eligible["maturity_years_act36525"].to_numpy(dtype=float)
    eligible["market_rate"] = eligible["rate"].to_numpy(dtype=float)
    eligible["discount_factor"] = discount
    eligible["price"] = normalized_price
    eligible["vega"] = [
        black76_normalized_vega(k, maturity, volatility)
        for k, maturity, volatility in zip(
            eligible["K"], eligible["T"], eligible["implied_vol"], strict=True
        )
    ]
    eligible["model_rate"] = 0.0
    eligible["rate"] = 0.0
    eligible["normalization"] = "call_equivalent_divided_by_discount_times_forward"
    if not np.isfinite(eligible[["K", "T", "price", "vega"]]).all(axis=None):
        raise ValueError("normalized calibration surface contains non-finite values")
    if (eligible["price"] <= 0.0).any() or (eligible["vega"] <= 0.0).any():
        raise ValueError("normalized calibration prices and vegas must be positive")
    return eligible.sort_values(["T", "K"]).reset_index(drop=True)


def chebyshev_targets(lower: float, upper: float, count: int) -> np.ndarray:
    indices = np.arange(1, int(count) + 1, dtype=float)
    nodes = np.cos((2.0 * indices - 1.0) * np.pi / (2.0 * int(count)))
    return np.sort(0.5 * (lower + upper) + 0.5 * (upper - lower) * nodes)


def select_chebyshev_nodes(
    eligible: pd.DataFrame,
    maturity_nodes: int = 8,
    moneyness_nodes: int = 8,
) -> pd.DataFrame:
    """Greedily map a Chebyshev grid to distinct observed option contracts."""

    candidates = eligible.loc[eligible["exclusion_reason"].eq("eligible")].copy()
    required_count = int(maturity_nodes) * int(moneyness_nodes)
    if len(candidates) < required_count:
        raise ValueError(f"Need {required_count} eligible contracts, found only {len(candidates)}")
    t_min = float(candidates["maturity_years_act36525"].min())
    t_max = float(candidates["maturity_years_act36525"].max())
    k_min = float(candidates["moneyness_k_over_f"].min())
    k_max = float(candidates["moneyness_k_over_f"].max())
    t_scale = max(t_max - t_min, 1e-12)
    k_scale = max(k_max - k_min, 1e-12)
    targets = [
        (t_index, k_index, target_t, target_k)
        for t_index, target_t in enumerate(chebyshev_targets(t_min, t_max, maturity_nodes), start=1)
        for k_index, target_k in enumerate(chebyshev_targets(k_min, k_max, moneyness_nodes), start=1)
    ]
    available = set(candidates.index.tolist())
    selected: list[pd.Series] = []
    for t_index, k_index, target_t, target_k in targets:
        subset = candidates.loc[list(available)]
        distance = ((subset["maturity_years_act36525"] - target_t) / t_scale) ** 2 + (
            (subset["moneyness_k_over_f"] - target_k) / k_scale
        ) ** 2
        chosen_index = distance.idxmin()
        row = candidates.loc[chosen_index].copy()
        row["chebyshev_T_index"] = t_index
        row["chebyshev_K_index"] = k_index
        row["chebyshev_target_T"] = target_t
        row["chebyshev_target_K_over_F"] = target_k
        row["chebyshev_distance_normalized"] = math.sqrt(float(distance.loc[chosen_index]))
        selected.append(row)
        available.remove(chosen_index)
    return pd.DataFrame(selected).reset_index(drop=True)
