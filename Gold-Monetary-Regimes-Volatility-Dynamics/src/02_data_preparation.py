import pandas as pd
import numpy as np
from pathlib import Path

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def main():
    df_def = pd.read_csv(
        PROCESSED_DIR / "asset_levels.csv",
        index_col=0,
        parse_dates=True
    )

    price_cols = ["gold", "silver", "sp500", "dxy"]

    log_returns = np.log(df_def[price_cols] / df_def[price_cols].shift(1))
    yield_change = df_def["ust10y_yield"].diff()

    returns = log_returns.copy()
    returns["ust10y_change"] = yield_change
    returns = returns.dropna()

    print("\nReturns head:")
    print(returns.head())
    print("\nReturns describe:")
    print(returns.describe())

    returns.to_csv(PROCESSED_DIR / "asset_returns.csv")

    print("\nSaved file:")
    print("-", PROCESSED_DIR / "asset_returns.csv")


if __name__ == "__main__":
    main()