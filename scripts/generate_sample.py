"""Buat data transaksi SINTETIS deterministik. Bukan data bisnis nyata."""

from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
categories = {"Elektronik": 1_500_000, "Pakaian": 350_000, "Makanan": 90_000, "Buku": 120_000, "Peralatan Rumah": 450_000}
rows = []
for i, day in enumerate(pd.date_range("2025-01-01", "2025-06-30", freq="D")):
    for _ in range(rng.integers(3, 9)):
        cat = rng.choice(list(categories))
        value = round(float(rng.lognormal(0, 0.35) * categories[cat]), -2)
        rows.append({"id_transaksi": f"TRX{len(rows) + 1:05d}", "tanggal": day.date().isoformat(), "kategori": cat,
                     "wilayah": rng.choice(["Bengkulu", "Padang", "Jambi"]), "nilai": value})
out = Path(__file__).resolve().parents[1] / "data" / "sample" / "transaksi_contoh_sintetis.csv"
out.parent.mkdir(parents=True, exist_ok=True)
pd.DataFrame(rows).to_csv(out, index=False)
print(f"Ditulis {len(rows)} baris ke {out}")
