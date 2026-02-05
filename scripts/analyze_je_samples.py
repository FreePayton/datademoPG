"""Analyze JE samples spreadsheet and print a quick summary."""
from __future__ import annotations

import inspect
import pathlib
from typing import Iterable

import pandas as pd


DATE_HINTS = ("date", "dt", "timestamp")


def _likely_date_columns(columns: Iterable[str]) -> list[str]:
    return [
        column
        for column in columns
        if any(hint in column.lower() for hint in DATE_HINTS)
    ]


def _coerce_date_columns(df: pd.DataFrame) -> list[str]:
    coerced: list[str] = []
    for column in _likely_date_columns(df.columns):
        series = df[column]
        if series.dtype.kind in {"M"}:
            continue
        parsed = _to_datetime(series)
        if parsed.notna().any():
            df[column] = parsed
            coerced.append(column)
    return coerced


def _to_datetime(series: pd.Series) -> pd.Series:
    kwargs = {"errors": "coerce"}
    if "infer_datetime_format" in inspect.signature(pd.to_datetime).parameters:
        kwargs["infer_datetime_format"] = True
    return pd.to_datetime(series, **kwargs)


def _build_summary(df: pd.DataFrame) -> dict[str, object]:
    coerced = _coerce_date_columns(df)
    summary = {
        "rows": len(df.index),
        "columns": list(df.columns),
        "coerced_date_columns": coerced,
        "null_counts": df.isna().sum().to_dict(),
    }
    return summary


def _load_samples(path: pathlib.Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing sample file: {path}")
    return pd.read_excel(path)


def main() -> None:
    base_dir = pathlib.Path(__file__).resolve().parents[1]
    sample_path = base_dir / "je_samples.xlsx"
    df = _load_samples(sample_path)
    summary = _build_summary(df)
    print("JE Samples Summary")
    for key, value in summary.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
