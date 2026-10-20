# DataLens Analytics

Dashboard Analitik Interaktif Berbasis Prinsip HCI.

## Deskripsi

DataLens Analytics adalah dashboard untuk mengubah data transaksi menjadi informasi
yang mudah dipahami. Pengguna dapat melihat ringkasan KPI, menyaring data,
membandingkan kategori, menelusuri rincian, dan mengekspor laporan.

Produk dirancang menggunakan prinsip HCI: kebutuhan pengguna, konsistensi,
feedback, pencegahan kesalahan, aksesibilitas, dan evaluasi usability.

## Fitur MVP

- Memuat dataset dengan kolom yang terdokumentasi.
- Validasi kolom wajib, tipe data, nilai kosong, dan format tanggal.
- KPI dasar seperti total transaksi, total nilai, dan nilai rata-rata.
- Minimal satu grafik tren dan satu grafik perbandingan kategori.
- Filter tanggal dan kategori yang memperbarui seluruh komponen terkait.
- Tabel detail yang sesuai dengan filter.
- Feedback ketika data sedang dimuat, kosong, atau tidak valid.
- Ekspor data hasil filter ke CSV dan laporan PDF; preset filter (simpan/muat JSON); drill-down dengan klik grafik; donut proporsi dan scatter bila relevan.

## Struktur folder
```text
app.py                # titik masuk Streamlit
src/                  # data_ingestion, filters, metrics, visualizations, table_view, export, usability
data/sample/          # transaksi_contoh_sintetis.csv (SINTETIS)
scripts/              # generate_sample.py, benchmark.py
tests/                # 25 tes pytest
docs/                 # DATA_DICTIONARY, ARCHITECTURE, PERSONA_AND_SCENARIOS, USABILITY_TEST, HEURISTIC_EVALUATION, PERFORMANCE, TEST_PLAN, PROGRESS, LAPORAN, screenshots/
.streamlit/           # config (batas unggah 50 MB)
```

## Prasyarat

- Python 3.10+
- Streamlit, Pandas, Plotly, OpenPyXL

## Instalasi

```powershell
pip install -r requirements.txt
```

## Menjalankan Aplikasi

```powershell
python -m streamlit run app.py
```

## Contoh Penggunaan

1. Unggah CSV/XLSX (kolom wajib: `tanggal`, `kategori`, `nilai`) atau pakai data contoh sintetis (`data/sample/`).
2. Atur filter tanggal, kategori, dan pencarian di sidebar; "Reset semua filter" mengembalikan tampilan awal.
3. KPI, grafik, tabel (urut + halaman + drill-down), dan ekspor memakai filter yang sama.
4. Unduh CSV sesuai filter aktif.

## Pengujian

```bash
python -m pytest -q
```

Rencana uji: `docs/TEST_PLAN.md` (25 tes). Performa 1 juta baris: `docs/PERFORMANCE.md`. Evaluasi heuristik: `docs/HEURISTIC_EVALUATION.md`. Uji usability dengan peserta nyata **belum dilakukan** (`docs/USABILITY_TEST.md`). Laporan: `docs/LAPORAN.md`.

## Prinsip HCI

Fitur HCI yang benar-benar ada: status loading/sukses/error, filter aktif ditampilkan, reset filter, validasi rentang tanggal, empty state, bantuan definisi metrik, sumbu mulai dari nol, judul/satuan/periode/sumber pada grafik. Persona dan skenario: `docs/PERSONA_AND_SCENARIOS.md`.
