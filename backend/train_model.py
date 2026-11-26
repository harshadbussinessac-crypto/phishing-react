"""Train the phishing classifier and save model + honest metrics.

Usage (from backend/):
  python generate_dataset.py                      # creates data/emails_generated.csv
  python train_model.py                           # uses data/emails_generated.csv
  python train_model.py data/emails.csv           # the small demo file

CSV columns: text,label   (label: 1 = phishing, 0 = safe)

Evaluation:
  - 5-fold stratified cross-validation: every email is predicted by a model
    that never saw it. Accuracy, precision, recall, F1, and the confusion
    matrix come from these out-of-fold predictions.
  - A 25% held-out split, reported separately as a final check.
  - The saved model.joblib is trained on the 75% split.
"""
import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             f1_score, precision_score, recall_score)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import StandardScaler

from features import EmailFeatures, TextTfidf

BASE = Path(__file__).resolve().parent
csv_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/emails_generated.csv")
csv_path = csv_arg if csv_arg.is_absolute() else BASE / csv_arg

df = pd.read_csv(csv_path).dropna(subset=["text", "label"])
df["text"] = df["text"].astype(str)
X, y = df["text"], df["label"].astype(int)
print(f"Loaded {len(df)} emails from {csv_path.name} "
      f"({(y == 1).sum()} phishing, {(y == 0).sum()} safe)")


def build_model():
    features = FeatureUnion([
        ("text", TextTfidf()),
        ("structured", Pipeline([("hand", EmailFeatures()), ("scale", StandardScaler())])),
    ])
    return Pipeline([
        ("features", features),
        ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", C=2.0)),
    ])


n_splits = min(5, int(y.value_counts().min()))
cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
oof_pred = cross_val_predict(build_model(), X, y, cv=cv)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42)
holdout_model = build_model().fit(X_train, y_train)
holdout_pred = holdout_model.predict(X_test)

metrics = {
    "dataset": csv_path.name,
    "n_emails": int(len(df)),
    "evaluation": f"{n_splits}-fold stratified cross-validation (out-of-fold predictions)",
    "accuracy": round(accuracy_score(y, oof_pred), 4),
    "precision": round(precision_score(y, oof_pred), 4),
    "recall": round(recall_score(y, oof_pred), 4),
    "f1": round(f1_score(y, oof_pred), 4),
    "confusion_matrix": confusion_matrix(y, oof_pred).tolist(),  # [[TN, FP], [FN, TP]]
    "labels": ["Safe", "Phishing"],
    "holdout": {
        "test_size": int(len(X_test)),
        "accuracy": round(accuracy_score(y_test, holdout_pred), 4),
        "f1": round(f1_score(y_test, holdout_pred), 4),
        "confusion_matrix": confusion_matrix(y_test, holdout_pred).tolist(),
    },
}

print(json.dumps(metrics, indent=2))
print(classification_report(y, oof_pred, target_names=["Safe", "Phishing"]))

final_model = build_model().fit(X_train, y_train)
joblib.dump(final_model, BASE / "model.joblib")
with open(BASE / "metrics.json", "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)
print("Saved model.joblib and metrics.json")
