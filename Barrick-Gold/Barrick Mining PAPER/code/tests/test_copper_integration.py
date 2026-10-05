"""Financial units, American exercise, and additive valuation regression."""
from dataclasses import replace
import json
from pathlib import Path
import numpy as np
import pytest
from barrick_unified.copper import american_futures_price, attributable_copper_margin, LB_PER_TONNE
from barrick_unified.ib_gold_surface import black76_price
from barrick_unified.valuation import ValuationInputs, simulate_valuation_from_gold_paths, ValuationInputError


def test_tonne_conversion_and_no_double_ownership():
    total, mines = attributable_copper_margin(np.array([[5.]]), [[1.], [2.]], [[3.], [4.]])
    np.testing.assert_allclose(mines, [[[2 * LB_PER_TONNE / 1000], [2 * LB_PER_TONNE / 1000]]])
    np.testing.assert_allclose(total, [[4 * LB_PER_TONNE / 1000]])


@pytest.mark.parametrize('right', ['C', 'P'])
def test_zero_rate_american_matches_european_futures_option(right):
    tree = american_futures_price(6., 6.1, 1., 0., .3, right, 1600)
    european = black76_price(6., 6.1, 1., 0., .3, right)
    assert abs(tree - european) < .002
    early = american_futures_price(6., 6.1, 1., .05, .3, right, 1600)
    assert early >= black76_price(6., 6.1, 1., .05, .3, right) - .002


def test_zero_copper_preserves_baseline_and_discounting():
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / 'config/provisional_valuation_20260902_team8_refresh.json').read_text())
    inputs = replace(ValuationInputs.from_dict(config), n_simulations=100)
    gold = np.full((100, inputs.n_quarters), 4417.)
    shocks = np.zeros((100, inputs.n_years))
    baseline = simulate_valuation_from_gold_paths(inputs, gold, shocks, 'none')
    zero = simulate_valuation_from_gold_paths(inputs, gold, shocks, 'none', np.zeros_like(gold))
    np.testing.assert_array_equal(zero.enterprise_value_proxy_usd_mn, baseline.enterprise_value_proxy_usd_mn)
    added = simulate_valuation_from_gold_paths(inputs, gold, shocks, 'none', np.ones_like(gold))
    np.testing.assert_array_equal(added.annual_wacc, baseline.annual_wacc)
    np.testing.assert_allclose(added.annual_component_margin_usd_mn - baseline.annual_component_margin_usd_mn, 4.)
    assert (added.enterprise_value_proxy_usd_mn > baseline.enterprise_value_proxy_usd_mn).all()
    with pytest.raises(ValuationInputError):
        simulate_valuation_from_gold_paths(inputs, gold, shocks, 'none', np.zeros((100, 19)))
