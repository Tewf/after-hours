# French Income Tax Analysis (2024)

Mathematical analysis and modeling of France's progressive income tax system for 2024.

## What It Does

1. **Visualizes** marginal vs. effective tax rates across income brackets
2. **Models** the Gross-to-Net conversion (social charges, CSG, 10% deduction)
3. **Fits** an exponential decay model to the effective tax rate per bracket
4. **Finds** the fiscal "tipping point" (~62k gross) using the Lambert W function, where marginal efficiency shifts

## Files

- `taxes.qmd` — Quarto document with all code, math, and visualizations
- `taxes.pdf` — Rendered output

## How to Render

```bash
quarto render taxes.qmd
```

Requires: Python 3, NumPy, SciPy, Matplotlib, pandas, Quarto
