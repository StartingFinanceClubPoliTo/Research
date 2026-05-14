# Gold, Monetary Regimes, and Volatility Dynamics

From the Gold Standard to Econometric Analysis and Stochastic Volatility Foundations for Heston-Type Models.

## Authors
- Davide D'Amico
- Pietro Weisz

## Overview

This folder contains the research code, datasets, and reproducibility materials for the article *Gold, Monetary Regimes, and Volatility Dynamics: From the Gold Standard to Econometric Analysis and Stochastic Volatility Foundations for Heston-Type Models*.

The project combines historical and econometric analysis of gold dynamics, with empirical sections on returns, volatility, correlations, regression models, and stylized facts.

## Repository structure

- `src/` – Python scripts for the reproducible analysis pipeline  
- `data/raw/` – original downloaded or source data (not manually modified)  
- `data/processed/` – cleaned and transformed datasets used in the analysis  
- `output/figures/` – figures generated for the paper  
  - `output/figures/ch6/` – figures for Chapter 6 (regressions and correlations)  
  - `output/figures/ch7/` – figures for Chapter 7 (stylized facts and volatility)  
- `output/tables/` – tables exported for the manuscript (e.g. LaTeX, CSV)  
- `notebooks/` – (optional, to be added later) exploratory notebooks and working analysis

## Execution order

The main analysis can be reproduced by running the scripts in the following order:

1. `src/01_data_download.py`  
   Download raw price and yield data (e.g. from Yahoo Finance) and save to `data/raw/`.

2. `src/02_data_preparation.py`  
   Build cleaned and aligned datasets (levels and returns) and save to `data/processed/`.

3. `src/03_descriptive_stats.py`  
   Compute descriptive statistics and correlation matrices; export tables to `output/tables/`.

4. `src/04_chapter6_regressions.py`  
   Run the regression models for Chapter 6 and export coefficient tables and related figures.

5. `src/05_chapter7_stylized_facts.py`  
   Generate figures and tables for the stylized facts and volatility analysis in Chapter 7.

## Notes

- Raw data in `data/raw/` should never be edited by hand.  
- Processed datasets in `data/processed/` are derived from raw inputs via the scripts in `src/`.  
- Exploratory notebooks (once added) will live in `notebooks/` and are not the primary source of the reproducible pipeline.