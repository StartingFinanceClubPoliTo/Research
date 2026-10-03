"""Approval-locked manual USD rate inputs for the 2 September 2026 run."""

from __future__ import annotations

import numpy as np
import pandas as pd


MANUAL_CURVE_DATE = "2026-09-02"
MANUAL_YIELD_MATURITIES = np.array(
    [
        1 / 12,
        1.5 / 12,
        2 / 12,
        3 / 12,
        4 / 12,
        6 / 12,
        1,
        2,
        3,
        5,
        7,
        10,
        20,
        30,
    ],
    dtype=float,
)
MANUAL_YIELDS = np.array(
    [
        3.83,
        3.87,
        3.89,
        3.92,
        4.02,
        4.00,
        4.16,
        4.39,
        4.45,
        4.54,
        4.66,
        4.79,
        5.27,
        5.27,
    ],
    dtype=float,
) / 100.0


def manual_curve_frame() -> pd.DataFrame:
    """Return a fresh frame so callers cannot mutate the locked constants."""

    return pd.DataFrame(
        {
            "maturity_years": MANUAL_YIELD_MATURITIES.copy(),
            "par_yield_decimal": MANUAL_YIELDS.copy(),
            "curve_date": MANUAL_CURVE_DATE,
            "source": "manual_user_supplied",
        }
    )
