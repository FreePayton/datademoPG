# datademoPG

This repository includes a lightweight data workflow for summarizing the `je_samples.xlsx` general ledger export.

## What the workflow produces

Running the analysis script (locally or in GitHub Actions) generates an `outputs/` folder containing:

- `summary.json`: Core summary metrics (row/column counts, missing values, date ranges).
- `summary.md`: Human-readable summary.
- `missing_counts.csv`: Missing values per column.
- `date_ranges.csv`: Min/max dates for detected date columns (when available).
- `numeric_descriptive_stats.csv`: Descriptive statistics for numeric columns.

## Running locally

```bash
python -m pip install pandas openpyxl
python scripts/analyze_je_samples.py
```

## Running in GitHub Actions

The `JE Sample Summary` workflow runs when you push changes to the Excel file or script, or when triggered manually. It uploads the `outputs/` directory as a downloadable artifact named `je-sample-summary`.
