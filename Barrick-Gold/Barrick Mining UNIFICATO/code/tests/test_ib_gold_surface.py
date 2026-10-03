from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from barrick_unified.ib_gold_surface import (
    black76_implied_vol,
    black76_price,
    black76_normalized_vega,
    chebyshev_targets,
    select_chebyshev_nodes,
)


@pytest.mark.parametrize("right", ["C", "P"])
def test_black76_inversion_recovers_volatility(right: str) -> None:
    price = black76_price(4400.0, 4500.0, 0.5, 0.04, 0.27, right)
    recovered = black76_implied_vol(price, 4400.0, 4500.0, 0.5, 0.04, right)
    assert recovered == pytest.approx(0.27, abs=1e-10)


def test_black76_rejects_price_above_bound() -> None:
    with pytest.raises(ValueError, match="no-arbitrage"):
        black76_implied_vol(5000.0, 4400.0, 4500.0, 0.5, 0.04, "C")


def test_normalized_vega_matches_scaled_black76_finite_difference() -> None:
    moneyness, maturity, volatility = 1.1, 0.4, 0.25
    epsilon = 1e-5
    numerical = (
        black76_price(1.0, moneyness, maturity, 0.0, volatility + epsilon, "C")
        - black76_price(1.0, moneyness, maturity, 0.0, volatility - epsilon, "C")
    ) / (2.0 * epsilon)
    assert black76_normalized_vega(moneyness, maturity, volatility) == pytest.approx(
        numerical, rel=1e-8
    )


def test_chebyshev_selection_uses_distinct_observed_rows() -> None:
    rows = []
    for maturity in np.linspace(0.1, 1.0, 9):
        for moneyness in np.linspace(0.82, 1.20, 10):
            rows.append(
                {
                    "option_con_id": len(rows),
                    "maturity_years_act36525": maturity,
                    "moneyness_k_over_f": moneyness,
                    "exclusion_reason": "eligible",
                }
            )
    selected = select_chebyshev_nodes(pd.DataFrame(rows), 8, 8)
    assert len(selected) == 64
    assert selected["option_con_id"].nunique() == 64
    assert set(selected["chebyshev_T_index"]) == set(range(1, 9))
    assert set(selected["chebyshev_K_index"]) == set(range(1, 9))


def test_chebyshev_targets_stay_inside_domain() -> None:
    targets = chebyshev_targets(0.1, 1.0, 8)
    assert np.all(np.diff(targets) > 0.0)
    assert targets[0] > 0.1
    assert targets[-1] < 1.0
