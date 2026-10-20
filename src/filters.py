"""Filter konsisten: satu fungsi dipakai KPI, grafik, tabel, dan ekspor."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from datetime import date

import pandas as pd


@dataclass
class FilterState:
    start_date: date | None = None
    end_date: date | None = None
    categories: list[str] = field(default_factory=list)  # kosong = semua kategori
    search: str = ""

    def describe(self) -> list[str]:
        parts = []
        if self.start_date and self.end_date:
            parts.append(f"Tanggal: {self.start_date} s.d. {self.end_date}")
        parts.append(f"Kategori: {', '.join(self.categories) if self.categories else 'semua'}")
        if self.search.strip():
            parts.append(f"Pencarian: '{self.search.strip()}'")
        return parts


def validate_date_range(start_date: date | None, end_date: date | None) -> str | None:
    """Kembalikan pesan error bila rentang tanggal tidak masuk akal (error prevention)."""
    if start_date and end_date and start_date > end_date:
        return "Tanggal awal tidak boleh setelah tanggal akhir."
    return None


def apply_date_filter(df: pd.DataFrame, date_column: str, start_date, end_date) -> pd.DataFrame:
    """Filter inklusif pada rentang tanggal; df sumber tidak diubah."""
    error = validate_date_range(start_date, end_date)
    if error:
        raise ValueError(error)
    dates = pd.to_datetime(df[date_column], errors="coerce").dt.date
    mask = pd.Series(True, index=df.index)
    if start_date is not None:
        mask &= dates >= start_date
    if end_date is not None:
        mask &= dates <= end_date
    return df[mask]


def apply_category_filter(df: pd.DataFrame, column: str, selected_categories: list[str]) -> pd.DataFrame:
    """Daftar kosong berarti tidak ada pembatasan kategori."""
    if not selected_categories:
        return df
    return df[df[column].isin(selected_categories)]


def apply_search(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Pencarian teks (tidak peka huruf besar/kecil) pada semua kolom."""
    query = query.strip()
    if not query:
        return df
    text = df.astype(str)
    mask = text.apply(lambda col: col.str.contains(query, case=False, regex=False)).any(axis=1)
    return df[mask]


def apply_filters(df: pd.DataFrame, state: FilterState) -> pd.DataFrame:
    """Terapkan semua filter dengan urutan tetap sehingga seluruh komponen konsisten."""
    result = apply_date_filter(df, "tanggal", state.start_date, state.end_date)
    result = apply_category_filter(result, "kategori", state.categories)
    return apply_search(result, state.search)


PRESET_VERSION = 1


def preset_to_json(state: FilterState, frequency: str = "Harian") -> str:
    """Serialisasi filter ke JSON agar dapat disimpan/dibagikan (preset filter)."""
    return json.dumps({
        "version": PRESET_VERSION,
        "start_date": state.start_date.isoformat() if state.start_date else None,
        "end_date": state.end_date.isoformat() if state.end_date else None,
        "categories": list(state.categories), "search": state.search, "frequency": frequency,
    }, ensure_ascii=False, indent=2)


def preset_from_json(text: str, available_categories: list[str], min_date: date, max_date: date) -> tuple[FilterState, str, list[str]]:
    """Muat preset dan sesuaikan dengan data saat ini; setiap penyesuaian dilaporkan, tidak diam-diam."""
    try:
        raw = json.loads(text)
        start = date.fromisoformat(raw["start_date"]) if raw.get("start_date") else min_date
        end = date.fromisoformat(raw["end_date"]) if raw.get("end_date") else max_date
        cats, search, freq = list(raw.get("categories", [])), str(raw.get("search", "")), raw.get("frequency", "Harian")
    except (json.JSONDecodeError, KeyError, ValueError, TypeError, AttributeError) as exc:
        raise ValueError(f"Berkas preset tidak valid: {exc}") from exc
    notes: list[str] = []
    unknown = [c for c in cats if c not in available_categories]
    if unknown:
        notes.append(f"Kategori tidak ada pada data ini dan dibuang dari preset: {', '.join(unknown)}.")
        cats = [c for c in cats if c in available_categories]
    clamped_start, clamped_end = max(start, min_date), min(end, max_date)
    if (clamped_start, clamped_end) != (start, end):
        notes.append(f"Rentang tanggal preset disesuaikan ke rentang data ({clamped_start} s.d. {clamped_end}).")
    if clamped_start > clamped_end:
        raise ValueError("Rentang tanggal preset tidak beririsan dengan data.")
    return FilterState(clamped_start, clamped_end, cats, search), freq, notes
