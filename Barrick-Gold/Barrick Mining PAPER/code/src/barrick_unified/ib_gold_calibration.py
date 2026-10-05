"""Forward-normalized calibration for the IB COMEX Gold option snapshot."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import sys
from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution, minimize, minimize_scalar
from scipy.stats import jarque_bera, kurtosis, skew

from .ib_gold_surface import black76_implied_vol, black76_price


SEED = 20260902


@dataclass(frozen=True)
class Team8Modules:
    Bates: Any
    OptionSurface: Any
    ExactHawkesCalibration: Any


def load_team8_modules(source_dir: Path) -> Team8Modules:
    """Load the hash-auditable Team 8 engines without copying their formulas."""

    resolved = str(source_dir.resolve())
    if resolved not in sys.path:
        sys.path.insert(0, resolved)
    from Bates import Bates
    from calibration_core import OptionSurface
    from Hawkes import ExactHawkesCalibration

    return Team8Modules(Bates, OptionSurface, ExactHawkesCalibration)


def static_arbitrage_audit(surface: pd.DataFrame, grid_points: int = 101) -> dict[str, Any]:
    """Audit strike monotonicity/convexity and calendar total variance."""

    monotonicity_violations = 0
    convexity_violations = 0
    maturity_groups: list[pd.DataFrame] = []
    by_expiry: list[dict[str, Any]] = []
    for expiry, group in surface.groupby("option_expiry", sort=True):
        group = group.sort_values("K")
        strikes = group["K"].to_numpy(dtype=float)
        prices = group["price"].to_numpy(dtype=float)
        price_steps = np.diff(prices)
        slopes = price_steps / np.diff(strikes)
        monotonic = int(np.sum(price_steps > 1e-10))
        convex = int(np.sum(np.diff(slopes) < -1e-8))
        monotonicity_violations += monotonic
        convexity_violations += convex
        maturity_groups.append(group)
        by_expiry.append(
            {
                "option_expiry": str(expiry),
                "rows": int(len(group)),
                "monotonicity_violations": monotonic,
                "convexity_violations": convex,
            }
        )

    lower = max(float(group["K"].min()) for group in maturity_groups)
    upper = min(float(group["K"].max()) for group in maturity_groups)
    grid = np.linspace(lower, upper, int(grid_points))
    total_variance = np.asarray(
        [
            float(group["T"].iloc[0])
            * np.interp(grid, group["K"], group["implied_vol"]) ** 2
            for group in maturity_groups
        ]
    )
    calendar_steps = np.diff(total_variance, axis=0)
    calendar_violations = int(np.sum(calendar_steps < -1e-8))
    return {
        "strike_monotonicity_violations": monotonicity_violations,
        "strike_convexity_violations": convexity_violations,
        "calendar_total_variance_violations": calendar_violations,
        "calendar_grid_comparisons": int(calendar_steps.size),
        "minimum_calendar_total_variance_increment": float(calendar_steps.min()),
        "common_moneyness_domain": [lower, upper],
        "by_expiry": by_expiry,
        "passed": not (
            monotonicity_violations or convexity_violations or calendar_violations
        ),
    }


def deterministic_strike_holdout(
    surface: pd.DataFrame, every: int = 5, offset: int = 2
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reserve regularly spaced strikes inside every expiry for interpolation tests."""

    holdout_indices: list[int] = []
    for _, group in surface.groupby("option_expiry", sort=True):
        ordered = group.sort_values("K")
        holdout_indices.extend(ordered.index[offset::every].tolist())
    holdout = surface.loc[holdout_indices].sort_values(["T", "K"]).reset_index(drop=True)
    train = surface.drop(index=holdout_indices).sort_values(["T", "K"]).reset_index(drop=True)
    return train, holdout


