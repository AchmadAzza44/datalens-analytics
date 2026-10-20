# Laporan Singkat - DataLens Analytics
**Materi kuliah:** Human-Computer Interaction (HCI) dan Data Visualization. PRD: `docs/PRD_Tiga_Implementasi_Informatika.md` (root repo), PRD 3.

## Masalah dan tujuan
Tabel transaksi panjang sulit dibaca. DataLens mengubahnya menjadi KPI, grafik, dan tabel yang dapat difilter, dirancang dengan prinsip HCI dan dievaluasi melalui skenario tugas.

## Hubungan fitur dengan materi
| Konsep materi | Implementasi | Bukti |
|---|---|---|
| Visibility of system status | spinner, pesan sukses, "Filter aktif" | `app.py`, screenshot 01 |
| User control and freedom | reset filter, preset filter, drill-down dapat dibatalkan | skenario otomatis |
| Error prevention / recover from errors | validasi tanggal/format/kolom; pesan menyebut solusi | `tests/test_datalens.py` |
| Consistency | satu `apply_filters` untuk KPI-grafik-tabel-ekspor | `test_filters_consistent_across_components` |
| Recognition rather than recall | filter aktif + definisi metrik terlihat | UI |
| Visualisasi: line untuk tren, bar untuk kategori, donut hanya <=6 kategori, scatter untuk dua variabel numerik, sumbu mulai dari nol, judul/satuan/periode/sumber | `src/visualizations.py` | screenshot 01 |
| Overview first, zoom and filter, details on demand | KPI+grafik -> filter -> tabel + drill-down | UI |

## Hasil pengujian (nyata)
- 25 tes pytest lulus; hitungan KPI dicocokkan dengan perhitungan manual pada sampel kecil dan dengan perhitungan langsung pada 200.000 baris.
- Performa 1 juta baris: pipeline < 1,5 dtk (`PERFORMANCE.md`).
- Skenario tugas PRD lolos di Chromium otomatis, ekspor CSV konsisten dengan filter (213 baris pada contoh).
- **Uji usability dengan peserta nyata belum dilakukan**; evaluasi heuristik adalah penilaian pengembang sehingga bias.

## Keterbatasan
Data contoh sintetis (bukan bisnis nyata). Persona belum divalidasi wawancara. Backend/DB/autentikasi tidak dibangun (PRD P2 bersyarat). Aksesibilitas baru diuji sebatas navigasi Tab, belum dengan pembaca layar.

## Demonstrasi
`python -m streamlit run app.py` -> aktifkan data contoh -> filter kategori -> lihat KPI dan tabel -> klik batang untuk drill-down -> unduh CSV/PDF.
