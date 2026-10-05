# Graph Report - corpus  (2026-10-05)

## Corpus Check
- 93 files · ~57,951 words
- Verdict: corpus is large enough that graph structure adds value.
- Seven TeX sources were explicitly extracted semantically despite the detector's unsupported extension; all ten accepted semantic sources are represented.

## Summary
- 1057 nodes · 2568 edges · 67 communities (55 shown, 12 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 17 edges (avg confidence: 0.85)
- Token usage: unmetered by the host; zero placeholders do not mean zero cost.

## Community Hubs (Navigation)
- Operating Values and Discounting
- Paper Evidence and Interpretation
- Research Modules and Interfaces
- Paper Evidence and Interpretation
- Option Pricing and Calibration
- Copper Models and Integration
- Copper Models and Integration
- Paper Evidence and Interpretation
- Paper Evidence and Interpretation
- Research Modules and Interfaces
- Copper Models and Integration
- Research Modules and Interfaces
- Research Modules and Interfaces
- Paper Evidence and Interpretation
- Research Modules and Interfaces
- Operating Values and Discounting
- Operating Values and Discounting
- Copper Models and Integration
- Option Pricing and Calibration
- Measures and Scenario Boundaries
- Measures and Scenario Boundaries
- Research Modules and Interfaces
- Operating Values and Discounting
- Copper Models and Integration
- Paper Evidence and Interpretation
- Paper Evidence and Interpretation
- Paper Evidence and Interpretation
- Paper Evidence and Interpretation
- Copper Models and Integration
- Option Pricing and Calibration
- Option Pricing and Calibration
- Research Modules and Interfaces
- Research Modules and Interfaces
- Copper Models and Integration
- Measures and Scenario Boundaries
- Paper Evidence and Interpretation
- Option Pricing and Calibration
- Option Pricing and Calibration
- Research Modules and Interfaces
- Option Pricing and Calibration
- Paper Evidence and Interpretation
- Copper Models and Integration
- Paper Evidence and Interpretation
- Measures and Scenario Boundaries
- Copper Models and Integration
- Paper Evidence and Interpretation
- Copper Models and Integration
- Option Pricing and Calibration
- Option Pricing and Calibration
- Paper Evidence and Interpretation
- Research Modules and Interfaces
- Operating Values and Discounting
- Operating Values and Discounting
- Option Pricing and Calibration
- Option Pricing and Calibration
- Research Modules and Interfaces
- Operating Values and Discounting
- Option Pricing and Calibration
- Operating Values and Discounting
- Option Pricing and Calibration
- Copper Models and Integration
- Paper Evidence and Interpretation
- Option Pricing and Calibration
- Option Pricing and Calibration
- Option Pricing and Calibration
- Option Pricing and Calibration
- Option Pricing and Calibration

## God Nodes (most connected - your core abstractions)
1. `numpy` - 61 edges
2. `pathlib` - 37 edges
3. `dataclasses` - 28 edges
4. `pandas` - 26 edges
5. `ValuationInputs` - 21 edges
6. `main()` - 20 edges
7. `main()` - 20 edges
8. `UnitArray` - 19 edges
9. `run_multimodel_valuation()` - 18 edges
10. `argparse` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Paper paired five-year means with revised gold parameters and shared WACC` --semantically_similar_to--> `UNIFICATO paired five-year operating proxy: no terminal value`  [INFERRED] [semantically similar]
  VERSIONE PAPER/Overleaf/sections/04b_copper_extension.tex → UNIFICATO/Utilities-Progetto/COPPER-TEMPORAL-20261003.md
- `Transferred coefficients and anchors do not implement a Q-to-P change` --cites--> `Schwartz (1997): commodity-price dynamics, valuation and hedging`  [EXTRACTED]
  UNIFICATO/Utilities-Progetto/MEASURE-AUDIT-20261005.md → VERSIONE PAPER/Overleaf/sections/07_references.tex
- `main()` --calls--> `sha256_file()`  [EXTRACTED]
  VERSIONE PAPER/Github-Branch/code/run_copper_valuation.py → UNIFICATO/Github-Branch/src/barrick_unified/ib_gold_adapter.py
- `main()` --calls--> `run_multimodel_valuation()`  [EXTRACTED]
  VERSIONE PAPER/Github-Branch/code/run_copper_valuation.py → UNIFICATO/Github-Branch/src/barrick_unified/multimodel_valuation.py
- `main()` --calls--> `simulate_valuation_from_gold_paths()`  [EXTRACTED]
  VERSIONE PAPER/Github-Branch/code/run_copper_valuation.py → UNIFICATO/Github-Branch/src/barrick_unified/valuation.py

## Import Cycles
- 1-file cycle: `Utilities-Progetto/Artifacts/KnowledgeGraph-20261005/corpus/VERSIONE PAPER/Github-Branch/code/main.py -> Utilities-Progetto/Artifacts/KnowledgeGraph-20261005/corpus/VERSIONE PAPER/Github-Branch/code/main.py`
- 1-file cycle: `VERSIONE PAPER/Github-Branch/code/run_copper_valuation.py -> VERSIONE PAPER/Github-Branch/code/run_copper_valuation.py`
- 1-file cycle: `UNIFICATO/Github-Branch/src/barrick_unified/multimodel_valuation.py -> UNIFICATO/Github-Branch/src/barrick_unified/multimodel_valuation.py`
- 1-file cycle: `VERSIONE PAPER/Github-Branch/code/pricing/Bates.py -> VERSIONE PAPER/Github-Branch/code/pricing/Bates.py`
- 1-file cycle: `VERSIONE PAPER/Github-Branch/code/pricing/fourier_pricing.py -> VERSIONE PAPER/Github-Branch/code/pricing/fourier_pricing.py`
- 1-file cycle: `VERSIONE PAPER/Github-Branch/code/pricing/calibrate_one_day.py -> VERSIONE PAPER/Github-Branch/code/pricing/calibrate_one_day.py`
- 1-file cycle: `VERSIONE PAPER/Github-Branch/code/pricing/calibrate_surface.py -> VERSIONE PAPER/Github-Branch/code/pricing/calibrate_surface.py`
- 1-file cycle: `VERSIONE PAPER/Github-Branch/code/pricing/oos_validation.py -> VERSIONE PAPER/Github-Branch/code/pricing/oos_validation.py`
- 1-file cycle: `UNIFICATO/Github-Branch/tools/calibrate_ib_copper_models.py -> UNIFICATO/Github-Branch/tools/calibrate_ib_copper_models.py`
- 1-file cycle: `UNIFICATO/Github-Branch/tools/fetch_ib_copper_options.py -> UNIFICATO/Github-Branch/tools/fetch_ib_copper_options.py`
- 1-file cycle: `UNIFICATO/Github-Branch/tools/run_copper_oos.py -> UNIFICATO/Github-Branch/tools/run_copper_oos.py`
- 1-file cycle: `UNIFICATO/Github-Branch/src/barrick_unified/market_data.py -> UNIFICATO/Github-Branch/src/barrick_unified/market_data.py`
- 2-file cycle: `VERSIONE PAPER/Github-Branch/code/pricing/Bates.py -> VERSIONE PAPER/Github-Branch/code/pricing/calibration_core.py -> VERSIONE PAPER/Github-Branch/code/pricing/Bates.py`
- 2-file cycle: `VERSIONE PAPER/Github-Branch/code/pricing/Bates.py -> VERSIONE PAPER/Github-Branch/code/pricing/Heston.py -> VERSIONE PAPER/Github-Branch/code/pricing/Bates.py`
- 3-file cycle: `UNIFICATO/Github-Branch/src/barrick_unified/copper.py -> UNIFICATO/Github-Branch/src/barrick_unified/ib_gold_surface.py -> VERSIONE PAPER/Github-Branch/code/run_copper_valuation.py -> UNIFICATO/Github-Branch/src/barrick_unified/copper.py`
- 3-file cycle: `UNIFICATO/Github-Branch/src/barrick_unified/ib_gold_adapter.py -> VERSIONE PAPER/Github-Branch/code/pricing/calibrate_surface.py -> VERSIONE PAPER/Github-Branch/code/run_copper_valuation.py -> UNIFICATO/Github-Branch/src/barrick_unified/ib_gold_adapter.py`
- 3-file cycle: `UNIFICATO/Github-Branch/src/barrick_unified/multimodel_valuation.py -> VERSIONE PAPER/Github-Branch/code/pricing/calibrate_surface.py -> VERSIONE PAPER/Github-Branch/code/run_copper_valuation.py -> UNIFICATO/Github-Branch/src/barrick_unified/multimodel_valuation.py`
- 3-file cycle: `UNIFICATO/Github-Branch/src/barrick_unified/valuation.py -> VERSIONE PAPER/Github-Branch/code/pricing/calibrate_surface.py -> VERSIONE PAPER/Github-Branch/code/run_copper_valuation.py -> UNIFICATO/Github-Branch/src/barrick_unified/valuation.py`
- 3-file cycle: `VERSIONE PAPER/Github-Branch/code/pricing/Bates.py -> VERSIONE PAPER/Github-Branch/code/pricing/Heston.py -> VERSIONE PAPER/Github-Branch/code/pricing/calibration_core.py -> VERSIONE PAPER/Github-Branch/code/pricing/Bates.py`
- 4-file cycle: `UNIFICATO/Github-Branch/src/barrick_unified/copper.py -> UNIFICATO/Github-Branch/src/barrick_unified/ib_gold_surface.py -> VERSIONE PAPER/Github-Branch/code/pricing/calibrate_surface.py -> VERSIONE PAPER/Github-Branch/code/run_copper_valuation.py -> UNIFICATO/Github-Branch/src/barrick_unified/copper.py`

## Hyperedges (group relationships)
- **Pricing Q, artificial scenario R and unimplemented physical P** — unificato_utilities_progetto_measure_audit_20261005_pricing_q, unificato_utilities_progetto_measure_audit_20261005_artificial_r, unificato_utilities_progetto_measure_audit_20261005_unimplemented_p, unificato_utilities_progetto_measure_audit_20261005_measure_boundary [EXTRACTED 1.00]
- **Nested candidate commodity-price engine family** — versione_paper_overleaf_sections_03_methodology_black_scholes_gbm, versione_paper_overleaf_sections_03_methodology_heston, versione_paper_overleaf_sections_03_methodology_bates_poisson, versione_paper_overleaf_sections_03_methodology_bates_hawkes [EXTRACTED 1.00]
- **Three-mine attributable copper perimeter** — versione_paper_overleaf_sections_04b_copper_extension_copper_mine_perimeter, unificato_github_branch_docs_copper_integration_lumwana, unificato_github_branch_docs_copper_integration_zaldivar, unificato_github_branch_docs_copper_integration_jabal_sayid, unificato_github_branch_docs_copper_integration_attributable_sales [EXTRACTED 1.00]

## Communities (67 total, 12 thin omitted)

### Community 0 - "Operating Values and Discounting"
Cohesion: 0.14
Nodes (32): scipy, _array_hash(), _bh_distribution_figure(), _comparison_figure(), _input_entry(), _latex_quantile_table(), multimodel_quantile_rows(), multimodel_summary_rows() (+24 more)

### Community 1 - "Paper Evidence and Interpretation"
Cohesion: 0.14
Nodes (43): matplotlib_dates, re, sampling, all_calibrations_successful(), build_origin_calibration_set(), build_summary(), calibration_dir(), calibration_successful() (+35 more)

### Community 2 - "Research Modules and Interfaces"
Cohesion: 0.09
Nodes (39): collections_abc, Series, Provenance-safe market analytics for the Barrick unified research project., BarSchemaError, canonicalise_lse_candles(), compute_market_summary(), log_returns(), Any (+31 more)

### Community 3 - "Paper Evidence and Interpretation"
Cohesion: 0.15
Nodes (42): scipy_interpolate, scipy_spatial, all_calibrations_successful(), build_origin_calibration_set(), build_summary(), calibration_dir(), calibration_successful(), create_coverage_rows() (+34 more)

### Community 4 - "Option Pricing and Calibration"
Cohesion: 0.10
Nodes (23): ABC, GoldPathResult, GoldPriceModel, GoldSimulationContext, ndarray, Common gold-engine contract., A model whose only output is a conditional gold-price layer., FullBatesHawkesGoldModel (+15 more)

### Community 5 - "Copper Models and Integration"
Cohesion: 0.09
Nodes (27): IBGoldFuturesOptionProvider, IBGoldSnapshotConfig, last_valid_bid_ask(), parse_utc_timestamp(), Any, DataFrame, datetime, Path (+19 more)

### Community 6 - "Copper Models and Integration"
Cohesion: 0.13
Nodes (37): add_parameter_diagnostics(), calibrate_bates_forward(), calibrate_black76(), calibrate_hawkes_forward(), calibrate_heston_forward(), deterministic_strike_holdout(), _feller_population(), load_team8_modules() (+29 more)

### Community 7 - "Paper Evidence and Interpretation"
Cohesion: 0.15
Nodes (33): bates_seed_from_payload(), bs_objective(), calibrate_bs(), calibration_frame(), file_sha256(), find_previous_hawkes_result(), hawkes_payload(), hawkes_seed_from_payload() (+25 more)

### Community 8 - "Paper Evidence and Interpretation"
Cohesion: 0.15
Nodes (33): bates_seed_from_payload(), bs_objective(), calibrate_bs(), calibration_frame(), file_sha256(), find_previous_hawkes_result(), hawkes_payload(), hawkes_seed_from_payload() (+25 more)

### Community 9 - "Research Modules and Interfaces"
Cohesion: 0.09
Nodes (19): CostForecast, CostModel, FrozenTeam4CostModel, ndarray, Protocol, Cost models are independent of every gold-price engine., Compatibility adapter for the accepted 20 Team 4 output values., Team 4 production/cost adapters and operating identities. (+11 more)

### Community 10 - "Copper Models and Integration"
Cohesion: 0.12
Nodes (25): american_futures_price(), copper_surface(), invert(), Copper-specific quote audit and attributable operating margin. HXE is American.…, CRR futures tree: risk-neutral forward drift is zero, premium discounted., black76_normalized_vega(), build_observed_surface(), chebyshev_targets() (+17 more)

### Community 11 - "Research Modules and Interfaces"
Cohesion: 0.22
Nodes (27): _acf(), _fit_garch(), objective(), _fractional_difference(), _garch_filter(), generate_empirical_figures(), _gph_d(), load_current_panel() (+19 more)

### Community 12 - "Research Modules and Interfaces"
Cohesion: 0.19
Nodes (21): platform, _correlated_normals(), _inputs(), ndarray, Team 8 2026-09-02 path adapter for the unified Barrick experiment. The…, simulate_bates_paths(), simulate_full_hawkes_paths(), simulate_gbm_paths() (+13 more)

### Community 13 - "Paper Evidence and Interpretation"
Cohesion: 0.13
Nodes (16): ArgumentParser, csv, hashlib, importlib, os, subprocess, sys, typing (+8 more)

### Community 14 - "Research Modules and Interfaces"
Cohesion: 0.13
Nodes (9): ProjectLayout, Any, Path, Run the offline suite without leaving Python or pytest caches., Dispatch to a named, existing runner without duplicating its logic., Canonical, named paths used by people and automation., Small application facade for status checks and existing runners., Return a deterministic, read-only handoff summary. (+1 more)

### Community 15 - "Operating Values and Discounting"
Cohesion: 0.18
Nodes (13): BarrickScenarioEngine, Composition root for one gold model and common Team 4/5 layers., DCFProjection, Team 5 FCFF and terminal-value identities., Team5DCFValuator, EquityBridge, Explicit Team 5 enterprise-to-equity bridge., Team 5 valuation components used by the refactored pipeline. (+5 more)

### Community 16 - "Operating Values and Discounting"
Cohesion: 0.20
Nodes (19): types, _array_hash(), _canonical_hash(), common_input_fingerprints(), GoldModelRun, load_multimodel_inputs(), Any, ndarray (+11 more)

### Community 17 - "Copper Models and Integration"
Cohesion: 0.19
Nodes (15): asyncio, datetime, ib_insync, json, logging, math, pandas, IB API adapter for historical COMEX gold futures-option snapshots. The adapter… (+7 more)

### Community 18 - "Option Pricing and Calibration"
Cohesion: 0.14
Nodes (12): dataclasses, Enum, str, Validated domain contracts shared by the refactored layers., ConditionalBridgePolicy, Any, Fail-closed interpretation contracts., ArtifactRecord (+4 more)

### Community 19 - "Measures and Scenario Boundaries"
Cohesion: 0.12
Nodes (18): ModuleType, couple_by_terminal_scores(), main(), Sensitivity copula via whole-path permutation; preserves copper marginals. rho…, simulate_copper(), attributable_copper_margin(), Mine-quarter CoS margin, USD million; volumes ALREADY attributable. sales_kt…, measure_contract() (+10 more)

### Community 20 - "Measures and Scenario Boundaries"
Cohesion: 0.14
Nodes (8): importlib_util, pytest, parametrize, Financial units, American exercise, and additive valuation regression., test_zero_rate_american_matches_european_futures_option(), Scientific invariants of conditional, chronological surface validation., test_target_iv_only_changes_losses_and_scoring_cannot_refit(), Measure-boundary rejection and fixed-future drift/compensator checks.

### Community 21 - "Research Modules and Interfaces"
Cohesion: 0.19
Nodes (10): find_local_lse_key(), LSEMarketDataProvider, Any, Path, Atomically write licensed row-level data below a Git-ignored path., Find the process/user-scoped key without exposing it., Narrow provider owned by the project, backed by the official SDK., Fetch catalog-validated Barrick equities and the GLD option underlying.… (+2 more)

### Community 22 - "Operating Values and Discounting"
Cohesion: 0.28
Nodes (14): probability_value_exceeds_market(), quantile_rows(), Return the publication table at the canonical percentile levels., _distribution_figure(), _latex_quantile_table(), Any, ndarray, Path (+6 more)

### Community 23 - "Copper Models and Integration"
Cohesion: 0.28
Nodes (12): Already attributable sold copper volumes, Copper extension of an originally gold-only operating perimeter, Ten-date preliminary copper pilot spanning July 9–September 2, 2026, Jabal Sayid: 50% Barrick interest, Licensed quote rows remain in ignored local directories, Lumwana: 100% Barrick interest, Historical admission: 64 eligible actual quotes and at least three expiries, Read-only IB API acquisition without order submission (+4 more)

### Community 24 - "Paper Evidence and Interpretation"
Cohesion: 0.17
Nodes (5): CalibrationReport, MaturitySlice, OptionSurface, Shared contracts for option-surface calibration in the clean Team 8 build., Validated numeric view of a calibration DataFrame grouped by (T, rate).

### Community 25 - "Paper Evidence and Interpretation"
Cohesion: 0.27
Nodes (7): ExactHawkesCalibration, clip_full_seed(), conditional_objective(), local_minimize(), retain_candidates(), Calibrate the exact Heston-Hawkes model. When ``hawkes_seed`` is supplied, it…, Calibration API for the exact affine Heston-Hawkes pricer.

### Community 26 - "Paper Evidence and Interpretation"
Cohesion: 0.17
Nodes (5): CalibrationReport, MaturitySlice, OptionSurface, Shared contracts for option-surface calibration in the clean Team 8 build., Validated numeric view of a calibration DataFrame grouped by (T, rate).

### Community 27 - "Paper Evidence and Interpretation"
Cohesion: 0.27
Nodes (7): ExactHawkesCalibration, clip_full_seed(), conditional_objective(), local_minimize(), retain_candidates(), Calibrate the exact Heston-Hawkes model. When ``hawkes_seed`` is supplied, it…, Calibration API for the exact affine Heston-Hawkes pricer.

### Community 28 - "Copper Models and Integration"
Cohesion: 0.26
Nodes (9): argparse, bates, hawkes, heston, oos_validation, pathlib, Audit copper quotes, reserve strikes, and fit four conditional option models., Chronological copper refits and next-available-date conditional IV scoring.… (+1 more)

### Community 31 - "Research Modules and Interfaces"
Cohesion: 0.20
Nodes (3): ndarray, QuarterGrid, Validated mapping from a fine simulation grid to operating quarters.

### Community 32 - "Research Modules and Interfaces"
Cohesion: 0.20
Nodes (4): MarginProjection, ndarray, OperatingProjection, ndarray

### Community 33 - "Copper Models and Integration"
Cohesion: 0.24
Nodes (8): _float_array(), Any, datetime, ValueError, Raised when the provisional valuation contract is not explicit., _utc(), ValuationInputError, test_zero_copper_preserves_baseline_and_discounting()

### Community 34 - "Measures and Scenario Boundaries"
Cohesion: 0.42
Nodes (10): Artificial operating-scenario law R, Cross-delivery F(0,T) curve imposes scenario means, not fixed-future time drift, Zero drift of a fixed-delivery future under the deterministic-rate pricing convention, GLD shape reanchored to realised gold USD/oz without estimated carry or GLD/oz conversion, Jump compensator uses simulated intensity and exponential mark moment, Transferred coefficients and anchors do not implement a Q-to-P change, Executable measure-law rejection and four-engine drift/compensation checks, Option calibration under pricing measure Q (+2 more)

### Community 35 - "Paper Evidence and Interpretation"
Cohesion: 0.25
Nodes (10): Bates compensated compound-Poisson jumps, Black–Scholes/GBM constant-volatility gold benchmark, Common 8,192-path WACC array across model comparisons, Heston stochastic variance, Team 4 cost log master chain: ARIMA(3,1,0) with drift, Team 4 production: SARIMA ore, AR(1) grade and uniform bounded recovery, Team 5 after-tax component-margin mapping with growth/ROIC reinvestment, Signed perpetuity and five-year no-terminal closures are separate sensitivities (+2 more)

### Community 36 - "Option Pricing and Calibration"
Cohesion: 0.29
Nodes (6): scipy_integrate, time, Bates option pricing and reproducible surface calibration., Exact event-dependent Bates-Hawkes option-pricing engine. The jump intensity is…, Reusable Fourier inversion kernels for Heston, Bates and Bates-Hawkes., Heston pricing and self-contained surface calibration for the clean build.

### Community 37 - "Option Pricing and Calibration"
Cohesion: 0.20
Nodes (4): Bates, Heston, feller_feasible_population(), Build a Differential Evolution population satisfying Heston Feller.

### Community 38 - "Research Modules and Interfaces"
Cohesion: 0.24
Nodes (5): array_sha256(), ndarray, Scenario orchestration and reproducible random streams., RandomStreams, Independent, auditable random streams.

### Community 39 - "Option Pricing and Calibration"
Cohesion: 0.20
Nodes (4): Bates, Heston, feller_feasible_population(), Build a Differential Evolution population satisfying Heston Feller.

### Community 40 - "Paper Evidence and Interpretation"
Cohesion: 0.27
Nodes (7): Eight research teams connect theory, econometrics, simulation, operations and discounted margins, Operating-Value Sensitivity for Barrick Mining: controlled gold and copper experiment, Corporate FCFF, cash/debt and diluted-share bridge remains unreconciled, A positive WACC–growth spread does not justify perpetual mine production, Gold historical OOS uses original fits, separate from audited current calibration, Reproducibility, numerical accuracy and economic validity are distinct, Commodity basis, measure, operations, accounting and resource closure require economic validation

### Community 41 - "Copper Models and Integration"
Cohesion: 0.22
Nodes (9): Affine Bates–Hawkes with exponential self-exciting intensity, Lumwana consolidated; Zaldívar and Jabal Sayid equity-accounted, Risk-neutral Hawkes self-excitation does not establish physical or causal news clustering, Barrick Annual Report 2025: ownership, reporting and joint arrangements, Barrick Q2 2026 mine statistics: copper table page 8, Fang and Oosterlee (2008): Fourier-COS option pricing, Hawkes (1971): self-exciting point processes, Barrick Mining research repository, revised October 5, 2026 (+1 more)

### Community 42 - "Paper Evidence and Interpretation"
Cohesion: 0.36
Nodes (8): bns, bs_objective(), calibrate_bs(), hawkes_payload(), main(), Calibrate BS, Heston, Bates and Full Bates-Hawkes on one daily GLD surface.…, report_payload(), settings()

### Community 43 - "Measures and Scenario Boundaries"
Cohesion: 0.31
Nodes (6): matplotlib, matplotlib_pyplot, scipy_stats, Paired gold-only vs gold+copper conditional operating-value experiment. Run…, Option pricing Q and artificial operating-scenario R are distinct laws., Paired gold-only vs gold+copper conditional operating-value experiment. Run…

### Community 44 - "Copper Models and Integration"
Cohesion: 0.39
Nodes (5): numpy, Bates option pricing and reproducible surface calibration., Exact event-dependent Bates-Hawkes option-pricing engine. The jump intensity is…, Reusable Fourier inversion kernels for Heston, Bates and Bates-Hawkes., Heston pricing and self-contained surface calibration for the clean build.

### Community 45 - "Paper Evidence and Interpretation"
Cohesion: 0.36
Nodes (8): surface_builder, bs_objective(), calibrate_bs(), hawkes_payload(), main(), Calibrate BS, Heston, Bates and Full Bates-Hawkes on one daily GLD surface.…, report_payload(), settings()

### Community 46 - "Copper Models and Integration"
Cohesion: 0.39
Nodes (8): Every HXE option matched to its HG underlying using underConId, Monte Carlo standard errors measure mean simulation noise only, UNIFICATO paired five-year operating proxy: no terminal value, 600-step constant-volatility American-to-European HXE approximation, Independent commodity paths primary; whole-path rank permutations are dependence sensitivities, Copper margin: kt sales and USD/lb converted to USD millions using 2204.6226218488 lb/t, Q2 copper sales and CoS fixed for 20 quarters, not mine-level production forecasts, Paper paired five-year means with revised gold parameters and shared WACC

### Community 47 - "Option Pricing and Calibration"
Cohesion: 0.25
Nodes (3): phi(), adaptive_cos_call_prices(), cos_call_prices_from_values()

### Community 48 - "Option Pricing and Calibration"
Cohesion: 0.25
Nodes (3): phi(), adaptive_cos_call_prices(), cos_call_prices_from_values()

### Community 49 - "Paper Evidence and Interpretation"
Cohesion: 0.36
Nodes (8): Partners' interests must not be deducted again from already attributable flows, CoS includes depreciation and royalties: component margin is not EBITDA or reconciled EBIT, Same-date NSS Treasury par-yield proxy, not a bootstrapped zero curve, GLD non-distributing call exercise convention checked with an 800-step CRR tree, September 2 GLD calibration: 64 actual structured contracts, Eight-mine attributable gold operating subset, Company Q1–Q2 gold actuals followed by eight-mine forecasts; past actuals retained, Svensson (1994): yield-curve interpretation

### Community 50 - "Research Modules and Interfaces"
Cohesion: 0.36
Nodes (3): Any, Accumulate and atomically serialize one public run manifest., RunManifestBuilder

### Community 52 - "Operating Values and Discounting"
Cohesion: 0.32
Nodes (7): ndarray, Run one vectorized, deterministic-seed provisional valuation., Value Barrick from external quarterly gold paths. ``gold_price_usd_per_oz``…, simulate_valuation(), simulate_valuation_from_gold_paths(), _trend(), ValuationResult

### Community 53 - "Option Pricing and Calibration"
Cohesion: 0.29
Nodes (3): scipy_optimize, Hawkes, Hawkes utilities and exact Heston-Hawkes option-surface calibration. Cleaned…

### Community 55 - "Research Modules and Interfaces"
Cohesion: 0.38
Nodes (4): Application services for versioned Barrick experiments., Class-based compatibility pipeline for CODE-012. The legacy module is used only…, RefactoredBarrickPipeline, Class-based, parity-preserving Barrick valuation pipeline. The package is…

### Community 56 - "Operating Values and Discounting"
Cohesion: 0.29
Nodes (3): UnitArray, EquityProjection, ndarray

### Community 58 - "Operating Values and Discounting"
Cohesion: 0.53
Nodes (5): Namespace, main(), parse_args(), CLI for the conditional four-model Barrick valuation experiment., run()

### Community 60 - "Copper Models and Integration"
Cohesion: 0.73
Nodes (5): Copper fixed-origin OOS: July 9 origin on the same six target dates, 480 common model forecasts; rolling persistence 375 and fixed-origin persistence 333, Rolling IV persistence remains unbeaten by all four models, Copper rolling OOS: six chronological admitted origin–target pairs, Origin-only parameters and projected states; target futures/rates condition IV repricing

## Knowledge Gaps
- **6 isolated node(s):** `Black–Scholes/GBM constant-volatility gold benchmark`, `Barrick Mining research repository, revised October 5, 2026`, `importlib`, `logging`, `oos_validation` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 312 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ValuationInputs` connect `Operating Values and Discounting` to `Copper Models and Integration`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **Why does `run_multimodel_valuation()` connect `Operating Values and Discounting` to `Operating Values and Discounting`, `Copper Models and Integration`, `Measures and Scenario Boundaries`, `Operating Values and Discounting`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Why does `simulate_valuation_from_gold_paths()` connect `Operating Values and Discounting` to `Copper Models and Integration`, `Operating Values and Discounting`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **What connects `Black–Scholes/GBM constant-volatility gold benchmark`, `Barrick Mining research repository, revised October 5, 2026`, `importlib` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Operating Values and Discounting` be split into smaller, more focused modules?**
  _Cohesion score 0.1404040404040404 - nodes in this community are weakly interconnected._
- **Should `Paper Evidence and Interpretation` be split into smaller, more focused modules?**
  _Cohesion score 0.1427061310782241 - nodes in this community are weakly interconnected._
- **Should `Research Modules and Interfaces` be split into smaller, more focused modules?**
  _Cohesion score 0.09302325581395349 - nodes in this community are weakly interconnected._
## Scope and audit notes

This graph indexes the active gold/copper integration, audited pricing source and accepted Paper/measure evidence. It is not a scan of licensed quote rows, archive copies or every historical team artifact. Ten semantic sources include seven explicitly admitted TeX documents unsupported by auto detection. Repeated AST endpoint relations are grouped with original relationship records retained in `extraction.json`; the graph preserves their combined relation labels and multiplicity. No estimated Q-to-P bridge or corporate value is inferred. Token counts are unavailable from the host tool; zero means unmetered, not free.
