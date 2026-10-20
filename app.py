"""DataLens Analytics - dashboard analitik interaktif berbasis prinsip HCI."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.data_ingestion import DatasetError, load_dataset, prepare_dataframe, validate_columns
from src.export import filter_summary_text, pdf_report_bytes, to_csv_bytes
from src.filters import FilterState, apply_filters, preset_from_json, preset_to_json, validate_date_range
from src.metrics import compute_kpis
from src.table_view import paginate, sort_table
from src.visualizations import (FREQUENCIES, create_category_chart, create_scatter_chart, create_share_chart,
                               create_trend_chart, numeric_extra_columns)

SAMPLE_PATH = Path(__file__).parent / "data" / "sample" / "transaksi_contoh_sintetis.csv"

st.set_page_config(page_title="DataLens Analytics", page_icon="📊", layout="wide")
st.title("DataLens Analytics")
st.caption("Dashboard analitik transaksi. Definisi KPI ada di bagian 'Bantuan & definisi metrik' di bawah.")


@st.cache_data(show_spinner=False)
def _load_and_prepare(raw: bytes | None, name: str):
    import io

    source = SAMPLE_PATH if raw is None else io.BytesIO(raw)
    frame = load_dataset(source, filename=name)
    structure = validate_columns(frame)
    if not structure.valid:
        return None, structure
    return prepare_dataframe(frame)


# ---- Sumber data ----
st.sidebar.header("1. Muat data")
uploaded = st.sidebar.file_uploader("Unggah CSV atau XLSX", type=["csv", "xlsx"])
use_sample = st.sidebar.toggle("Pakai data contoh SINTETIS", value=uploaded is None, disabled=uploaded is not None)

if uploaded is None and not use_sample:
    st.info("Unggah file transaksi (kolom wajib: tanggal, kategori, nilai) atau aktifkan data contoh di sidebar.")
    st.stop()

source_name = uploaded.name if uploaded else SAMPLE_PATH.name
try:
    with st.spinner("Memuat dan memvalidasi data..."):
        df, report = _load_and_prepare(uploaded.getvalue() if uploaded else None, source_name)
except DatasetError as exc:
    st.error(f"Data tidak dapat dimuat. {exc}")
    st.stop()

if df is None or not report.valid:
    for message in report.errors:
        st.error(message)
    st.stop()
for message in report.warnings:
    st.warning(message)
if uploaded is None:
    st.info("Anda memakai **data contoh sintetis**; angka di bawah bukan hasil bisnis nyata.")
st.success(f"Data dimuat: {len(df):,} baris valid dari {report.rows_total:,} baris ({source_name}).")

# ---- Filter (state disimpan agar reset berfungsi) ----
st.sidebar.header("2. Filter")
min_date, max_date = df["tanggal"].min().date(), df["tanggal"].max().date()
categories = sorted(df["kategori"].unique())

if st.sidebar.button("Reset semua filter"):
    for key in ("date_range", "cats", "search", "freq", "drill"):
        st.session_state.pop(key, None)

preset_file = st.sidebar.file_uploader("Muat preset filter (.json)", type=["json"], key="preset_upload")
if preset_file is not None and st.session_state.get("applied_preset") != preset_file.file_id:
    try:
        loaded, loaded_freq, notes = preset_from_json(preset_file.getvalue().decode("utf-8"), categories, min_date, max_date)
        st.session_state.update(date_range=(loaded.start_date, loaded.end_date), cats=loaded.categories,
                                search=loaded.search, freq=loaded_freq if loaded_freq in FREQUENCIES else "Harian")
        st.session_state["applied_preset"] = preset_file.file_id
        for note in notes:
            st.sidebar.warning(note)
        st.sidebar.success("Preset dimuat.")
    except (ValueError, UnicodeDecodeError) as exc:
        st.sidebar.error(str(exc))

date_range = st.sidebar.date_input("Rentang tanggal", value=(min_date, max_date), min_value=min_date,
                                   max_value=max_date, key="date_range")
selected = st.sidebar.multiselect("Kategori (kosong = semua)", categories, key="cats")
search = st.sidebar.text_input("Cari di semua kolom", key="search")
freq = st.sidebar.radio("Granularitas tren", list(FREQUENCIES), horizontal=True, key="freq")

if not isinstance(date_range, tuple) or len(date_range) != 2:
    st.warning("Pilih tanggal awal **dan** tanggal akhir untuk menerapkan filter tanggal.")
    st.stop()
error = validate_date_range(*date_range)
if error:
    st.error(error)
    st.stop()

state = FilterState(date_range[0], date_range[1], selected, search)
filtered = apply_filters(df, state)
st.sidebar.download_button("Simpan filter sebagai preset", preset_to_json(state, freq), "preset_filter.json", "application/json")

st.markdown("**Filter aktif:** " + " | ".join(state.describe()))
if filtered.empty:
    st.warning("Tidak ada transaksi yang cocok dengan filter. Klik 'Reset semua filter' atau longgarkan filter.")
    st.stop()

# ---- KPI ----
kpis = compute_kpis(filtered)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Jumlah transaksi", f"{kpis['total_transactions']:,}")
c2.metric("Total nilai (Rp)", f"{kpis['total_value']:,.0f}")
c3.metric("Rata-rata per transaksi (Rp)", f"{kpis['average_value']:,.0f}")
c4.metric("Kategori teratas", kpis["top_category"], help=f"Total Rp {kpis['top_category_value']:,.0f}")

# ---- Grafik ----
left, right = st.columns(2)
left.plotly_chart(create_trend_chart(filtered, freq, source=source_name), width="stretch")
event = right.plotly_chart(create_category_chart(filtered, source=source_name), width="stretch",
                           on_select="rerun", selection_mode="points", key="category_chart")
right.caption("Klik sebuah batang untuk drill-down ke rincian transaksi kategori itu.")
points = event.selection.points if event and event.selection else []
if points and points[0].get("x") in set(filtered["kategori"]):
    st.session_state["drill"] = points[0]["x"]

share = create_share_chart(filtered, source=source_name)
extra = numeric_extra_columns(filtered)
if share is not None or extra:
    g1, g2 = st.columns(2)
    if share is not None:
        g1.plotly_chart(share, width="stretch")
    if extra:
        x_col = g2.selectbox("Scatter: nilai vs kolom numerik", extra)
        g2.plotly_chart(create_scatter_chart(filtered, x_col, source=source_name), width="stretch")

# ---- Tabel detail + drill-down ----
st.subheader("Tabel detail")
options = ["(semua)"] + sorted(filtered["kategori"].unique())
if st.session_state.get("drill") not in options:
    st.session_state["drill"] = "(semua)"
drill = st.selectbox("Lihat rincian kategori tertentu (drill-down)", options, key="drill")
detail = filtered if drill == "(semua)" else filtered[filtered["kategori"] == drill]
sc1, sc2, sc3 = st.columns([2, 1, 1])
sort_col = sc1.selectbox("Urutkan menurut", list(detail.columns), index=list(detail.columns).index("tanggal"))
ascending = sc2.radio("Arah", ["Naik", "Turun"], horizontal=True) == "Naik"
page_size = sc3.selectbox("Baris/halaman", [10, 20, 50], index=1)
ordered = sort_table(detail, sort_col, ascending)
_, pages = paginate(ordered, 1, page_size)
page = st.number_input(f"Halaman (1-{pages})", min_value=1, max_value=pages, value=1)
view, _ = paginate(ordered, int(page), page_size)
st.dataframe(view, width="stretch", hide_index=True)
st.caption(f"{len(detail):,} baris pada tampilan ini.")

# ---- Ekspor sesuai filter aktif ----
st.subheader("Ekspor")
d1, d2 = st.columns(2)
d1.download_button("Unduh CSV (sesuai filter aktif)", to_csv_bytes(detail), "datalens_filtered.csv", "text/csv")
d2.download_button("Unduh laporan PDF (sesuai filter aktif)",
                   pdf_report_bytes(filtered, kpis, state.describe(), len(df), source_name, synthetic=uploaded is None),
                   "datalens_laporan.pdf", "application/pdf")
st.caption(filter_summary_text(state.describe() + ([f"Drill-down: {drill}"] if drill != "(semua)" else []),
                               len(detail), len(df)))

# ---- Bantuan ----
with st.expander("Bantuan & definisi metrik"):
    st.markdown(
        """
- **Jumlah transaksi** = banyaknya baris setelah filter.
- **Total nilai** = jumlah kolom `nilai`; **Rata-rata** = total / jumlah transaksi.
- **Kategori teratas** = kategori dengan total nilai terbesar pada data terfilter.
- Baris dengan tanggal/nilai tidak valid dibuang dan jumlahnya dilaporkan di atas.
- Filter kategori kosong berarti semua kategori. Semua komponen (KPI, grafik, tabel, ekspor) memakai filter yang sama.
"""
    )
