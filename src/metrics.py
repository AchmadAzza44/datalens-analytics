"""KPI dasar; definisi tertulis di docs/DATA_DICTIONARY.md."""

from __future__ import annotations

from typing import Any

import pandas as pd


def compute_kpis(df: pd.DataFrame, value_column: str = "nilai", category_column: str = "kategori") -> dict[str, Any]:
    """Hitung jumlah transaksi, total, rata-rata, dan kategori teratas.

    Mengembalikan nilai ``None`` (bukan 0) untuk metrik yang tidak terdefinisi pada data kosong.
    """
    kpis: dict[str, Any] = {
        "total_transactions": int(len(df)),
        "total_value": None,
        "average_value": None,
        "top_category": None,
        "top_category_value": None,
    }
    if df.empty:
        return kpis

    values = pd.to_numeric(df[value_column], errors="coerce")
    kpis["total_value"] = float(values.sum())
    kpis["average_value"] = float(values.mean())
    if category_column in df.columns:
        by_category = values.groupby(df[category_column]).sum().sort_values(ascending=False)
        kpis["top_category"] = str(by_category.index[0])
        kpis["top_category_value"] = float(by_category.iloc[0])
    return kpis
