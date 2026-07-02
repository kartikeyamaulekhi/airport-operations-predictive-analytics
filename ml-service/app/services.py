import os
import json
import numpy as np
import joblib
from app.config import Config

class MLService:
    FEATURE_ORDER = [
        "year", "month", "arr_flights", "is_summer", 
        "is_winter_holiday", "years_since_2013", 
        "airport_avg_delay_rate", "carrier_avg_delay_rate"
    ]

    def __init__(self):
        self.delay_model = self._load_model(Config.MODEL_PATH, "Delay model")
        self.traffic_model = self._load_model(Config.TRAFFIC_MODEL_PATH, "Traffic model")
        self.traffic_meta = self._load_traffic_metadata()

    def _load_model(self, path: str, model_name: str):
        if not os.path.exists(path):
            raise RuntimeError(f"{model_name} artifact not found at {path}")
        return joblib.load(path)

    def _load_traffic_metadata(self) -> dict:
        meta_path = Config.TRAFFIC_MODEL_PATH.replace(".pkl", "_meta.json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                return json.load(f)
        return {}

    def predict_flight_delay(self, input_dict: dict) -> tuple[int, float]:
        features = np.array([input_dict[col] for col in self.FEATURE_ORDER]).reshape(1, -1)
        prediction = int(self.delay_model.predict(features)[0])
        probability = float(self.delay_model.predict_proba(features)[0][1])
        return prediction, probability

    def run_traffic_forecast(self, days: int) -> list[dict]:
        future = self.traffic_model.make_future_dataframe(periods=days, freq="D")
        forecast = self.traffic_model.predict(future)
        result_df = forecast.tail(days)[["ds", "yhat", "yhat_lower", "yhat_upper"]]
        
        points = []
        for _, row in result_df.iterrows():
            points.append({
                "date": str(row["ds"].date()),
                "predicted_footfall": max(0, int(round(row["yhat"]))),
                "lower_bound": max(0, int(round(row["yhat_lower"]))),
                "upper_bound": max(0, int(round(row["yhat_upper"])))
            })
        return points

ml_service = MLService()
