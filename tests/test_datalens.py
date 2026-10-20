import io
from datetime import date

import pandas as pd
import pytest

from src.data_ingestion import DatasetError, load_dataset, prepare_dataframe, validate_columns
from src.export import to_csv_bytes
from src.filters import FilterState, apply_date_filter, apply_filters, apply_search, validate_date_range
from src.metrics import compute_kpis
from src.table_view import paginate, sort_table
from src.usability import UsabilityResult, compute_summary, load_results, save_results
from src.visualizations import aggregate_categories, aggregate_trend, create_category_chart, create_trend_chart

CSV = (
    "tanggal,kategori,nilai\n"
    "2025-01-01,A,100\n2025-01-01,B,50\n2025-01-02,A,200\n2025-01-03,B,150\n"
)


@pytest.fixture
def frame():
    df, report = prepare_dataframe(pd.read_csv(io.StringIO(CSV)))
    assert report.valid
    return df


def test_load_from_filelike_and_path(tmp_path):
    buf = io.BytesIO(CSV.encode())
    assert len(load_dataset(buf, filename="x.csv")) == 4
    p = tmp_path / "x.csv"
    p.write_text(CSV)
    assert len(load_dataset(p)) == 4


def test_load_rejects_bad_format_and_empty(tmp_path):
    with pytest.raises(DatasetError):
        load_dataset(io.BytesIO(b"abc"), filename="x.txt")
    with pytest.raises(DatasetError):
        load_dataset(io.BytesIO(b"tanggal,kategori,nilai\n"), filename="x.csv")
    with pytest.raises(DatasetError):
        load_dataset(tmp_path / "tidak_ada.csv")


def test_missing_columns_reported():
    report = validate_columns(pd.DataFrame({"tanggal": [1]}))
    assert not report.valid and "kategori" in report.errors[0]


def test_invalid_rows_dropped_and_reported():
    raw = pd.DataFrame({"Tanggal": ["2025-01-01", "bukan", "2025-01-03"], "kategori": ["A", "A", None],
                        "nilai": ["10", "5", "x"]})
    df, report = prepare_dataframe(raw)
    assert len(df) == 1 and report.rows_invalid_date == 1 and report.rows_invalid_value == 1
    assert report.rows_missing_category == 1 and report.warnings


def test_all_invalid_gives_error():
    raw = pd.DataFrame({"tanggal": ["x"], "kategori": ["A"], "nilai": [1]})
    _, report = prepare_dataframe(raw)
    assert not report.valid


def test_kpis_manual_check(frame):
    k = compute_kpis(frame)
    assert k["total_transactions"] == 4 and k["total_value"] == 500 and k["average_value"] == 125
    assert k["top_category"] == "A" and k["top_category_value"] == 300


def test_kpis_empty(frame):
    k = compute_kpis(frame.iloc[0:0])
    assert k["total_transactions"] == 0 and k["total_value"] is None


def test_date_filter_inclusive_and_source_untouched(frame):
    before = frame.copy()
    out = apply_date_filter(frame, "tanggal", date(2025, 1, 2), date(2025, 1, 3))
    assert len(out) == 2
    pd.testing.assert_frame_equal(frame, before)


def test_invalid_date_range():
    assert validate_date_range(date(2025, 2, 1), date(2025, 1, 1))
    with pytest.raises(ValueError):
        apply_date_filter(pd.DataFrame({"tanggal": []}), "tanggal", date(2025, 2, 1), date(2025, 1, 1))


def test_filters_consistent_across_components(frame):
    state = FilterState(date(2025, 1, 1), date(2025, 1, 2), ["A"])
    out = apply_filters(frame, state)
    assert compute_kpis(out)["total_value"] == 300
    assert aggregate_trend(out)["nilai"].sum() == 300
    assert aggregate_categories(out)["nilai"].sum() == 300
    assert to_csv_bytes(out).decode().count("\n") == len(out) + 1


def test_search_and_empty_category_means_all(frame):
    assert len(apply_search(frame, "b")) == 2
    assert len(apply_filters(frame, FilterState(date(2025, 1, 1), date(2025, 1, 3)))) == 4


def test_trend_fills_missing_days():
    df = pd.DataFrame({"tanggal": pd.to_datetime(["2025-01-01", "2025-01-03"]), "nilai": [1, 2], "kategori": "A"})
    trend = aggregate_trend(df)
    assert len(trend) == 3 and trend["nilai"].tolist() == [1, 0, 2]


def test_charts_have_titles_and_handle_empty(frame):
    assert create_trend_chart(frame).layout.title.text
    assert create_category_chart(frame).layout.yaxis.title.text
    assert create_trend_chart(frame.iloc[0:0]).layout.annotations


def test_sort_and_paginate(frame):
    assert sort_table(frame, "nilai", False)["nilai"].iloc[0] == 200
    page, pages = paginate(frame, 99, 3)
    assert pages == 2 and len(page) == 1
    with pytest.raises(KeyError):
        sort_table(frame, "x")


