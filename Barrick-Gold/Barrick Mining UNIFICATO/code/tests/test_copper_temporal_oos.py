"""Scientific invariants of conditional, chronological surface validation."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location(
    'copper_oos_test_module', Path(__file__).parents[1] / 'tools/run_copper_oos.py')
oos = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oos)


def test_persistence_interpolates_inside_hull_and_does_not_extrapolate():
    origin = pd.DataFrame({'T': [.3, .3, .8, .8],
        'K': np.exp([-.1, .1, -.1, .1]), 'implied_vol': [.2, .3, .4, .5]})
    target = pd.DataFrame({'T': [.55, .2, .55], 'K': np.exp([0., 0., .2])})
    prediction = oos.persistence(origin, target)
    assert prediction[0] == pytest.approx(.35)
    assert np.isnan(prediction[1:]).all()


def test_hawkes_projection_preserves_structural_parameters_and_origin():
    p = dict(v0=.09, kappa=2., theta=.04, xi=.1, rho=-.3,
        lambda0=.2, lambda_bar=.4, branching_ratio=.25, beta=3., mu_J=-.01, sigma_J=.05)
    before = dict(p)
    out = oos.project_model_state('hawkes', p, .1)
    assert p == before
    assert out['v0'] == pytest.approx(.04 + (.09-.04)*np.exp(-.2))
    stationary = .4/(1-.25)
    assert out['lambda0'] == pytest.approx(stationary + (.2-stationary)*np.exp(-2.25*.1))
    for key in p.keys() - {'v0', 'lambda0'}:
        assert out[key] == p[key]


def test_target_iv_only_changes_losses_and_scoring_cannot_refit(monkeypatch):
    origin = pd.DataFrame({'T': [.3, .3, .8, .8],
        'K': [.9, 1.1, .9, 1.1], 'implied_vol': [.2, .2, .2, .2]})
    target = pd.DataFrame({'T': [.5], 'K': [1.], 'implied_vol': [.21],
        'option_con_id': [123], 'option_expiry': ['20270126']})
    results = {'Black-76': {'parameters': {'sigma': .2}, 'parameter_names': ['sigma']}}
    def forbidden(*args, **kwargs):
        raise AssertionError('A target score must not fit parameters')
    monkeypatch.setattr(oos, 'fit_models', forbidden)
    monkeypatch.setattr(oos, 'price_model_calls', lambda m, values, frame, modules, n:
        np.array([oos.black76_implied_vol.__globals__['black76_price'](
            1., r.K, r.T, 0., values[0], 'C') for r in frame.itertuples()]))
    rows, forecasts = oos.score('2026-07-09', '2026-07-10', origin, target, results)
    target['implied_vol'] = .35
    changed, forecasts2 = oos.score('2026-07-09', '2026-07-10', origin, target, results)
    assert forecasts['Black-76_iv'].iloc[0] == pytest.approx(.2)
    assert forecasts2['Black-76_iv'].iloc[0] == forecasts['Black-76_iv'].iloc[0]
    assert changed[0]['mse_iv'] > rows[0]['mse_iv']
    with pytest.raises(ValueError, match='strictly follow'):
        oos.score('2026-07-10', '2026-07-09', origin, target, results)


def test_date_equal_and_pooled_oos_use_their_actual_supports():
    frame = pd.DataFrame([dict(model='Black-76', common_n=n, persistence_n=0,
        mse_iv=a, mean_benchmark_mse_iv=4., model_mse_on_persistence_support_iv=np.nan,
        persistence_mse_iv=np.nan) for n, a in [(10, 1.), (100, 9.)]])
    row = oos.summarize(frame).iloc[0]
    assert row.date_equal_oos_r2 == pytest.approx(1-10/8)
    assert row.pooled_oos_r2 == pytest.approx(1-910/440)
    assert row.mean_daily_rmse_bp == pytest.approx(20000.)
    assert row.root_mean_daily_mse_bp == pytest.approx(np.sqrt(5)*10000)
