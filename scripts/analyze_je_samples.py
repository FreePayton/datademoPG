from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = BASE_DIR / "je_samples.xlsx"
OUTPUT_DIR = BASE_DIR / "outputs"


def _ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _coerce_date_columns(df: pd.DataFrame) -> list[str]:
    date_columns: list[str] = []
    for column in df.columns:
        series = df[column]
        if pd.api.types.is_datetime64_any_dtype(series):
            date_columns.append(column)
            continue

        column_name = str(column).lower()
        should_try = "date" in column_name or column_name.endswith("dt")
        if not should_try and series.dtype != object:
            continue

        parsed = pd.to_datetime(series, errors="coerce", infer_datetime_format=True)
        if parsed.notna().any():
            if should_try or parsed.notna().sum() >= max(1, int(0.8 * len(series))):
                df[column] = parsed
                date_columns.append(column)

    return date_columns


def _build_summary(df: pd.DataFrame) -> dict:
    summary: dict[str, object] = {
        "row_count": int(len(df)),
        "column_count": int(df.shape[1]),
        "columns": [str(col) for col in df.columns],
        "missing_counts": df.isna().sum().astype(int).to_dict(),
    }

    date_columns = _coerce_date_columns(df)
    date_ranges: dict[str, dict[str, object]] = {}
    for column in date_columns:
        series = df[column]
        if series.notna().any():
            date_ranges[str(column)] = {
                "min": series.min().strftime("%Y-%m-%d"),
                "max": series.max().strftime("%Y-%m-%d"),
                "non_null": int(series.notna().sum()),
            }
    summary["date_ranges"] = date_ranges

    numeric_columns = df.select_dtypes(include="number")
    if not numeric_columns.empty:
        summary["numeric_descriptive_stats"] = numeric_columns.describe().to_dict()
    else:
        summary["numeric_descriptive_stats"] = {}

    return summary


def _write_outputs(summary: dict, df: pd.DataFrame) -> None:
    json_path = OUTPUT_DIR / "summary.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    (OUTPUT_DIR / "summary.md").write_text(
        "# JE Sample Summary\n\n"
        f"- Rows: {summary['row_count']}\n"
        f"- Columns: {summary['column_count']}\n"
        "\n## Date Ranges\n"
        + (
            "\n".join(
                f"- **{column}**: {info['min']} to {info['max']} (non-null: {info['non_null']})"
                for column, info in summary["date_ranges"].items()
            )
            or "- No date columns detected."
        )
        + "\n\n## Missing Counts\n"
        + "\n".join(
            f"- **{column}**: {count}"
            for column, count in summary["missing_counts"].items()
        )
        + "\n",
        encoding="utf-8",
    )

    missing_counts = (
        pd.Series(summary["missing_counts"], name="missing_count")
        .rename_axis("column")
        .reset_index()
    )
    missing_counts.to_csv(OUTPUT_DIR / "missing_counts.csv", index=False)

    date_ranges = summary.get("date_ranges", {})
    if date_ranges:
        pd.DataFrame.from_dict(date_ranges, orient="index").rename_axis("column").reset_index().to_csv(
            OUTPUT_DIR / "date_ranges.csv", index=False
        )

    numeric_columns = df.select_dtypes(include="number")
    if not numeric_columns.empty:
        numeric_columns.describe().to_csv(OUTPUT_DIR / "numeric_descriptive_stats.csv")


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing input file at {INPUT_PATH}")

    _ensure_output_dir()
    df = pd.read_excel(INPUT_PATH)
    summary = _build_summary(df)
    _write_outputs(summary, df)


if __name__ == "__main__":
    main()
