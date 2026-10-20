from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def test_app_runs_with_sample_data():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    labels = [m.label for m in at.metric]
    assert "Jumlah transaksi" in labels and "Total nilai (Rp)" in labels


def test_app_without_data_shows_info():
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    at.sidebar.toggle[0].set_value(False).run()
    assert not at.exception
    assert any("Unggah file" in i.value for i in at.info)
