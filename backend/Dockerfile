FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .
# Train at build time so model.joblib and metrics.json exist in the image
RUN python train_model.py data/emails.csv

ENV CORS_ORIGINS=http://localhost:5173,http://localhost:8080
EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
