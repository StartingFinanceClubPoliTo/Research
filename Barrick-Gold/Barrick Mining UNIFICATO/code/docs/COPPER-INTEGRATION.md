# Copper integration

The user also requires **historical temporal OOS tests**. The first September 2
experiment below is a static extension; reserved-strike scores do not satisfy
that requirement. The historical acquisition and temporal validation are
separate runs, with date-specific Treasury curves and origin-only refits:

```powershell
python tools/fetch_ib_copper_panel.py --quote-budget 112 --max-dte 250 --dates 2026-07-09,2026-07-10,2026-07-20,2026-07-31,2026-08-03,2026-08-12,2026-08-21,2026-08-31,2026-09-01,2026-09-02 --output-dir data/raw/ib_local/copper_rolling_20260709_20260902_budget112
python tools/run_copper_oos.py --panel-dir data/raw/ib_local/copper_rolling_20260709_20260902_budget112 --output-dir outputs/validation/copper_temporal_oos_budget112_20261003 --watch
```

The reference calendar contains the 31 July 9–September 2 observation dates of
the gold panel. The current **ten-date preliminary pilot** spans that period,
including the final three consecutive dates. It does not reproduce all 31
gold OOS dates; its next-available-date gaps and sample size differ. Dates were
chosen before temporal scoring. Omitting `--dates` requests all reference
dates; use a new acquisition/output directory for that larger experiment.
The current run distributes up to 112 spaced real OTM quote
locations evenly across each date's selected expiries with DTE 75–250.
The first fixed 8 × 14 attempt with DTE up to 300 was too sparse (51, 33 and
62 eligible quotes on July 9, 10 and 13) and is retained as an interrupted
acquisition audit. This acquisition adjustment precedes temporal model scoring.
Quotes and their matching futures must be at most 120 seconds
old, with option relative spreads at most 20%. A date requires **64 eligible
actual quotes on at least three expiries** before fitting. No interpolation
manufactures observations. This copper fit uses all eligible sampled quotes;
it is not the gold model's fixed CC64 design.

An origin is scored against the next admitted date using its structural
parameters and projected variance/intensity. Target matched futures and as-of
Treasury rates condition repricing. Targets never enter origin fitting. Mean
and inside-hull persistence benchmarks use explicit common supports; daily
and pooled loss aggregations remain separate. These are conditional IV tests,
not physical copper-price forecasts. A currently discoverable contract
catalogue also has survivorship limits: expired options are not reconstructed.

`origin_target_coverage.csv` records actual admitted dates and omissions. A
timeout is a failed retrieval, **not evidence of absent historical data**.
Only actual chronological admitted pairs may produce an OOS score. If coverage
is insufficient, retain the static valuation's qualification and report the
missing validation explicitly. The valuation runner accepts `--oos-dir` to
attach the completed aggregate evidence to a new immutable valuation run.

The frozen gold configurations contain no copper operating contribution.
This separate experiment adds Lumwana (100%), Zaldívar (50%) and Jabal Sayid
(50%) using **already attributable sold volumes** from Barrick's Q2 2026 mine
statistics. Ownership must not be applied again. One tonne is
2204.6226218488 pounds; copper option/futures prices and unit CoS are USD/lb.

Use the existing Python environment with `ib_insync`, `numpy`, `pandas`,
`scipy`, `matplotlib`, and `nelson_siegel_svensson`. Enable the TWS local
socket API. Acquisition connects with `readonly=True` and submits no orders.

```powershell
python tools/fetch_ib_copper_options.py --port 7497 --client-id 104 --maturities 8 --strikes 14 --max-dte 300 --log-moneyness-limit 0.16 --output-dir data/raw/ib_local/20261003-acquired-hg-20260902-spaced112
python tools/calibrate_ib_copper_models.py --input data/raw/ib_local/20261003-acquired-hg-20260902-spaced112/hg_futures_option_bid_ask.csv --output-dir data/processed/copper/calibration_20260902_spaced
python run_copper_valuation.py --calibration-dir data/processed/copper/calibration_20260902_spaced --output-dir outputs/valuation/20261003-gold-plus-copper-v2
```

Run directories are immutable: choose a new name when reacquiring or refitting.
The same valuation runner is available from the standard entry point:
`python main.py --copper-valuation --calibration-dir <local-calibration> --output-dir <new-run>`.
The September 2 snapshot matches the frozen gold experiment; it is **not** a
current October market valuation. Contracts that IB no longer lists are not
reconstructed. Every option's matching future is verified using `underConId`.

The acquisition target is about 100 spaced OTM quote locations rather than
thousands of contracts. Missing historical quotes and wide spreads remain in
the audit. No synthetic quotes fill the gaps. Licensed quote rows, training
data and residuals stay in ignored local directories.

HXE options are American. A 600-step constant-volatility futures CRR tree
provides equivalent European quotes for the four European pricing models.
The 300/600-step comparison measures discretization sensitivity; it does not
validate early-exercise behavior under stochastic volatility or jumps.
Reserved-strike checks evaluate interpolation, not temporal forecasting.

