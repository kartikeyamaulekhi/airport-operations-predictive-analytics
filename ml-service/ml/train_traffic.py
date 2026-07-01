"""
ml/train_traffic.py
Phase 2A: Train a Prophet time-series model to forecast daily airport
passenger footfall. Follows the identical save/load pattern as train_delay.py
so the FastAPI service can load both models the same way.

Run from ml-service/ with venv activated:
    python ml/train_traffic.py
"""

import pandas as pd
import numpy as np
import os
import json
import joblib
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from app.config import Config


def train_pipeline():
    # ------------------------------------------------------------------
    # 1. Load data
    # ------------------------------------------------------------------
    print("[INFO] Loading traffic data...")
    df = pd.read_csv(Config.TRAFFIC_DATA_PATH)

    # Prophet requires exactly two columns: ds (datestamp) and y (value)
    df = df.rename(columns={"date": "ds", "passenger_footfall": "y"})
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values("ds").reset_index(drop=True)

    print(f"[INFO] Loaded {len(df)} daily records: "
          f"{df['ds'].min().date()} to {df['ds'].max().date()}")
    print(f"[INFO] Footfall range: {df['y'].min():,} – {df['y'].max():,}")

    # ------------------------------------------------------------------
    # 2. Train / test split (last 90 days held out for evaluation)
    # ------------------------------------------------------------------
    holdout_days = 90
    train_df = df.iloc[:-holdout_days].copy()
    test_df  = df.iloc[-holdout_days:].copy()
    print(f"[INFO] Train: {len(train_df)} rows | Test (holdout): {len(test_df)} rows")

    # ------------------------------------------------------------------
    # 3. Build and fit Prophet model
    # ------------------------------------------------------------------
    print("[INFO] Fitting Prophet model...")
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,      # daily granularity but no sub-daily pattern
        seasonality_mode="multiplicative",  # better for growing traffic data
        changepoint_prior_scale=0.05,       # conservative: avoids overfitting trend
        seasonality_prior_scale=10.0,
        interval_width=0.95,
    )

    # Add Indian/US holiday effects manually as extra regressors via
    # built-in country holidays. Use US since the training data is US DOT.
    model.add_country_holidays(country_name="US")

    model.fit(train_df)
    print("[INFO] Prophet model fitted successfully.")

    # ------------------------------------------------------------------
    # 4. Evaluate on holdout set
    # ------------------------------------------------------------------
    future_test = model.make_future_dataframe(periods=holdout_days, freq="D")
    forecast    = model.predict(future_test)
    test_forecast = forecast.tail(holdout_days).copy()

    y_true = test_df["y"].values
    y_pred = test_forecast["yhat"].values

    mae  = mean_absolute_error(y_true, y_pred)
    mape = mean_absolute_percentage_error(y_true, y_pred) * 100

    print("\n=== Prophet Evaluation (90-day holdout) ===")
    print(f"  MAE  (Mean Absolute Error):      {mae:,.0f} passengers/day")
    print(f"  MAPE (Mean Abs % Error):          {mape:.2f}%")
    print(f"  Baseline mean footfall:           {y_true.mean():,.0f}/day")

    # ------------------------------------------------------------------
    # 5. Refit on full data for production use
    # ------------------------------------------------------------------
    print("\n[INFO] Refitting on full dataset for production...")
    model_prod = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode="multiplicative",
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10.0,
        interval_width=0.95,
    )
    model_prod.add_country_holidays(country_name="US")
    model_prod.fit(df)

    # ------------------------------------------------------------------
    # 6. Save model and metadata
    # ------------------------------------------------------------------
    os.makedirs(os.path.dirname(Config.TRAFFIC_MODEL_PATH), exist_ok=True)
    joblib.dump(model_prod, Config.TRAFFIC_MODEL_PATH)

    # Save evaluation metadata alongside the model (used by API /health endpoint)
    meta = {
        "mae":            round(float(mae), 2),
        "mape_pct":       round(float(mape), 4),
        "train_rows":     len(df),
        "holdout_days":   holdout_days,
        "date_min":       str(df["ds"].min().date()),
        "date_max":       str(df["ds"].max().date()),
        "model_version":  Config.MODEL_VERSION,
    }
    meta_path = Config.TRAFFIC_MODEL_PATH.replace(".pkl", "_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\n[SUCCESS] Traffic model saved to {Config.TRAFFIC_MODEL_PATH}")
    print(f"[SUCCESS] Metadata saved to {meta_path}")
    return meta


if __name__ == "__main__":
    train_pipeline()
