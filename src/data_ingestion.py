"""Membaca dan memvalidasi dataset transaksi DataLens Analytics."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Any

import pandas as pd

REQUIRED_COLUMNS = ["tanggal", "kategori", "nilai"]
SUPPORTED_EXTENSIONS = (".csv", ".xlsx")
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


class DatasetError(ValueError):
    """Dataset tidak dapat dibaca atau tidak memenuhi skema; pesan aman ditampilkan ke pengguna."""


@dataclass
class ValidationReport:
    """Hasil validasi: error menghentikan analisis, warning hanya memberi tahu pengguna."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rows_total: int = 0
    rows_invalid_date: int = 0
    rows_invalid_value: int = 0
    rows_missing_category: int = 0

    @property
    def valid(self) -> bool:
        return not self.errors


def load_dataset(source: str | Path | IO[bytes], filename: str | None = None) -> pd.DataFrame:
    """Baca CSV/XLSX dari path atau objek file (mis. UploadedFile Streamlit).

    ``filename`` wajib bila ``source`` berupa objek file tanpa atribut ``name``.
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise DatasetError(f"File tidak ditemukan: {path}")
        name = path.name
        size = path.stat().st_size
        handle: Any = path
    else:
        name = filename or getattr(source, "name", "")
        size = getattr(source, "size", None)
        if size is None:
            size = len(source.getbuffer()) if hasattr(source, "getbuffer") else 0
        handle = source

    suffix = Path(name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise DatasetError(
            f"Format '{suffix or 'tanpa ekstensi'}' tidak didukung. Gunakan file CSV atau XLSX."
        )
    if size > MAX_UPLOAD_BYTES:
        raise DatasetError(
            f"Ukuran file {size / 1_048_576:.1f} MB melebihi batas {MAX_UPLOAD_BYTES // 1_048_576} MB."
        )

    try:
        frame = pd.read_csv(handle) if suffix == ".csv" else pd.read_excel(handle)
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        raise DatasetError(f"Isi file tidak dapat dibaca sebagai tabel: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - pesan ramah untuk berkas korup
        raise DatasetError(f"Gagal membaca file: {exc}") from exc

    if frame.empty:
        raise DatasetError("File tidak memiliki baris data.")
    frame.columns = [str(c).strip() for c in frame.columns]
    return frame


def validate_columns(df: pd.DataFrame, required_columns: list[str] | None = None) -> ValidationReport:
    """Periksa keberadaan kolom wajib (tanpa membedakan huruf besar/kecil)."""
    required = required_columns or REQUIRED_COLUMNS
    report = ValidationReport(rows_total=len(df))
    lower = {str(c).lower() for c in df.columns}
    missing = [c for c in required if c.lower() not in lower]
    if missing:
        report.errors.append(
            f"Kolom wajib tidak ditemukan: {', '.join(missing)}. "
            f"Kolom pada file: {', '.join(map(str, df.columns))}. "
            "Ganti nama kolom di file Anda agar sesuai dengan docs/DATA_DICTIONARY.md."
        )
    return report


def prepare_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, ValidationReport]:
    """Normalkan nama kolom, ubah tipe, dan buang baris yang tidak valid secara eksplisit.

    Baris dengan tanggal/nilai tidak valid dibuang dan jumlahnya dilaporkan;
    tidak ada perubahan diam-diam.
    """
    report = validate_columns(df)
    if not report.valid:
        return df, report

    working = df.copy()
    working.columns = [c.lower() if c.lower() in REQUIRED_COLUMNS else c for c in working.columns]

    dates = pd.to_datetime(working["tanggal"], errors="coerce")
    values = pd.to_numeric(working["nilai"], errors="coerce")
    category_missing = working["kategori"].isna() | (working["kategori"].astype(str).str.strip() == "")

    report.rows_invalid_date = int(dates.isna().sum())
    report.rows_invalid_value = int(values.isna().sum())
    report.rows_missing_category = int(category_missing.sum())

    keep = dates.notna() & values.notna() & ~category_missing
    dropped = int((~keep).sum())
    if dropped:
        parts = []
        if report.rows_invalid_date:
            parts.append(f"{report.rows_invalid_date} tanggal tidak valid")
        if report.rows_invalid_value:
            parts.append(f"{report.rows_invalid_value} nilai bukan angka")
        if report.rows_missing_category:
            parts.append(f"{report.rows_missing_category} kategori kosong")
        report.warnings.append(f"{dropped} baris dibuang dari analisis ({'; '.join(parts)}).")

    working["tanggal"] = dates
    working["nilai"] = values
    working["kategori"] = working["kategori"].astype(str).str.strip()
    working = working[keep].reset_index(drop=True)

    if working.empty:
        report.errors.append("Tidak ada baris valid setelah validasi tanggal, nilai, dan kategori.")
    elif (working["nilai"] < 0).any():
        report.warnings.append(
            f"{int((working['nilai'] < 0).sum())} baris bernilai negatif (mis. retur); tetap dihitung dalam total."
        )
    duplicates = int(working.duplicated().sum())
    if duplicates:
        report.warnings.append(f"{duplicates} baris duplikat terdeteksi; tidak dibuang otomatis.")
    return working, report
