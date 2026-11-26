# Phishing Email Detector

A professional React and Flask phishing-email detection application built with scikit-learn.

## Features

- Machine-learning phishing classification
- URL and text feature analysis
- Precision, recall, accuracy, F1-score, and confusion matrix
- Responsive security dashboard UI
- Flask REST API with health and metrics endpoints

## Run locally

### Backend

```powershell
cd backend
pip install -r requirements.txt
python train_model.py
python app.py
```

The API runs at `http://127.0.0.1:5000`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The UI runs at `http://localhost:5173`.

## API

- `GET /api/health`
- `GET /api/metrics`
- `POST /api/predict`
