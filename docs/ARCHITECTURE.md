# Arsitektur

```text
app.py (Streamlit: input, state, tampilan)
  ├─ src/data_ingestion.py  baca + validasi + normalisasi tipe
  ├─ src/filters.py         FilterState + apply_filters (satu jalur untuk semua komponen)
  ├─ src/metrics.py         KPI
  ├─ src/visualizations.py  agregasi + figur Plotly
  ├─ src/table_view.py      sort + paginate
  ├─ src/export.py          CSV dan PDF (ReportLab + matplotlib) sesuai filter aktif
  └─ src/usability.py       pencatatan hasil uji usability
```
Alur data: unggah -> `load_dataset` -> `prepare_dataframe` -> `apply_filters` -> KPI/grafik/tabel/ekspor.
Semua logika berada di `src/` sebagai fungsi murni agar dapat diuji; `app.py` hanya merangkai.

Keputusan: Streamlit saja (tanpa FastAPI/PostgreSQL) karena PRD menyatakan backend baru ditambahkan bila ada kebutuhan nyata.
Fitur interaksi: preset filter (JSON), drill-down dari klik grafik (`on_select`), donut/scatter kondisional.
Batasan: data dimuat penuh ke memori (aman hingga >=1 juta baris, lihat PERFORMANCE.md); autentikasi, backend FastAPI, dan PostgreSQL (P2) sengaja tidak dibangun karena PRD menyatakan baru ditambahkan bila ada kebutuhan nyata.
