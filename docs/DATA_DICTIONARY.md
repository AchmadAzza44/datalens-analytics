# Data Dictionary

## Kolom
| Kolom | Wajib | Tipe | Deskripsi | Contoh |
|---|---|---|---|---|
| tanggal | ya | tanggal | Tanggal transaksi (ISO `YYYY-MM-DD` disarankan) | 2025-01-15 |
| kategori | ya | teks | Kategori produk/layanan | Elektronik |
| nilai | ya | angka | Nilai transaksi dalam Rupiah | 150000 |
| id_transaksi, wilayah, dst. | tidak | bebas | Ikut tampil di tabel dan dapat dicari | TRX00001 |

Nama kolom wajib tidak peka huruf besar/kecil.

## Aturan validasi
- Format selain CSV/XLSX ditolak; ukuran maksimum 50 MB; file tanpa baris ditolak.
- Baris dengan tanggal tidak terbaca, nilai bukan angka, atau kategori kosong **dibuang dan jumlahnya ditampilkan** sebagai peringatan.
- Nilai negatif (mis. retur) dan baris duplikat hanya diberi peringatan; tidak diubah otomatis.

## Definisi KPI
| KPI | Rumus |
|---|---|
| Jumlah transaksi | COUNT(baris terfilter) |
| Total nilai | SUM(nilai) |
| Rata-rata per transaksi | SUM(nilai) / COUNT(baris) |
| Kategori teratas | kategori dengan SUM(nilai) terbesar |

Pada data kosong, KPI bernilai "tidak terdefinisi", bukan 0.

## Dataset contoh
`data/sample/transaksi_contoh_sintetis.csv` dibuat oleh `scripts/generate_sample.py` (seed tetap, 1.020 baris, Jan-Jun 2025). **Data SINTETIS, bukan data bisnis nyata.**