def test_usability_roundtrip(tmp_path):
    rs = [UsabilityResult("P1", "T1", True, 30, 0), UsabilityResult("P2", "T1", False, 90, 2, "bingung")]
    save_results(rs, tmp_path / "r.csv")
    loaded = load_results(tmp_path / "r.csv")
    assert loaded == rs
    s = compute_summary(loaded)
    assert s["task_completion_rate_pct"] == 50.0 and s["total_participants"] == 2
    assert compute_summary([])["total_participants"] == 0


# ---------- P1/P2: preset, donut, scatter, PDF, skala ----------
from src.export import pdf_report_bytes
from src.filters import preset_from_json, preset_to_json
from src.visualizations import MAX_SCATTER_POINTS, create_scatter_chart, create_share_chart, numeric_extra_columns


def test_preset_roundtrip(frame):
    state = FilterState(date(2025, 1, 2), date(2025, 1, 3), ["A"], "x")
    loaded, freq, notes = preset_from_json(preset_to_json(state, "Mingguan"), ["A", "B"], date(2025, 1, 1), date(2025, 1, 3))
    assert (loaded.start_date, loaded.end_date, loaded.categories, loaded.search, freq) == (date(2025, 1, 2), date(2025, 1, 3), ["A"], "x", "Mingguan")
    assert notes == []


def test_preset_adjustments_are_reported_not_silent():
    text = preset_to_json(FilterState(date(2020, 1, 1), date(2030, 1, 1), ["A", "ZZZ"], ""))
    loaded, _, notes = preset_from_json(text, ["A"], date(2025, 1, 1), date(2025, 6, 30))
    assert loaded.categories == ["A"] and (loaded.start_date, loaded.end_date) == (date(2025, 1, 1), date(2025, 6, 30))
    assert len(notes) == 2


def test_preset_invalid_inputs_rejected():
    for bad in ("bukan json", '{"start_date": "tanggal-salah"}', "[]"):
        with pytest.raises(ValueError):
            preset_from_json(bad, ["A"], date(2025, 1, 1), date(2025, 1, 2))
    far = preset_to_json(FilterState(date(2030, 1, 1), date(2031, 1, 1), [], ""))
    with pytest.raises(ValueError):
        preset_from_json(far, ["A"], date(2025, 1, 1), date(2025, 1, 2))


def test_empty_preset_means_defaults():
    loaded, freq, notes = preset_from_json("{}", ["A"], date(2025, 1, 1), date(2025, 1, 9))
    assert (loaded.start_date, loaded.end_date, loaded.categories, freq, notes) == (date(2025, 1, 1), date(2025, 1, 9), [], "Harian", [])


def test_donut_only_for_few_categories(frame):
    assert create_share_chart(frame) is not None
    many = pd.DataFrame({"tanggal": pd.Timestamp("2025-01-01"), "kategori": list("ABCDEFGH"), "nilai": 1.0})
    assert create_share_chart(many) is None  # 8 kategori > 6
    assert create_share_chart(frame.iloc[0:0]) is None
    neg = frame.assign(nilai=-frame["nilai"])
    assert create_share_chart(neg) is None  # proporsi tidak bermakna untuk nilai negatif


def test_scatter_columns_and_sampling():
    big = pd.DataFrame({"tanggal": pd.Timestamp("2025-01-01"), "kategori": "A", "nilai": range(MAX_SCATTER_POINTS + 500), "jumlah": 1.0})
    assert numeric_extra_columns(big) == ["jumlah"]
    fig = create_scatter_chart(big, "jumlah")
    assert sum(len(t.x) for t in fig.data) == MAX_SCATTER_POINTS and "sampel" in fig.layout.title.text
    with pytest.raises(ValueError):
        create_scatter_chart(big, "nilai")


def test_pdf_report_valid_and_filter_dependent(frame):
    kpis = compute_kpis(frame)
    pdf = pdf_report_bytes(frame, kpis, ["Kategori: semua"], len(frame), "uji.csv", synthetic=True)
    assert pdf.startswith(b"%PDF") and len(pdf) > 2000
    with pytest.raises(ValueError):
        pdf_report_bytes(frame.iloc[0:0], kpis, [], 4, "x")


def test_pipeline_correct_on_large_dataset():
    import numpy as np
    n = 200_000
    rng = np.random.default_rng(1)
    raw = pd.DataFrame({"tanggal": pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 100, n), unit="D"),
                        "kategori": rng.choice(["A", "B"], n), "nilai": rng.integers(1, 1000, n).astype(float)})
    df, report = prepare_dataframe(raw)
    assert report.valid and len(df) == n
    out = apply_filters(df, FilterState(date(2025, 1, 1), date(2025, 4, 10), ["A"], ""))
    expected = raw[raw["kategori"] == "A"]["nilai"].sum()
    assert compute_kpis(out)["total_value"] == expected
    assert aggregate_categories(out)["nilai"].sum() == expected
