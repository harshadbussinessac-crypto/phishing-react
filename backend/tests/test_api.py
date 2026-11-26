"""Basic API and feature tests. Run from the backend folder: pytest -q"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from features import extract_urls, url_features  # noqa: E402


def test_extract_urls_finds_http_and_www():
    urls = extract_urls("Visit http://a.com/x and www.b.org.")
    assert "http://a.com/x" in urls
    assert "www.b.org" in urls


def test_ip_and_shortener_detected():
    f = url_features("go to http://192.168.1.5/login or http://bit.ly/abc")
    assert f[0] == 2  # count
    assert f[1] == 1  # shortened
    assert f[2] == 1  # ip links


def test_no_urls_gives_zero_vector():
    assert url_features("plain text, no links")[:5] == [0, 0, 0, 0, 0]


@pytest.fixture
def client(monkeypatch):
    import app as app_module
    monkeypatch.setattr(app_module, "MODEL", None)
    monkeypatch.setattr(app_module, "METRICS", None)
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def test_health_reports_missing_model(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json()["model_loaded"] is False


def test_predict_without_model_returns_503(client):
    r = client.post("/api/predict", json={"text": "hello"})
    assert r.status_code == 503


def test_predict_validates_input(client, monkeypatch):
    import app as app_module

    class Dummy:
        def predict_proba(self, X):
            return [[0.2, 0.8]]

    monkeypatch.setattr(app_module, "MODEL", Dummy())
    assert client.post("/api/predict", data="not json", content_type="text/plain").status_code == 400
    assert client.post("/api/predict", json={"text": 5}).status_code == 400
    assert client.post("/api/predict", json={"text": "   "}).status_code == 400


def test_predict_returns_label(client, monkeypatch):
    import app as app_module

    class Dummy:
        def predict_proba(self, X):
            return [[0.1, 0.9]]

    monkeypatch.setattr(app_module, "MODEL", Dummy())
    r = client.post("/api/predict", json={"text": "verify now http://bit.ly/x"})
    body = r.get_json()
    assert r.status_code == 200
    assert body["label"] == "Phishing"
    assert body["url_stats"]["shortened"] == 1
