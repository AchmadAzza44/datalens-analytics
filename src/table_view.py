"""Tabel detail: pengurutan dan pemotongan halaman (logika murni, mudah diuji)."""

from __future__ import annotations

import pandas as pd


def sort_table(df: pd.DataFrame, column: str, ascending: bool = True) -> pd.DataFrame:
    if column not in df.columns:
        raise KeyError(f"Kolom '{column}' tidak ditemukan.")
    return df.sort_values(column, ascending=ascending, kind="stable")


def paginate(df: pd.DataFrame, page: int, page_size: int = 20) -> tuple[pd.DataFrame, int]:
    """Kembalikan (potongan halaman, jumlah halaman); halaman di luar rentang dijepit."""
    if page_size < 1:
        raise ValueError("page_size harus >= 1")
    pages = max(1, -(-len(df) // page_size))
    page = min(max(1, page), pages)
    start = (page - 1) * page_size
    return df.iloc[start : start + page_size], pages