The operating comparison freezes each mine's Q2 attributable sales and CoS as
an explicit scenario, and adds its CoS margin before the same inherited
tax/growth/ROIC transformation. CoS includes depreciation: this is **not**
reconciled EBITDA or FCFF. Reported capital expenditure is retained as a source
fact but is not separately deducted in this margin experiment, since that
would require a different, reconciled cash-flow specification. Expansion
production/capex and Reko Diq are excluded from this initial extension.

Primary output: paired gold-only and gold+copper **five-year operating-value
proxies**, aggregate USD million, with no terminal value. Signed perpetuity
and terminal dependence assumptions ±0.5 are separate sensitivities. Prices,
WACC and terminal policy are held consistent between paired runs; quantiles
are computed after aggregating each path, never by adding quantiles.

The copper anchor follows observed matching-HG forward levels and holds the
last level flat beyond available maturity support. The primary gold/copper
dependence is independence. Dependence sensitivities use whole-path rank
permutations, preserve copper marginal paths, and are not calibrated Brownian
correlations. Neither this curve extension nor the inherited gold Q/P bridge
is a validated physical forecast. The corporate bridge, accounting, mine
life, closure, realized-price basis, growth investments and gold operating
calendar require further research before a corporate equity valuation.

Verified local results (October 3 acquisition, September 2 market snapshot):
88 real quotes over seven expiries; 76 eligible after a 20% relative-spread
filter; 62 training quotes and 14 reserved strikes. The reserved-strike IV RMSE
is 126.93 bp (Black-76), 28.39 bp (Heston), 28.56 bp (Bates), and 28.08 bp
(Hawkes). This small interpolation sample does not establish temporal model
superiority. The primary paired mean copper increment is USD 2.67–2.70 billion
under the explicit operating and price assumptions above. Source metadata,
quantiles, dependence sensitivities, mine-level scenarios and plots are in
`outputs/valuation/20261003-gold-plus-copper-v2/`.


## Copper historical extension — October 3 local acquisition

The original gold-only baseline excluded copper. The separate extension admits
Lumwana, Zaldívar and Jabal Sayid, using already attributable sold volumes.
Ten historical dates were acquired with about 100 spaced quote requests per date;
7 quality-admitted surfaces produce 6 chronological pairs (480 common
forecasts, 375 on persistence support). This is a preliminary pilot,
not the full 31-date gold calendar. All model estimates are origin-only with
dated Treasury curves and projected states; static strike holdout remains separate.
No robust model-superiority claim follows from this small sample.

Authoritative copper run: `outputs/valuation/20261003-gold-plus-copper-v3-temporal`;
rolling evidence: `outputs/validation/copper_temporal_oos_budget112_20261003`;
fixed-origin check: `outputs/validation/copper_fixed_origin_20261003`.
The paired mean copper increment is USD 2.618–2.663 billion over five years
without terminal value, conditional on fixed Q2 sales/CoS and the inherited
margin-to-value assumptions. This is an aggregate operating-value proxy;
accounting, capex, reserve life and the corporate equity bridge remain unresolved.
The source thesis now includes the supplied corporate-perimeter revision and
generated copper tables/figures. Licensed quote rows remain local.

```powershell
python tools/score_copper_fixed_origin.py --panel-dir data/raw/ib_local/copper_rolling_20260709_20260902_budget112 --rolling-dir outputs/validation/copper_temporal_oos_budget112_20261003 --output-dir <new-fixed-run>
python run_copper_valuation.py --calibration-dir data/raw/ib_local/copper_rolling_20260709_20260902_budget112/oos_local/calibrations/2026-09-02 --oos-dir outputs/validation/copper_temporal_oos_budget112_20261003 --fixed-oos-dir <new-fixed-run> --output-dir <new-value-run>
```

## Probability-measure contract - October 5, 2026

Option calibration remains under Q with deterministic rates. The operating experiment uses an artificial scenario law R: transferred coefficients, imposed commodity mean schedules and independent WACC shocks. No Q-to-P density, physical risk premia or pricing kernel is estimated. A fixed-delivery future has zero drift in the pricing convention; the cross-delivery copper curve is a scenario mean schedule, not that futures drift. WACC is not the short rate. Combining Q-shaped scenarios and assumed WACC is a sensitivity operator, not corporate pricing. Replacing WACC with a risk-free rate alone would not reconcile corporate cash flows.

`--valuation-law` supports only `conditional_option_implied_shape`; physical and corporate risk-neutral interpretations are rejected. The manifest records the measure boundary. Tests check jump compensation and zero fixed-future drift for all four engines. The October 5 Paper replay reproduces the October 3 numerical aggregates exactly. Copper mine volumes/CoS remain controlled fixed scenarios; they are not the gold mine-level SARIMA forecasts.
