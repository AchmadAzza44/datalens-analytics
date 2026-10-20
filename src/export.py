"""Ekspor data hasil filter (CSV) dan ringkasan metadata filter."""

from __future__ import annotations

import io
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """CSV UTF-8 persis seperti data yang sedang ditampilkan (tanpa indeks)."""
    return df.to_csv(index=False).encode("utf-8")


def filter_summary_text(filters: list[str], rows: int, total_rows: int) -> str:
    lines = [f"Baris diekspor: {rows} dari {total_rows}", "Filter aktif:"]
    lines += [f"- {item}" for item in filters]
    return "\n".join(lines)


def _png(fig) -> io.BytesIO:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def pdf_report_bytes(df: pd.DataFrame, kpis: dict[str, Any], filters: list[str], total_rows: int, source: str,
                     synthetic: bool = False) -> bytes:
    """Laporan PDF sesuai filter aktif: KPI, tren, kategori, 10 baris teratas, definisi metrik."""
    if df.empty:
        raise ValueError("Tidak ada data untuk dilaporkan.")
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="Laporan DataLens Analytics", leftMargin=2 * cm, rightMargin=2 * cm)
    st = getSampleStyleSheet()
    flow: list[Any] = [Paragraph("Laporan DataLens Analytics", st["Title"]),
                       Paragraph(f"Sumber data: {source}. Baris dilaporkan: {len(df):,} dari {total_rows:,} (setelah filter).", st["BodyText"])]
    if synthetic:
        flow.append(Paragraph("<b>Data SINTETIS - bukan hasil bisnis nyata.</b>", st["BodyText"]))
    flow += [Paragraph("Filter aktif", st["Heading2"])] + [Paragraph(f"- {f}", st["BodyText"]) for f in filters]
    flow.append(Paragraph("Ringkasan KPI", st["Heading2"]))
    kpi_rows = [["Metrik", "Nilai"], ["Jumlah transaksi", f"{kpis['total_transactions']:,}"],
                ["Total nilai (Rp)", f"{kpis['total_value']:,.0f}"], ["Rata-rata per transaksi (Rp)", f"{kpis['average_value']:,.0f}"],
                ["Kategori teratas", f"{kpis['top_category']} (Rp {kpis['top_category_value']:,.0f})"]]
    table = Table(kpi_rows, colWidths=[7 * cm, 9 * cm])
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey)]))
    flow.append(table)

    from .visualizations import aggregate_categories, aggregate_trend
    trend = aggregate_trend(df, "Mingguan" if (df["tanggal"].max() - df["tanggal"].min()).days > 60 else "Harian")
    fig, ax = plt.subplots(figsize=(7, 2.6))
    ax.plot(trend["tanggal"], trend["nilai"], marker="o", ms=2.5, color="#0072B2")
    ax.set_ylim(bottom=0)
    ax.set_title("Tren nilai transaksi"), ax.set_ylabel("Nilai (Rp)"), ax.set_xlabel("Tanggal")
    ax.tick_params(axis="x", labelrotation=30, labelsize=7)
    flow += [Spacer(1, 8), RLImage(_png(fig), width=16 * cm, height=6 * cm)]
    cats = aggregate_categories(df)
    fig, ax = plt.subplots(figsize=(7, 2.6))
    ax.bar(cats["kategori"], cats["nilai"], color="#E69F00")
    ax.set_title("Total nilai per kategori"), ax.set_ylabel("Total nilai (Rp)"), ax.tick_params(axis="x", labelrotation=20, labelsize=8)
    flow.append(RLImage(_png(fig), width=16 * cm, height=6 * cm))

    flow.append(Paragraph("10 transaksi bernilai tertinggi", st["Heading2"]))
    top = df.nlargest(10, "nilai")
    rows = [list(map(str, top.columns))] + [[f"{v:,.0f}" if isinstance(v, float) else str(v)[:19] for v in r] for r in top.itertuples(index=False)]
    grid = Table(rows, repeatRows=1)
    grid.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 7)]))
    flow += [grid, Paragraph("Definisi dan keterbatasan", st["Heading2"]),
             Paragraph("Total nilai = SUM(nilai); rata-rata = total / jumlah transaksi. Baris dengan tanggal/nilai tidak valid dibuang "
                       "saat pemuatan dan dilaporkan di aplikasi. Laporan hanya mencerminkan data yang diunggah.", st["BodyText"])]
    doc.build(flow)
    return buf.getvalue()
