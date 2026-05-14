# Component-Driven EBITDA Forecast for Barrick Gold

**Authors:** [Giacomo Scali](https://www.linkedin.com/in/giacomo-scali-abp01/), [Jacopo Foralosso](https://www.linkedin.com/in/jacopo-foralosso-6753a2256)  
**Reviewer:** [Salvatore Messina](https://www.linkedin.com/in/salvatore-messinaa) 
**Published:** May 8, 2026

This folder contains the code supporting the article *"A Component-Driven Methodology for EBITDA Forecasting in Gold Mining"*, which decomposes Barrick Gold's five-year EBITDA forecast into its three operational drivers: Cost of Sales, physical production, and gold price.

## Structure

- **`cost_of_sales`** — Log-Space ARIMA Master Chain of the cost-of-sales forecasting methodology (Chapter 2 of the paper).
- **`production`** — Bottom-up SARIMA forecast of Ore Processed and Average Grade, stochastic simulation of Recovery Rate, and aggregation via Goodman's exact variance-of-products formula (Chapter 3).
- **`ebitda_montecarlo`** — Black–Scholes inversion of GLD option prices and per-maturity constant-volatility calibration σ*(τ) and 10,000-path GBM Monte Carlo of the gold price combined with the deterministic CoS and Production forecasts to produce the final EBITDA distribution (Chapter 4).

## Requirements

Python ≥ 3.10 with the following packages:
numpy
pandas
scipy
matplotlib
seaborn
plotly
pmdarima
nelson_siegel_svensson
ib_insync

Install with:
```bash
pip install numpy pandas scipy matplotlib seaborn plotly pmdarima nelson_siegel_svensson ib_insync
```

## Data

The operational data used in this analysis (ore processed, average grade, recovery rate, gold production, cost of sales) were extracted from Barrick Gold Corporation's quarterly reports, publicly available at:

https://www.barrick.com/English/investors/

The Excel file used during development (`Quarterly Data.xlsx`) is **not included** in this repository, as it contains private working notes. To reproduce the analysis:

1. Download the relevant quarterly reports from Barrick's investor website.
2. Compile the data into an Excel file with the structure expected by `production/Production_forecast.ipynb` (one sheet per mine, plus a `Dati_P` aggregate sheet).

Option chain data for GLD (used in `gold_price_iv/`) were retrieved via the Interactive Brokers API on 2 April 2026 and are not redistributed here. The notebook contains the full pipeline to regenerate them, requiring an active IB Gateway / TWS connection on `127.0.0.1:7497`.
