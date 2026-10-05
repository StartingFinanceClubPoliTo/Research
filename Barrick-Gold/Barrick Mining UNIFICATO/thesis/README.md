# Barrick unified thesis — working draft

Main file: `Articolo.tex`

Engine: pdfLaTeX

Release date: **TBD**

The self-contained Research working draft now integrates September calibration, dense OOS diagnostics and the conditional corporate valuation. Historical August examples remain explicitly dated; they are not current calibration evidence.

The current executable Team 8/Barrick experiment is maintained in the [Research companion](https://github.com/StartingFinanceClubPoliTo/Research/tree/main/Barrick-Gold/Barrick%20Mining%20UNIFICATO/code):

- snapshot date September 2, 2026;
- authoritative run `20260904T130000Z-team8-refresh-v4`;
- 605 eligible calls before CC64 sampling;
- Full Bates–Hawkes best rolling OOS IV RMSE at 65.0507 bp;
- Barrick market reference USD 44.13.

Heston has the best current in-sample IV RMSE. Full Bates-Hawkes leads the four-model dense OOS ranking, but no model beats observed-IV persistence. Model targets contain 4,667 observations; persistence comparisons have 4,026. The Treasury curve is a par-yield proxy, not a bootstrapped zero curve.

Compile `Articolo.tex` with pdfLaTeX. Upload `chapters/`, `img/` and the Research cover with the main file. Build by-products and continuity registers stay outside Overleaf. The measure transfer, accounting/equity bridge and corporate assumptions remain qualified research limitations, not a finished valuation product.


## Copper historical extension — October 3 local acquisition

The original gold-only baseline excluded copper. The separate extension admits
Lumwana, Zaldívar and Jabal Sayid, using already attributable sold volumes.
Ten historical dates were acquired with about 100 spaced quote requests per date;
7 quality-admitted surfaces produce 6 chronological pairs (480 common
forecasts, 375 on persistence support). This is a preliminary pilot,
not the full 31-date gold calendar. All model estimates are origin-only with
dated Treasury curves and projected states; static strike holdout remains separate.
No robust model-superiority claim follows from this small sample.

Authoritative copper run: `../Github-Branch/outputs/valuation/20261003-gold-plus-copper-v3-temporal`;
rolling evidence: `../Github-Branch/outputs/validation/copper_temporal_oos_budget112_20261003`;
fixed-origin check: `../Github-Branch/outputs/validation/copper_fixed_origin_20261003`.
The paired mean copper increment is USD 2.618–2.663 billion over five years
without terminal value, conditional on fixed Q2 sales/CoS and the inherited
margin-to-value assumptions. This is an aggregate operating-value proxy;
accounting, capex, reserve life and the corporate equity bridge remain unresolved.
The source thesis now includes the supplied corporate-perimeter revision and
generated copper tables/figures. Licensed quote rows remain local.

## Copper and measure audit - October 5, 2026

The eight-mine gold study omitted copper. Three producing copper mines now enter through attributable Q2 sales and CoS; historical option acquisition uses ten dates and six admitted temporal pairs. No copper model beats rolling IV persistence. Copper mine operations remain fixed scenarios rather than a fitted mine-level forecast.

Chapter 12 separates option-pricing Q from the artificial operating scenario law R. No Q-to-P change, physical risk premia or corporate pricing kernel is estimated. WACC is not a short rate, and the copper delivery-curve schedule is not the time drift of a fixed-delivery future. These boundaries apply to both metals. The thesis uses the original gold parameters; the separate Paper paired run uses audited September 7 gold parameters. Release remains TBD and no corporate fair value is asserted.
