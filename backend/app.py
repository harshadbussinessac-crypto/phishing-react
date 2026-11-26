"""Flask API serving the trained scikit-learn phishing classifier.

Endpoints
  GET  /api/health    -> service + model status
  GET  /api/metrics   -> evaluation metrics saved by train_model.py
  POST /api/predict   -> {"text": "..."} -> label, probability, URL stats
"""
import json
import logging
import os
from pathlib import Path

import joblib
from flask import Flask, jsonify, request
from flask_cors import CORS

from features import extract_urls, url_features

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = Path(os.environ.get("MODEL_PATH", BASE_DIR / "model.joblib"))
METRICS_PATH = Path(os.environ.get("METRICS_PATH", BASE_DIR / "metrics.json"))
MAX_TEXT_CHARS = int(os.environ.get("MAX_TEXT_CHARS", 20000))
THRESHOLD = float(os.environ.get("PHISHING_THRESHOLD", 0.5))
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("phishing-api")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # reject bodies over 64 KB
CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})


def load_model():
    if not MODEL_PATH.exists():
        log.warning("Model file not found at %s. Run train_model.py first.", MODEL_PATH)
        return None
    log.info("Loading model from %s", MODEL_PATH)
    return joblib.load(MODEL_PATH)


def load_metrics():
    if not METRICS_PATH.exists():
        return None
    with open(METRICS_PATH, encoding="utf-8") as f:
        return json.load(f)


MODEL = load_model()
METRICS = load_metrics()


def error(message, status):
    return jsonify({"error": message}), status


@app.errorhandler(413)
def too_large(_):
    return error("Request body too large", 413)


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "model_loaded": MODEL is not None,
        "metrics_loaded": METRICS is not None,
        "threshold": THRESHOLD,
    })


@app.get("/api/metrics")
def metrics():
    if METRICS is None:
        return error("Metrics not found. Run train_model.py first.", 404)
    return jsonify(METRICS)


@app.post("/api/predict")
def predict():
    if MODEL is None:
        return error("Model not loaded. Run train_model.py first.", 503)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error("Request body must be a JSON object", 400)

    text = data.get("text")
    if not isinstance(text, str):
        return error("'text' must be a string", 400)
    text = text.strip()
    if not text:
        return error("Email text is required", 400)
    if len(text) > MAX_TEXT_CHARS:
        return error(f"Email text exceeds {MAX_TEXT_CHARS} characters", 413)

    try:
        proba = float(MODEL.predict_proba([text])[0][1])
    except Exception:
        log.exception("Prediction failed")
        return error("Prediction failed", 500)

    label = "Phishing" if proba >= THRESHOLD else "Safe"
    u = url_features(text)
    return jsonify({
        "label": label,
        "phishing_probability": round(proba, 4),
        "threshold": THRESHOLD,
        "urls_found": extract_urls(text),
        "url_stats": {
            "count": u[0],
            "shortened": u[1],
            "ip_address_links": u[2],
            "suspicious_domain": u[3],
            "non_https": u[4],
        },
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
