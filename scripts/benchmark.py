"""Ukur waktu pipeline pada dataset besar. Hasil dicetak sebagai tabel Markdown (disalin ke docs/PERFORMANCE.md)."""

import io
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data_ingestion import load_dataset, prepare_dataframe  # noqa: E402
from src.export import pdf_report_bytes, to_csv_bytes  # noqa: E402
from src.filters import FilterState, apply_filters  # noqa: E402
from src.metrics import compute_kpis  # noqa: E402
from src.visualizations import aggregate_categories, aggregate_trend  # noqa: E402


def make(n: int) -> bytes:
    rng = np.random.default_rng(0)
    df = pd.DataFrame({
        "tanggal": pd.to_datetime("2024-01-01") + pd.to_timedelta(rng.integers(0, 365, n), unit="D"),
        "kategori": rng.choice(["A", "B", "C", "D", "E"], n),
        "nilai": rng.lognormal(10, 0.6, n).round(0),
        "wilayah": rng.choice(["X", "Y", "Z"], n),
    })
    return df.to_csv(index=False).encode()


def timed(fn):
    t = time.perf_counter()
    out = fn()
    return out, time.perf_counter() - t


print(f"Python {platform.python_version()}, pandas {pd.__version__}")
print("| Baris | CSV (MB) | muat+validasi (s) | filter (s) | KPI (s) | agregasi grafik (s) | CSV ekspor (s) | PDF (s) |\n|---|---|---|---|---|---|---|---|")
for n in (10_000, 100_000, 500_000, 1_000_000):
    raw = make(n)
    (frame, _), t_load = timed(lambda: prepare_dataframe(load_dataset(io.BytesIO(raw), filename="b.csv")))
    state = FilterState(frame["tanggal"].min().date(), frame["tanggal"].max().date(), ["A", "B"], "")
    filtered, t_filter = timed(lambda: apply_filters(frame, state))
    kpis, t_kpi = timed(lambda: compute_kpis(filtered))
    _, t_agg = timed(lambda: (aggregate_trend(filtered), aggregate_categories(filtered)))
    _, t_csv = timed(lambda: to_csv_bytes(filtered))
    _, t_pdf = timed(lambda: pdf_report_bytes(filtered, kpis, state.describe(), len(frame), "benchmark"))
    print(f"| {n:,} | {len(raw) / 1e6:.1f} | {t_load:.2f} | {t_filter:.2f} | {t_kpi:.3f} | {t_agg:.2f} | {t_csv:.2f} | {t_pdf:.2f} |")
