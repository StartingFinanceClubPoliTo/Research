# Barrick Paper reproducibility 🔬

Audited operating-proxy sensitivity experiment supporting the September 7, 2026 Barrick Paper. Outputs are aggregate USD-billion proxies, not equity values, physical probabilities or market mispricing estimates.

## 👥 Authors
Research Teams 1–8, Starting Finance Club PoliTo. The full named author list is in the accompanying paper. Team 8 option models: Salvatore Gabriele Messina and Alessandro Coco.

## 🗂️ Structure
- `pricing/`: corrected Team 8 calibration and pricing modules.
- `src/`: operating-proxy and gold-path integration.
- `team8_data/data/processed/`: curated source data, with provenance in `DATA_MANIFEST.json`.
- `audit_inputs/`: frozen September 2 calibration and original rolling OOS inputs.
- `data/processed/team8/`: original and separately audited parameters.
- `audit_outputs/`: numerical audit tables, figures and samples.
- `tests/`: regression tests for candidate preservation and nested boundaries.

## ▶️ Run
From this directory, use Python 3.11 or later:

```sh
python -m pip install -r requirements.txt
python main.py
python -m pytest tests -q
```

`python main.py --recalibrate` also repeats the Hawkes local refinement. The default replays its saved audited candidate. Refinements are deterministic local improvements, not proofs of global minima. Input hashes are verified before every run.

## 📊 Interpretation
The current-snapshot refit and the historical OOS experiment are distinct. Historical OOS results retain the original origin parameters: changing the final-date fit does not retroactively validate a new calibration protocol. `oos_audit.csv` gives exact supports, denominators and two different RMSE aggregations. The bootstrap is exploratory with 30 dates.

The reported signed terminal preserves negative operating outcomes. `legacy_positive` is retained only to replay and quantify the earlier floor. `none` truncates at five years and is not a reserve-life estimate. Q-law plus assumed WACC remains a sensitivity operator; no accounting reconciliation or Q-to-P transformation is claimed. Calendar entries are frozen scenario inputs, not forecasts commencing at the option snapshot.

The option inputs were collected through the IB API; Treasury histories are separately identified. No account configuration, keys, private runtime files or environments are distributed. The user-provided curated dataset is copied without rewriting source observations.

## 📚 Audit
See `technical_audit.pdf`, `audit_outputs/review_status.json`, parameter JSON files and the tabular numerical outputs. New historical recalibration and an independently reconciled corporate valuation remain separate research tasks.

## Copper extension - October 3, 2026

The original operating perimeter omitted copper. Lumwana (100%), Zaldivar (50%) and Jabal Sayid (50%) now enter through already-attributable Q2 sales and unit Cost of Sales. Ownership is not applied a second time. Volumes and costs are frozen for twenty quarters; expansion and reserve life are not forecast.

- Ten preselected historical IB API dates, 112 spaced contract locations per date, 912 returned quote rows. Seven dates pass common quality gates, producing six temporal origin-target pairs.
- Rolling conditional IV repricing uses 480 common forecasts and 375 persistence-supported targets. Mean daily IV RMSE is 106.48 / 71.46 / 70.49 / 67.65 bp for Black-76 / Heston / Bates / Hawkes. None beats persistence.
- Fixed-July-9-origin comparisons give positive persistence R-squared for Bates and Hawkes (0.193 and 0.182), on different support. Six target dates do not establish a winner.
- Primary paired five-year means, without terminal value, add USD 2.618-2.666 bn under independent commodity paths. This increment is not added to signed-terminal gold medians. It is a methodological operating proxy, not corporate FCFF or equity value.
- [Copper technical audit](code/copper_technical_audit.pdf) records coverage, units, scope and results. The September 7 gold technical audit remains dated evidence.

```sh
python main.py --copper --output-dir outputs/copper-replay-new
```

This standalone replay uses derived copper parameters and delivery-curve aggregates with the audited Paper gold configuration. It checks frozen evidence hashes and requires a new output directory. Licensed raw copper quotes remain local. Acquisition and temporal-calibration code is available in the companion [UNIFICATO code](../Barrick%20Mining%20UNIFICATO/code).


## Probability-measure contract - October 5, 2026

Option calibration remains under Q with deterministic rates. The operating experiment uses an artificial scenario law R: transferred coefficients, imposed commodity mean schedules and independent WACC shocks. No Q-to-P density, physical risk premia or pricing kernel is estimated. A fixed-delivery future has zero drift in the pricing convention; the cross-delivery copper curve is a scenario mean schedule, not that futures drift. WACC is not the short rate. Combining Q-shaped scenarios and assumed WACC is a sensitivity operator, not corporate pricing. Replacing WACC with a risk-free rate alone would not reconcile corporate cash flows.

`--valuation-law` supports only `conditional_option_implied_shape`; physical and corporate risk-neutral interpretations are rejected. The manifest records the measure boundary. Tests check jump compensation and zero fixed-future drift for all four engines. The October 5 Paper replay reproduces the October 3 numerical aggregates exactly. Copper mine volumes/CoS remain controlled fixed scenarios; they are not the gold mine-level SARIMA forecasts.

## Active project graph

[Graph report](../../Barrick%20Mining%20UNIFICATO/graphify-out/GRAPH_REPORT.md) covers active integration and accepted measure/Paper evidence. HTML and JSON are alongside the report; archive/build duplicates and licensed quote rows are excluded.
