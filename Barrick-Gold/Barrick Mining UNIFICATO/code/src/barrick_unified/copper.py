"""Copper-specific quote audit and attributable operating margin.

HXE is American. A constant-volatility futures tree is used to estimate an
equivalent European quote before the existing European stochastic engines are
fitted. This is a model-dependent approximation, not exact de-Americanization.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from .ib_gold_surface import black76_price, build_observed_surface, SurfaceFilterConfig

LB_PER_TONNE = 2204.6226218488


def american_futures_price(forward, strike, maturity, rate, sigma, right, steps=300):
    """CRR futures tree: risk-neutral forward drift is zero, premium discounted."""
    if right not in {'C', 'P'}:
        raise ValueError('right must be C or P')
    if min(forward, strike, maturity, sigma) <= 0 or steps < 2:
        raise ValueError('positive tree inputs required')
    dt = maturity / steps
    u = math.exp(sigma * math.sqrt(dt))
    d = 1 / u
    p = (1 - d) / (u - d)
    discount = math.exp(-rate * dt)
    nodes = forward * np.exp((2 * np.arange(steps + 1) - steps) * math.log(u))
    sign = 1 if right == 'C' else -1
    value = np.maximum(sign * (nodes - strike), 0)
    for n in range(steps - 1, -1, -1):
        nodes = nodes[:-1] * u
        continuation = discount * (p * value[1:] + (1 - p) * value[:-1])
        value = np.maximum(continuation, sign * (nodes - strike))
    return float(value[0])


def copper_surface(quotes, max_age=120., max_spread=.20, rate_curve=None, rate_metadata=None):
    if 'quote_unit' not in quotes or not quotes.quote_unit.eq('USD/lb').all():
        raise ValueError('copper quotes must explicitly use USD/lb')
    if 'trading_class' not in quotes or not quotes.trading_class.eq('HXE').all():
        raise ValueError('expected standard COMEX HXE copper options')
    if 'underlying_verified' not in quotes or not quotes.underlying_verified.eq(True).all():
        raise ValueError('every copper option must have a verified matching future')
    audit, metadata = build_observed_surface(quotes, SurfaceFilterConfig(
        max_quote_age_seconds=max_age, max_relative_spread=max_spread), rate_curve, rate_metadata)
    # Matching futures must pass the same staleness gate as the option itself.
    eligible = audit.exclusion_reason.eq('eligible')
    audit.loc[eligible & (audit.future_quote_age_seconds > max_age), 'exclusion_reason'] = 'stale_forward'
    for col in ['bid', 'ask', 'mid']:
        audit['raw_' + col] = audit[col]
    audit['american_iv'] = np.nan
    audit['american_adjustment_usd_per_lb'] = np.nan
    audit['tree_300_600_iv_difference'] = np.nan
    for idx, row in audit[audit.exclusion_reason.eq('eligible')].iterrows():
        f, k, t, r, right = row.future_mid, row.strike, row.maturity_years_act36525, row.rate, row.right
        try:
            def invert(price, steps):
                return brentq(lambda sigma: american_futures_price(f, k, t, r, sigma, right, steps) - price,
                              .005, 2., xtol=1e-9)
            iv = invert(row['mid'], 600)
            iv300 = invert(row['mid'], 300)
            for col in ['bid', 'ask', 'mid']:
                sigma = iv if col == 'mid' else invert(row[col], 600)
                audit.at[idx, col] = black76_price(f, k, t, r, sigma, right)
            audit.at[idx, 'american_iv'] = iv
            audit.at[idx, 'implied_vol'] = iv
            audit.at[idx, 'tree_300_600_iv_difference'] = abs(iv - iv300)
            audit.at[idx, 'american_adjustment_usd_per_lb'] = row['mid'] - audit.at[idx, 'mid']
        except ValueError:
            audit.at[idx, 'exclusion_reason'] = 'american_tree_inversion_failed'
    kept = audit[audit.exclusion_reason.eq('eligible')]
    metadata['exclusion_counts'] = audit.exclusion_reason.value_counts().to_dict()
    metadata['eligible_rows'] = len(kept)
    metadata['american_approximation'] = {
        'method': '600-step constant-volatility CRR futures IV, then equivalent Black-76 European bid/ask/mid',
        'exact_for_stochastic_volatility_and_jumps': False,
        'max_abs_adjustment_usd_per_lb': float(kept.american_adjustment_usd_per_lb.abs().max()),
        'max_300_600_iv_difference_bp': float(kept.tree_300_600_iv_difference.max() * 1e4),
        'note': 'Tree discretization comparison; not an error bound on stochastic-model early exercise.'}
    return audit, metadata


def attributable_copper_margin(prices_usd_per_lb, sales_kt, cost_usd_per_lb):
    """Mine-quarter CoS margin, USD million; volumes ALREADY attributable.

    sales_kt and costs have shape (mines, quarters); prices shape (paths, quarters).
    Ownership is deliberately not multiplied again. CoS includes depreciation;
    this margin is not EBITDA or reconciled FCFF.
    """
    prices = np.asarray(prices_usd_per_lb, dtype=float)
    sales, costs = np.asarray(sales_kt, dtype=float), np.asarray(cost_usd_per_lb, dtype=float)
    if prices.ndim != 2 or sales.ndim != 2 or costs.shape != sales.shape or sales.shape[1] != prices.shape[1]:
        raise ValueError('expected aligned path-quarter and mine-quarter arrays')
    if not all(np.isfinite(x).all() for x in (prices, sales, costs)):
        raise ValueError('finite copper operating inputs required')
    if (prices <= 0).any() or (sales < 0).any() or (costs < 0).any():
        raise ValueError('positive prices and nonnegative sales/costs required')
    by_mine = (prices[:, None, :] - costs[None, :, :]) * sales[None, :, :] * LB_PER_TONNE / 1000.
    return by_mine.sum(axis=1), by_mine
