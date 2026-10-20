# Evaluasi Heuristik (penilaian pengembang)

> **Bukan uji pengguna.** Ini penilaian internal terhadap 10 heuristik Nielsen (PRD bagian 5) oleh pembuat aplikasi, ditambah verifikasi skenario otomatis di browser. Hasilnya tidak menggantikan uji dengan peserta nyata (`USABILITY_TEST.md`) dan cenderung bias karena penilai adalah pembuat.

| Heuristik | Penerapan di aplikasi | Bukti | Celah yang diketahui |
|---|---|---|---|
| Visibility of system status | Spinner pemuatan, pesan sukses (jumlah baris valid), "Filter aktif" selalu tampil | `app.py` | Tidak ada indikator saat PDF dibuat (cepat: <0,5 dtk pada 1 juta baris) |
| Match with the real world | Istilah transaksi, kategori, nilai (Rp), "drill-down" dijelaskan | UI | Istilah "drill-down" teknis bagi pemula |
| User control and freedom | "Reset semua filter", preset filter dimuat/disimpan, drill-down dapat dikembalikan ke "(semua)" | skenario otomatis | Tidak ada undo bertahap |
| Consistency | Satu `apply_filters` untuk KPI, grafik, tabel, ekspor; satuan Rp seragam | `test_filters_consistent_across_components` | Format angka ribuan memakai koma (locale en) |
| Error prevention | Validasi rentang tanggal, batas ukuran/format file, kolom wajib dicek sebelum analisis | tes validasi | - |
| Recognition rather than recall | Filter aktif ditampilkan, definisi metrik di expander | UI | Preset harus diunduh/diunggah manual |
| Flexibility and efficiency | Pencarian, pengurutan, ukuran halaman, klik grafik untuk drill-down, preset | UI | Tidak ada pintasan keyboard khusus |
| Aesthetic and minimalist design | Dua grafik utama + donut/scatter hanya bila relevan | UI | - |
| Help users recover from errors | Pesan error menyebut kolom yang hilang dan merujuk `DATA_DICTIONARY.md`; empty state menyarankan reset | tes | Pesan masih dalam satu bahasa (Indonesia) |
| Help and documentation | Expander bantuan, README, data dictionary | - | Tidak ada tur interaktif |

## Verifikasi skenario tugas PRD secara otomatis (Playwright/Chromium, data contoh sintetis)
| Skenario | Hasil terukur |
|---|---|
| 1. Kategori dengan nilai tertinggi | Kartu KPI "Kategori teratas" = Elektronik (cocok dengan `test_kpis_manual_check` dan agregasi) |
| 2. Filter ke satu kategori | Jumlah transaksi 1.020 -> 213; total Rp 334.119.500 |
| 3. Rincian transaksi terkait | Tabel detail menampilkan baris kategori terpilih (selectbox drill-down; klik batang juga mengisi pilihan) |
| 4. Ekspor data terfilter | CSV terunduh berisi 213 baris, hanya kategori "Elektronik"; PDF terunduh valid (`%PDF-`) |
| Reset | KPI kembali ke 1.020 transaksi |
| Keyboard | Tombol Tab menjangkau skip-link, sidebar, unggah, toggle, tombol reset, input tanggal, dan pemilih kategori berurutan secara logis |

**Tidak diuji:** pembaca layar, kontras warna terukur, seluruh alur hanya dengan keyboard sampai ekspor, perangkat sentuh nyata. Tata letak ponsel (390 px) hanya diambil screenshot-nya (`screenshots/03_mobile.png`) dan belum dinilai oleh pengguna.