def _feller_population(bounds: tuple[tuple[float, float], ...], popsize: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    bounds_array = np.asarray(bounds, dtype=float)
    size = max(5, int(popsize) * len(bounds))
    population = rng.uniform(bounds_array[:, 0], bounds_array[:, 1], (size, len(bounds)))
    for row in population:
        ceiling = 0.995 * math.sqrt(max(2.0 * row[1] * row[2], 1e-12))
        row[3] = rng.uniform(bounds_array[3, 0], min(bounds_array[3, 1], ceiling))
    return population


def price_model_calls(
    model: str,
    parameters: Any,
    surface: pd.DataFrame,
    modules: Team8Modules,
    cos_terms: int = 256,
) -> np.ndarray:
    """Price normalized unit-forward calls, preserving input row order."""

    result = np.empty(len(surface), dtype=float)
    for _, group in surface.groupby("T", sort=False):
        positions = surface.index.get_indexer(group.index)
        strikes = group["K"].to_numpy(dtype=float)
        maturity = float(group["T"].iloc[0])
        if model == "Black-76":
            values = np.asarray(
                [
                    black76_price(1.0, strike, maturity, 0.0, float(parameters[0]), "C")
                    for strike in strikes
                ]
            )
        elif model == "Heston-forward":
            v0, kappa, theta, xi, rho = parameters
            values = modules.Bates.bates_prices_cos(
                1.0, strikes, maturity, v0, kappa, theta, xi, rho,
                0.0, 0.0, 0.10, 0.0, 0.0, N=cos_terms,
            )
        elif model == "Bates-Poisson-forward":
            values = modules.Bates.bates_prices_cos(
                1.0, strikes, maturity, *parameters, 0.0, 0.0, N=cos_terms
            )
        elif model == "Full-Bates-Hawkes-forward":
            p = (
                modules.ExactHawkesCalibration.unpack_heston_params(parameters)
                if not isinstance(parameters, dict)
                else parameters
            )
            pricer = modules.ExactHawkesCalibration._pricer()
            values = pricer.hawkes_price_cos(
                1.0,
                strikes,
                maturity,
                p["v0"], p["kappa"], p["theta"], p["xi"], p["rho"],
                p["lambda0"], p["lambda_bar"], p["alpha"], p["beta"],
                p["mu_J"], p["sigma_J"], 0.0, 0.0, N=cos_terms,
            )
        else:
            raise ValueError(f"Unknown model: {model}")
        result[positions] = values
    return result


def _weighted_objective(
    model: str,
    parameters: np.ndarray,
    surface: pd.DataFrame,
    modules: Team8Modules,
    cos_terms: int,
) -> float:
    try:
        prices = price_model_calls(model, parameters, surface, modules, cos_terms)
    except (FloatingPointError, OverflowError, ValueError):
        return 1e8
    if not np.isfinite(prices).all():
        return 1e8
    residual = (prices - surface["price"].to_numpy(dtype=float)) / np.maximum(
        surface["vega"].to_numpy(dtype=float), 1e-4
    )
    return float(np.mean(residual**2))


def calibrate_black76(surface: pd.DataFrame) -> dict[str, Any]:
    started = perf_counter()
    result = minimize_scalar(
        lambda sigma: _weighted_objective(
            "Black-76", np.asarray([sigma]), surface, None, 0
        ),
        bounds=(0.05, 0.80),
        method="bounded",
        options={"xatol": 1e-12},
    )
    return {
        "model": "Black-76",
        "parameter_names": ["sigma"],
        "values": [float(result.x)],
        "objective": float(result.fun),
        "success": bool(result.success),
        "message": str(result.message),
        "evaluations": int(result.nfev),
        "iterations": int(result.nit),
        "elapsed_seconds": perf_counter() - started,
    }


def calibrate_heston_forward(
    surface: pd.DataFrame,
    modules: Team8Modules,
    maxiter: int,
    popsize: int,
    seed: int,
) -> dict[str, Any]:
    started = perf_counter()
    bounds = (
        (0.005, 0.25), (0.10, 10.0), (0.005, 0.25),
        (0.01, 2.0), (-0.95, 0.95),
    )
    objective = lambda values, terms: _weighted_objective(  # noqa: E731
        "Heston-forward", values, surface, modules, terms
    )
    global_result = differential_evolution(
        objective,
        bounds=bounds,
        args=(128,),
        maxiter=int(maxiter),
        popsize=int(popsize),
        tol=1e-4,
        polish=False,
        seed=int(seed),
        init=_feller_population(bounds, popsize, seed),
        disp=False,
        workers=1,
    )
    constraint = {"type": "ineq", "fun": lambda x: 2.0 * x[1] * x[2] - x[3] ** 2}
    local_result = minimize(
        objective,
        global_result.x,
        args=(256,),
        method="SLSQP",
        bounds=bounds,
        constraints=(constraint,),
        options={"ftol": 1e-10, "maxiter": 250, "disp": False},
    )
    return {
        "model": "Heston-forward",
        "parameter_names": ["v0", "kappa", "theta", "xi", "rho"],
        "values": [float(value) for value in local_result.x],
        "objective": float(local_result.fun),
        "global_objective": float(global_result.fun),
        "success": bool(local_result.success),
        "message": str(local_result.message),
        "evaluations": int(local_result.nfev),
        "iterations": int(local_result.nit),
        "elapsed_seconds": perf_counter() - started,
    }


def calibrate_bates_forward(
    surface: pd.DataFrame,
    modules: Team8Modules,
    maxiter: int,
    popsize: int,
    seed: int,
) -> dict[str, Any]:
    report = modules.Bates.calibrate_bates(
        surface,
        1.0,
        q=0.0,
        maxiter=int(maxiter),
        popsize=int(popsize),
        seed=int(seed),
        pricing="cos",
        cos_N=256,
        disp=False,
        return_report=True,
    )
    payload = report.as_dict()
    payload["model"] = "Bates-Poisson-forward"
    return payload


def calibrate_hawkes_forward(
    surface: pd.DataFrame,
    modules: Team8Modules,
    bates_values: list[float],
    maxiter: int,
    popsize: int,
    seed: int,
) -> dict[str, Any]:
    started = perf_counter()
    result = modules.ExactHawkesCalibration.calibrate_heston(
        surface,
        1.0,
        q=0.0,
        bates_seed=np.asarray(bates_values, dtype=float),
        maxiter=int(maxiter),
        popsize=int(popsize),
        seed=int(seed),
        global_cos_N=128,
        local_cos_N=192,
        min_branching=0.0,
    )
    names = [
        "v0", "kappa", "theta", "xi", "rho", "lambda0", "lambda_bar",
        "branching_ratio", "beta", "mu_J", "sigma_J",
    ]
    return {
        "model": "Full-Bates-Hawkes-forward",
        "parameter_names": names,
        "values": [float(value) for value in result.x],
        "objective": float(result.fun),
        "success": bool(result.success),
        "message": str(result.message),
        "evaluations": int(result.nfev),
        "iterations": int(result.nit),
        "elapsed_seconds": perf_counter() - started,
    }


def add_parameter_diagnostics(result: dict[str, Any]) -> dict[str, Any]:
    payload = dict(result)
    parameters = dict(zip(payload["parameter_names"], payload["values"]))
    payload["parameters"] = parameters
    if {"kappa", "theta", "xi"}.issubset(parameters):
        payload["feller_gap"] = (
            2.0 * parameters["kappa"] * parameters["theta"] - parameters["xi"] ** 2
        )
    if "branching_ratio" in parameters:
        payload["hawkes_stationary"] = 0.0 <= parameters["branching_ratio"] < 1.0
        payload["alpha"] = parameters["branching_ratio"] * parameters["beta"]
    return payload


def model_diagnostics(
    model: str,
    result: dict[str, Any],
    surface: pd.DataFrame,
    modules: Team8Modules | None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    parameters = np.asarray(result["values"], dtype=float)
    model_prices = price_model_calls(model, parameters, surface, modules, 256)
    diagnostics = surface.copy().reset_index(drop=True)
    diagnostics["model"] = model
    diagnostics["model_normalized_call_price"] = model_prices
    model_iv: list[float] = []
    for row, price in zip(diagnostics.itertuples(index=False), model_prices, strict=True):
        try:
            model_iv.append(black76_implied_vol(price, 1.0, row.K, row.T, 0.0, "C"))
        except ValueError:
            model_iv.append(float("nan"))
    diagnostics["model_implied_vol"] = model_iv
    diagnostics["iv_residual"] = diagnostics["implied_vol"] - diagnostics["model_implied_vol"]
    diagnostics["model_option_price"] = (
        diagnostics["model_normalized_call_price"]
        * diagnostics["discount_factor"]
        * diagnostics["future_mid"]
    )
    put_mask = diagnostics["right"].eq("P")
    diagnostics.loc[put_mask, "model_option_price"] -= (
        diagnostics.loc[put_mask, "discount_factor"]
        * (diagnostics.loc[put_mask, "future_mid"] - diagnostics.loc[put_mask, "strike"])
    )
    diagnostics["price_residual"] = diagnostics["mid"] - diagnostics["model_option_price"]
    diagnostics["inside_bid_ask"] = diagnostics["model_option_price"].between(
        diagnostics["bid"], diagnostics["ask"], inclusive="both"
    )
    finite = diagnostics["iv_residual"].dropna().to_numpy(dtype=float)
    jb = jarque_bera(finite)
    summary = {
        "model": model,
        "observations": int(len(diagnostics)),
        "price_rmse_quote_units": float(np.sqrt(np.mean(diagnostics["price_residual"] ** 2))),
        "price_mae_quote_units": float(np.mean(np.abs(diagnostics["price_residual"]))),
        "iv_rmse_bp": float(np.sqrt(np.mean(finite**2)) * 10_000.0),
        "iv_mae_bp": float(np.mean(np.abs(finite)) * 10_000.0),
        "inside_bid_ask_pct": float(diagnostics["inside_bid_ask"].mean() * 100.0),
        "residual_skewness": float(skew(finite, bias=False)),
        "residual_excess_kurtosis": float(kurtosis(finite, fisher=True, bias=False)),
        "jarque_bera_pvalue": float(jb.pvalue),
    }
    return diagnostics, summary


def run_calibrations(
    surface: pd.DataFrame,
    team8_source: Path,
    heston_maxiter: int = 50,
    bates_maxiter: int = 60,
    hawkes_maxiter: int = 20,
    popsize: int = 8,
    seed: int = SEED,
) -> tuple[dict[str, dict[str, Any]], pd.DataFrame, pd.DataFrame]:
    """Run all four comparable full-sample calibrations and diagnostics."""

    modules = load_team8_modules(team8_source)
    print("[CAL] Black-76", flush=True)
    results: dict[str, dict[str, Any]] = {}
    results["Black-76"] = add_parameter_diagnostics(calibrate_black76(surface))
    print("[CAL] Heston-forward", flush=True)
    results["Heston-forward"] = add_parameter_diagnostics(
        calibrate_heston_forward(surface, modules, heston_maxiter, popsize, seed)
    )
    print("[CAL] Bates-Poisson-forward", flush=True)
    results["Bates-Poisson-forward"] = add_parameter_diagnostics(
        calibrate_bates_forward(surface, modules, bates_maxiter, popsize, seed + 1)
    )
    print("[CAL] Full-Bates-Hawkes-forward", flush=True)
    results["Full-Bates-Hawkes-forward"] = add_parameter_diagnostics(
        calibrate_hawkes_forward(
            surface,
            modules,
            results["Bates-Poisson-forward"]["values"],
            hawkes_maxiter,
            max(5, popsize - 2),
            seed + 2,
        )
    )

    diagnostic_frames: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []
    for model, result in results.items():
        diagnostics, metrics = model_diagnostics(
            model,
            result,
            surface,
            None if model == "Black-76" else modules,
        )
        diagnostic_frames.append(diagnostics)
        metric_rows.append(metrics)
    return results, pd.DataFrame(metric_rows), pd.concat(diagnostic_frames, ignore_index=True)
