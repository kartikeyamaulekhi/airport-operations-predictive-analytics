"""
clean_and_engineer.py
Day 2: Data cleaning + feature engineering for the Airline Delay Cause dataset
(real US DOT/BTS data, 2013-2023, 395 airports, 21 carriers, 171,666 rows).

Granularity note: each row = one carrier + airport + month combination
(NOT individual flights). The target we engineer here, `delay_rate`, answers:
"what fraction of this carrier's flights at this airport were delayed 15+
minutes in this month?" - a legitimate airport-operations forecasting target.

Run this from the ml-service/ folder with the venv activated:
    python clean_and_engineer.py
"""

import pandas as pd
import numpy as np

RAW_PATH = "data/Airline_Delay_Cause.csv"
CLEAN_PATH = "data/flight_delay_clean.csv"

print("Loading raw data...")
df = pd.read_csv(RAW_PATH)
print(f"Raw shape: {df.shape}")

# ---------------------------------------------------------------------------
# STEP 1: Drop rows with no recorded activity
# ---------------------------------------------------------------------------
# The 240 rows with nulls across nearly all numeric columns represent
# carrier-airport-month combos with zero recorded flights - not useful
# for delay-rate modeling (can't compute a rate from 0 flights).
before = len(df)
df = df.dropna(subset=["arr_flights", "arr_del15"])
print(f"Dropped {before - len(df)} rows with no recorded flights "
      f"({(before - len(df)) / before:.2%} of data)")

# ---------------------------------------------------------------------------
# STEP 2: Remove rows where arr_flights is 0 (can't compute a rate)
# ---------------------------------------------------------------------------
before = len(df)
df = df[df["arr_flights"] > 0]
print(f"Dropped {before - len(df)} additional rows with 0 flights")

# ---------------------------------------------------------------------------
# STEP 3: Engineer the target variable - delay_rate
# ---------------------------------------------------------------------------
df["delay_rate"] = df["arr_del15"] / df["arr_flights"]

# Sanity check: delay_rate should be between 0 and 1. Real operational data
# can occasionally have arr_del15 > arr_flights due to reporting quirks
# (e.g. delayed flights counted across reporting boundaries) - clip these.
out_of_range = (df["delay_rate"] > 1).sum()
print(f"Rows with delay_rate > 1 (data quirk, will clip to 1.0): {out_of_range}")
df["delay_rate"] = df["delay_rate"].clip(0, 1)

# ---------------------------------------------------------------------------
# STEP 4: Engineer delay-cause proportions (what's DRIVING the delay)
# ---------------------------------------------------------------------------
# These help explain WHY delays happen, useful for SHAP analysis later and
# for the dashboard's "primary delay cause" feature.
cause_cols = ["carrier_ct", "weather_ct", "nas_ct", "security_ct", "late_aircraft_ct"]
total_cause = df[cause_cols].sum(axis=1).replace(0, np.nan)  # avoid div by 0

for col in cause_cols:
    df[f"{col}_share"] = (df[col] / total_cause).fillna(0)

# ---------------------------------------------------------------------------
# STEP 5: Engineer time-based features
# ---------------------------------------------------------------------------
df["is_summer"] = df["month"].isin([6, 7, 8]).astype(int)        # peak travel
df["is_winter_holiday"] = df["month"].isin([12, 1]).astype(int)  # holiday travel
df["years_since_2013"] = df["year"] - 2013                       # trend feature

# ---------------------------------------------------------------------------
# STEP 6: Engineer historical/rolling features (route-level delay tendency)
# ---------------------------------------------------------------------------
# Average historical delay rate for this airport (across all carriers/time) -
# captures "this airport tends to be congested" signal, a key real-world
# predictor that individual-row data alone won't show the model.
airport_avg_delay = df.groupby("airport")["delay_rate"].transform("mean")
df["airport_avg_delay_rate"] = airport_avg_delay

# Average historical delay rate for this carrier (across all airports/time) -
# captures "this airline tends to run late" signal.
carrier_avg_delay = df.groupby("carrier")["delay_rate"].transform("mean")
df["carrier_avg_delay_rate"] = carrier_avg_delay

# ---------------------------------------------------------------------------
# STEP 7: Cancellation and diversion rates (additional operational signals)
# ---------------------------------------------------------------------------
df["cancellation_rate"] = (df["arr_cancelled"] / df["arr_flights"]).clip(0, 1)
df["diversion_rate"] = (df["arr_diverted"] / df["arr_flights"]).clip(0, 1)

# ---------------------------------------------------------------------------
# STEP 8: Final column selection and save
# ---------------------------------------------------------------------------
final_cols = [
    "year", "month", "carrier", "carrier_name", "airport", "airport_name",
    "arr_flights", "arr_del15", "delay_rate",
    "carrier_ct_share", "weather_ct_share", "nas_ct_share",
    "security_ct_share", "late_aircraft_ct_share",
    "is_summer", "is_winter_holiday", "years_since_2013",
    "airport_avg_delay_rate", "carrier_avg_delay_rate",
    "cancellation_rate", "diversion_rate",
]
df_final = df[final_cols].copy()

df_final.to_csv(CLEAN_PATH, index=False)

print(f"\nClean dataset saved: {CLEAN_PATH}")
print(f"Final shape: {df_final.shape}")
print(f"\nDelay rate distribution:\n{df_final['delay_rate'].describe()}")
print(f"\nSample rows:\n{df_final.head(3).to_string()}")
