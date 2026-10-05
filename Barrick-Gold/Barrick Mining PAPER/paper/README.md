# Operating-Value Sensitivity for Barrick Mining

Research working draft prepared September 7, 2026 and revised October 5, 2026. Ten pages including the cover, with the original typography and margins.

The gold comparison retains the audited September 7 calibration and its separate historical OOS evidence. The copper extension uses three producing mines, ten historical acquisition dates, six admitted temporal pairs and paired finite-horizon operating values. No model beats observed-IV persistence in the copper rolling pilot. Fixed-origin results remain a robustness comparison.

All values are aggregate operating proxies. No share-price target, corporate fair value or market-relative conclusion is reported. The copper volumes and costs are fixed scenarios; Q/P, corporate FCFF, ownership/financial claims and reserves remain unreconciled. The original gold vectors mix company actuals and an eight-mine forecast; the scope break is disclosed.

## Compile

```sh
pdflatex Articolo.tex
pdflatex Articolo.tex
```

The bibliography is frozen in `sections/07_references.tex`; no BibTeX step is needed. For Overleaf upload `Articolo.zip`, choose `Articolo.tex` and pdfLaTeX. The ZIP contains only source dependencies, without Python code or LaTeX build files.

Standalone offline execution and data provenance are documented in [../README.md](../README.md). The gold and new copper technical audits are retained separately in `../code/`.
