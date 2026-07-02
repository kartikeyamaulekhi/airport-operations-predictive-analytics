"""
ml/train_traffic.py
Phase 2A: Train a Prophet time-series model to forecast daily airport
passenger footfall. Extends training data to today so forecasts always
start from the current date, not the end of the historical dataset.

Run from ml-service/ with venv activated:
    python ml/train_traffic.py
"""

import pandas as pd
import numpy as np
import os
import json
import joblib
from datetime import date
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from app.config import Config


def extend_to_today(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extends the training dataframe to today's date by extrapolating
    the existing trend. This ensures Prophet forecasts always start
    from today, not from the end of the historical dataset.
    """
    last_date = df["ds"].max()
    today = pd.Timestamp(date.today())

    if last_date >= today:
        return df  # already up to date

    # Generate missing dates
    missing_dates = pd.date_range(
        start=last_date + pd.Timedelta(days=1),
        end=today,
        freq="D"
    )

    if len(missing_dates) == 0:
        return df

    # Extrapolate using the last 90 days average daily change (trend)
    recent = df.tail(90)
    avg_daily_change = (recent["y"].iloc[-1] - recent["y"].iloc[0]) / len(recent)
    last_value = df["y"].iloc[-1]

    extra_rows = []
    for i, d in enumerate(missing_dates):
        dow = d.dayofweek
        weekly_effect = {
            0: -600, 1: -1400, 2: -900, 3: 300,
            4: 2100, 5: 900,  6: 1700
        }[dow]
        seasonal = (3500 if d.month in [6, 7, 8] else 0) + \
                   (4200 if (d.month == 12 and d.day >= 15) else 0)
        trend = last_value + (i + 1) * avg_daily_change
        noise = np.random.normal(0, 500)
        footfall = max(5000, trend + weekly_effect + seasonal + noise)
        extra_rows.append({"ds": d, "y": int(footfall)})

    extra_df = pd.DataFrame(extra_rows)
    extended = pd.concat([df, extra_df], ignore_index=True)
    print(f"[INFO] Extended training data from {last_date.date()} "
          f"to {today} (+{len(missing_dates)} days)")
    return extended


def train_pipeline():
    # ------------------------------------------------------------------
    # 1. Load data
    # ------------------------------------------------------------------
    print("[INFO] Loading traffic data...")
    df = pd.read_csv(Config.TRAFFIC_DATA_PATH)
    df = df.rename(columns={"date": "ds", "passenger_footfall": "y"})
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values("ds").reset_index(drop=True)

    print(f"[INFO] Loaded {len(df)} daily records: "
          f"{df['ds'].min().date()} to {df['ds'].max().date()}")

    # ------------------------------------------------------------------
    # 2. Extend to today so forecasts start from current date
    # ------------------------------------------------------------------
    df = extend_to_today(df)
    print(f"[INFO] Final training range: "
          f"{df['ds'].min().date()} to {df['ds'].max().date()}")

    # ------------------------------------------------------------------
    # 3. Train / test split (last 90 days held out for evaluation)
    # ------------------------------------------------------------------
    holdout_days = 90
    train_df = df.iloc[:-holdout_days].copy()
    test_df  = df.iloc[-holdout_days:].copy()
    print(f"[INFO] Train: {len(train_df)} rows | "
          f"Test (holdout): {len(test_df)} rows")

    # ------------------------------------------------------------------
    # 4. Fit evaluation model on train split
    # ------------------------------------------------------------------
    print("[INFO] Fitting Prophet model for evaluation...")
    model_eval = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode="multiplicative",
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10.0,
        interval_width=0.95,
    )
    model_eval.add_country_holidays(country_name="US")
    model_eval.fit(train_df)

    future_test  = model_eval.make_future_dataframe(periods=holdout_days, freq="D")
    forecast     = model_eval.predict(future_test)
    test_forecast = forecast.tail(holdout_days).copy()

    y_true = test_df["y"].values
    y_pred = test_forecast["yhat"].values
    mae    = mean_absolute_error(y_true, y_pred)
    mape   = mean_absolute_percentage_error(y_true, y_pred) * 100

    print("\n=== Prophet Evaluation (90-day holdout) ===")
    print(f"  MAE  (Mean Absolute Error):  {mae:,.0f} passengers/day")
    print(f"  MAPE (Mean Abs % Error):      {mape:.2f}%")

    # ------------------------------------------------------------------
    # 5. Refit on FULL dataset for production
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
    # 6. Save model + metadata
    # ------------------------------------------------------------------
    os.makedirs(os.path.dirname(Config.TRAFFIC_MODEL_PATH), exist_ok=True)
    joblib.dump(model_prod, Config.TRAFFIC_MODEL_PATH)

    meta = {
        "mae":           round(float(mae), 2),
        "mape_pct":      round(float(mape), 4),
        "train_rows":    len(df),
        "holdout_days":  holdout_days,
        "date_min":      str(df["ds"].min().date()),
        "date_max":      str(df["ds"].max().date()),
        "model_version": Config.MODEL_VERSION,
        "trained_on":    str(date.today()),
    }
    meta_path = Config.TRAFFIC_MODEL_PATH.replace(".pkl", "_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\n[SUCCESS] Traffic model saved to {Config.TRAFFIC_MODEL_PATH}")
    print(f"[SUCCESS] Metadata: MAE={mae:,.0f}, MAPE={mape:.2f}%")
    return meta


if __name__ == "__main__":
    train_pipeline()
