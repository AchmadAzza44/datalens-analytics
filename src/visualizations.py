"""Grafik Plotly: tren (line) dan perbandingan kategori (bar), dengan judul, satuan, dan sumber."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

FREQUENCIES = {"Harian": "D", "Mingguan": "W", "Bulanan": "MS"}
PALETTE = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#000000"]


def aggregate_trend(df: pd.DataFrame, frequency: str = "Harian") -> pd.DataFrame:
    """Jumlahkan nilai per periode; periode tanpa transaksi bernilai 0."""
    rule = FREQUENCIES.get(frequency)
    if rule is None:
        raise ValueError(f"Frekuensi tidak dikenal: {frequency}")
    series = df.set_index("tanggal")["nilai"].resample(rule).sum()
    return series.rename("nilai").reset_index()


def aggregate_categories(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("kategori")["nilai"].sum().reset_index().sort_values("nilai", ascending=False).reset_index(drop=True)
    )


def _empty_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        annotations=[dict(text="Tidak ada data untuk filter ini", showarrow=False, font=dict(size=16))],
        xaxis_visible=False,
        yaxis_visible=False,
    )
    return fig


def create_trend_chart(df: pd.DataFrame, frequency: str = "Harian", unit: str = "Rp", source: str = "") -> go.Figure:
    title = f"Tren nilai transaksi ({frequency.lower()})"
    if df.empty:
        return _empty_figure(title)
    data = aggregate_trend(df, frequency)
    fig = px.line(
        data, x="tanggal", y="nilai", markers=True, title=title,
        labels={"tanggal": "Tanggal", "nilai": f"Nilai ({unit})"}, color_discrete_sequence=PALETTE,
    )
    fig.update_yaxes(rangemode="tozero")
    _annotate(fig, df, source)
    return fig


def create_category_chart(df: pd.DataFrame, unit: str = "Rp", source: str = "") -> go.Figure:
    title = "Perbandingan total nilai per kategori"
    if df.empty:
        return _empty_figure(title)
    data = aggregate_categories(df)
    fig = px.bar(
        data, x="kategori", y="nilai", title=title, text_auto=".3s",
        labels={"kategori": "Kategori", "nilai": f"Total nilai ({unit})"}, color_discrete_sequence=PALETTE,
    )
    fig.update_yaxes(rangemode="tozero")
    _annotate(fig, df, source)
    return fig


def _annotate(fig: go.Figure, df: pd.DataFrame, source: str) -> None:
    period = f"{df['tanggal'].min():%Y-%m-%d} s.d. {df['tanggal'].max():%Y-%m-%d}"
    note = f"Periode: {period}" + (f" | Sumber: {source}" if source else "")
    fig.add_annotation(
        text=note, xref="paper", yref="paper", x=0, y=-0.28, showarrow=False, font=dict(size=11), xanchor="left"
    )


MAX_DONUT_CATEGORIES = 6
MAX_SCATTER_POINTS = 5000


def create_share_chart(df: pd.DataFrame, source: str = "") -> go.Figure | None:
    """Donut proporsi per kategori; hanya bila kategori <= 6 (PRD: pie/donut untuk jumlah kategori terbatas)."""
    data = aggregate_categories(df)
    if data.empty or len(data) > MAX_DONUT_CATEGORIES or (data["nilai"] <= 0).any():
        return None
    fig = px.pie(data, names="kategori", values="nilai", hole=0.5, title="Proporsi total nilai per kategori",
                 color_discrete_sequence=PALETTE)
    fig.update_traces(textinfo="label+percent", sort=False)
    return fig


def numeric_extra_columns(df: pd.DataFrame) -> list[str]:
    """Kolom numerik selain 'nilai' yang dapat dipakai untuk scatter (hubungan dua variabel numerik)."""
    return [c for c in df.select_dtypes("number").columns if c != "nilai"]


def create_scatter_chart(df: pd.DataFrame, x_column: str, source: str = "") -> go.Figure:
    if x_column not in df.columns or x_column == "nilai":
        raise ValueError("Pilih kolom numerik selain 'nilai'.")
    total = len(df)
    if total > MAX_SCATTER_POINTS:  # batasi beban browser; sampel acak dengan seed tetap dan dinyatakan di judul
        df = df.sample(MAX_SCATTER_POINTS, random_state=0)
    suffix = f" (sampel {MAX_SCATTER_POINTS:,} dari {total:,} baris)" if total > MAX_SCATTER_POINTS else ""
    fig = px.scatter(df, x=x_column, y="nilai", color="kategori", title=f"Hubungan {x_column} dan nilai{suffix}",
                     labels={x_column: x_column, "nilai": "Nilai (Rp)"}, color_discrete_sequence=PALETTE, opacity=0.7)
    _annotate(fig, df, source)
    return fig
