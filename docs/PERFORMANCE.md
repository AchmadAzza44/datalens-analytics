# Uji Performa (dataset besar)

Dijalankan dengan `python scripts/benchmark.py` (Python 3.13, pandas 3.0.5, CPU 4 inti, data sintetis acak seed 0; waktu = sekali jalan, bukan rata-rata, sehingga bervariasi antar mesin).

| Baris | CSV (MB) | muat+validasi (s) | filter (s) | KPI (s) | agregasi grafik (s) | CSV ekspor (s) | PDF (s) |
|---|---|---|---|---|---|---|---|
| 10.000 | 0,2 | 0,04 | 0,01 | 0,004 | 0,01 | 0,01 | 0,27 |
| 100.000 | 2,3 | 0,13 | 0,03 | 0,003 | 0,01 | 0,05 | 0,24 |
| 500.000 | 11,5 | 0,47 | 0,20 | 0,009 | 0,05 | 0,30 | 0,36 |
| 1.000.000 | 22,9 | 1,24 | 0,29 | 0,021 | 0,14 | 0,87 | 0,48 |

**Kesimpulan yang didukung angka:** pipeline data (muat, validasi, filter, KPI, agregasi, ekspor) tetap di bawah ~1,5 detik pada 1 juta baris. Batas unggah 50 MB menahan ukuran file jauh di bawah titik ini.
**Batasan:** angka ini tidak mencakup waktu render browser. Grafik tren/kategori dikirim dalam bentuk agregat (kecil); scatter dibatasi sampel 5.000 titik (dinyatakan di judul grafik) agar browser tidak menerima jutaan titik; tabel detail hanya mengirim satu halaman. Seluruh data dimuat ke memori, sehingga file jauh lebih besar dari 1 juta baris perlu backend/database (PRD P2, belum ada). Kebenaran hasil pada 200.000 baris diverifikasi terhadap hitungan langsung di `test_pipeline_correct_on_large_dataset`.
