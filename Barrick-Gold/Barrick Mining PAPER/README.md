# Barrick Mining PAPER 📄

[Operating-Value Sensitivity for Barrick Mining](paper/Articolo.pdf) is an ten-page working draft first prepared September 7 and revised October 5, 2026. It compares option-implied gold-price laws and adds a paired copper extension within an unreconciled operating-proxy experiment.

## Current evidence

- Snapshot: September 2, 2026; 64 actual GLD call contracts, with curated Team 8 option and Treasury inputs included.
- Current-snapshot IV RMSE after local refinement: Heston 49.4881 bp, Bates 49.4077 bp, Bates–Hawkes 49.3258 bp. These are local improvements, not certified global optima.
- Historical conditional next-date repricing: 30 origins, 4,667 common forecasts; Hawkes has the lowest mean daily RMSE point estimate, 65.0507 bp. Root-mean-MSE is a different metric (70.3008 bp). No model beats persistence on its common support.
- Signed aggregate operating-proxy medians are approximately USD 59–60 billion. Numerical changes with path count, time resolution and seed exceed some inter-model differences. No equity values or market-relative verdicts are reported.

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

## Files and execution

- [paper/Articolo.pdf](paper/Articolo.pdf): ten-page Paper including the cover; LaTeX source and figures in the same directory.
- [code/README.md](code/README.md): standalone offline experiment, data provenance, parameters, tests and output tables.
- [Technical audit](code/technical_audit.pdf): all 27 review points, exact OOS denominators, parameter table and remaining limitations.
- [Full thesis draft](../Barrick%20Mining%20UNIFICATO/thesis/Articolo.pdf): broader thesis project; its copper study uses the original gold calibration, while this Paper reuses the audited September 7 gold parameters.

```sh
python -m pip install -r code/requirements.txt
python main.py
python -m pytest code/tests -q
```

Use `python main.py --recalibrate` to repeat the Hawkes local refinement. Build the Paper by running `pdflatex Articolo.tex` twice from `paper/`.

## Interpretation

Q-law plus assumed WACC is a sensitivity operator. Gold sales versus production, corporate accounting, ownership, finite reserves and risk-premium reconciliation remain unresolved. Copper is admitted as a fixed-sales component-margin scenario; this does not reconcile corporate FCFF. Signed terminal values and a five-year truncation comparison make the terminal convention explicit; neither is a calibrated mine-life model. Historical OOS is retained separately from the current refit.

## Authors

Stefano Falcione, Marco Fracca, Filippo Triassi, Giorgio Zoccatelli, Andrea Rostagno, Francesco Florio, Giacomo Scali, Jacopo Foralosso, Federico Vesco, Lorenzo Pietra, Bader Moussaif, Davide Sisto, Matteo Armando, Davide D'Amico, Pietro Weisz, Salvatore Gabriele Messina and Alessandro Coco.

## Citation

Barrick Gold Research Teams (2026), *Operating-Value Sensitivity for Barrick Mining*, Starting Finance Club PoliTo Research, working draft, September 7, 2026; revised October 5, 2026.

## Probability-measure contract - October 5, 2026

Option calibration remains under Q with deterministic rates. The operating experiment uses an artificial scenario law R: transferred coefficients, imposed commodity mean schedules and independent WACC shocks. No Q-to-P density, physical risk premia or pricing kernel is estimated. A fixed-delivery future has zero drift in the pricing convention; the cross-delivery copper curve is a scenario mean schedule, not that futures drift. WACC is not the short rate. Combining Q-shaped scenarios and assumed WACC is a sensitivity operator, not corporate pricing. Replacing WACC with a risk-free rate alone would not reconcile corporate cash flows.

`--valuation-law` supports only `conditional_option_implied_shape`; physical and corporate risk-neutral interpretations are rejected. The manifest records the measure boundary. Tests check jump compensation and zero fixed-future drift for all four engines. The October 5 Paper replay reproduces the October 3 numerical aggregates exactly. Copper mine volumes/CoS remain controlled fixed scenarios; they are not the gold mine-level SARIMA forecasts.

## Active project graph

[Graph report](../Barrick%20Mining%20UNIFICATO/graphify-out/GRAPH_REPORT.md) covers active integration and accepted measure/Paper evidence. HTML and JSON are alongside the report; archive/build duplicates and licensed quote rows are excluded.
