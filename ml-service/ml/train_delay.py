import pandas as pd
import numpy as np
import os
joblib = __import__('joblib')
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

def train_pipeline():
    print(" Loading data and stripping leaks...")
    df = pd.read_csv("data/flight_delay_clean.csv")
    df["high_delay"] = (df["delay_rate"] > 0.20).astype(int)
    target_col = "high_delay"
    leak_cols = ["arr_del15", "delay_rate", "cancellation_rate", "diversion_rate", "carrier_ct_share", "weather_ct_share", "nas_ct_share", "security_ct_share", "late_aircraft_ct_share"]
    X = df.select_dtypes(include=[np.number]).drop(columns=[target_col] + leak_cols, errors="ignore")
    y = df[target_col].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    print(f"Training cleanly on {X_train.shape[0]} samples...")
    model = XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, eval_metric="logloss")
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]
    print("\n=== Realistic Evaluation Metrics ===")
    print(classification_report(y_test, preds))
    print("ROC-AUC Score: " + str(round(roc_auc_score(y_test, probs), 4)))
    os.makedirs("saved_models", exist_ok=True)
    joblib.dump(model, "saved_models/delay_model_v1.pkl")
    print("\n[SUCCESS] Honest, leak-free model saved!")

if __name__ == "__main__":
    train_pipeline()