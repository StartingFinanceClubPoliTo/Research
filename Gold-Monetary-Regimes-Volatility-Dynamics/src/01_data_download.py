import pandas as pd
import yfinance as yf
from pathlib import Path

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

TICKERS = {
    "gold": "GLD",         # ETF proxy for gold
    "silver": "SLV",       # ETF proxy for silver
    "sp500": "^GSPC",      # S&P 500 index
    "ust10y": "^TNX",      # 10Y Treasury yield
    "dxy": "DX-Y.NYB"      # U.S. Dollar Index
}

START_DATE = "2000-01-01"
END_DATE = "2024-12-31"
FINAL_START_DATE = "2006-05-01"

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def main():
    raw = yf.download(
        list(TICKERS.values()),
        start=START_DATE,
        end=END_DATE,
        auto_adjust=False,
        progress=False
    )

    # Retry semplice per SLV se il download è fallito (tutta NaN)
    if raw["Adj Close"][TICKERS["silver"]].isna().all():
        print("\n[WARN] SLV download failed on first try. Retrying only SLV...")
        slv_raw = yf.download(
            TICKERS["silver"],
            start=START_DATE,
            end=END_DATE,
            auto_adjust=False,
            progress=False
        )
        # Se il retry va a buon fine, inseriamo SLV nelle colonne di raw
        if not slv_raw.empty:
            for price_field in slv_raw.columns:
                raw[(price_field, TICKERS["silver"])] = slv_raw[price_field]
        else:
            print("[ERROR] SLV retry also failed. Silver series will remain NaN.")

    print("Raw head:\n", raw.head())
    print("\nRaw columns:\n", raw.columns)

    adj_close = raw["Adj Close"].copy()
    close = raw["Close"].copy()

    df = pd.DataFrame(index=raw.index)
    df["gold"] = adj_close[TICKERS["gold"]]
    df["silver"] = adj_close[TICKERS["silver"]]
    df["sp500"] = adj_close[TICKERS["sp500"]]
    df["dxy"] = adj_close[TICKERS["dxy"]]
    df["ust10y_yield"] = close[TICKERS["ust10y"]]

    print("\nDataFrame unificato (con NaN):")
    print(df.head(10))
    print("\nMissing values per colonna:")
    print(df.isna().sum())

    df_full = df.dropna().copy()

    print("\nPrima data con tutti i dati disponibili:", df_full.index.min())
    print("Ultima data:", df_full.index.max())
    print("Shape prima dropna totale:", df.shape)
    print("Shape dopo dropna totale:", df_full.shape)

    df_def = df_full[FINAL_START_DATE:END_DATE].copy()

    print("\nPeriodo effettivo usato:")
    print("Start:", df_def.index.min())
    print("End:", df_def.index.max())
    print("Shape df_def:", df_def.shape)

    raw.to_csv(RAW_DIR / "yahoo_raw_download.csv")
    df.to_csv(RAW_DIR / "asset_levels_with_nans.csv")
    df_def.to_csv(PROCESSED_DIR / "asset_levels.csv")

    print("\nSaved files:")
    print("-", RAW_DIR / "yahoo_raw_download.csv")
    print("-", RAW_DIR / "asset_levels_with_nans.csv")
    print("-", PROCESSED_DIR / "asset_levels.csv")


if __name__ == "__main__":
    main()