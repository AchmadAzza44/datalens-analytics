# Test Plan
Jalankan: `python -m pytest -q` (hasil terakhir: 25 lulus).

| ID | Kasus | Input | Diharapkan | Tes |
|---|---|---|---|---|
| T1 | Muat dari path/file upload | CSV valid | 4 baris terbaca | test_load_from_filelike_and_path |
| T2 | Format/kosong/tidak ada file | .txt, header saja | DatasetError | test_load_rejects_bad_format_and_empty |
| T3 | Kolom wajib hilang | hanya `tanggal` | error menyebut `kategori` | test_missing_columns_reported |
| T4 | Baris tidak valid | tanggal/nilai/kategori rusak | dibuang + dilaporkan | test_invalid_rows_dropped_and_reported |
| T5 | KPI cocok hitungan manual | 4 baris | total 500, rata-rata 125 | test_kpis_manual_check |
| T6 | Filter konsisten KPI/grafik/ekspor | filter A, 1-2 Jan | semua = 300 | test_filters_consistent_across_components |
| T7 | Rentang tanggal terbalik | awal > akhir | error | test_invalid_date_range |
| T8 | Data kosong | filter tanpa hasil | grafik kosong + KPI None | test_kpis_empty, test_charts_... |
| T9 | Smoke aplikasi | data contoh / tanpa data | tanpa exception | test_app_smoke.py |
| T10 | Preset filter: simpan-muat, penyesuaian dilaporkan, preset rusak ditolak | JSON | roundtrip sama; catatan; ValueError | test_preset_* |
| T11 | Donut hanya bila <=6 kategori dan nilai positif; scatter disampel 5.000 titik | data | sesuai aturan | test_donut_only_for_few_categories, test_scatter_columns_and_sampling |
| T12 | Laporan PDF sesuai filter; kosong ditolak | KPI | `%PDF`, ValueError | test_pdf_report_valid_and_filter_dependent |
| T13 | Kebenaran pada 200.000 baris | acak seed 1 | total = hitungan langsung | test_pipeline_correct_on_large_dataset |
| T14 | Skenario tugas di browser (Playwright) | lihat HEURISTIC_EVALUATION.md | lolos | manual-otomatis, tidak ada di pytest |

Benchmark performa: `docs/PERFORMANCE.md`. Uji pengguna: belum dilakukan.
