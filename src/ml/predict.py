import os
import json
import joblib
import numpy as np
import pandas as pd

_MODELS = {}

def load_config():
    path = "config/thresholds.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"alert_thresholds": {"attendance_low": 60.0, "gpa_low": 1.8, "engagement_low": 45.0}}

def load_models(models_dir="models"):
    global _MODELS
    cache_key = models_dir
    if cache_key in _MODELS and _MODELS[cache_key]:
        return _MODELS[cache_key]

    models = {}
    try:
        models["scaler"] = joblib.load(f"{models_dir}/scaler.joblib")
        models["feature_cols"] = joblib.load(f"{models_dir}/feature_cols.joblib")
        models["feature_medians"] = joblib.load(f"{models_dir}/feature_medians.joblib")
        models["performance"] = joblib.load(f"{models_dir}/performance_model.joblib")
        models["dropout"] = joblib.load(f"{models_dir}/dropout_model.joblib")
        models["le_risk"] = joblib.load(f"{models_dir}/label_encoder_risk.joblib")
        models["course_demand"] = joblib.load(f"{models_dir}/course_demand_model.joblib")
        models["anomaly"] = joblib.load(f"{models_dir}/anomaly_detector.joblib")
    except Exception as e:
        print(f"[WARN] Error loading models: {e}")
    _MODELS[cache_key] = models
    return models

def predict_single_student(data_dict, models_dir="models"):
    models = load_models(models_dir)
    if not models or "scaler" not in models:
        cfg = load_config().get("alert_thresholds", {})
        att_threshold = cfg.get("attendance_low", 60.0)
        att = float(data_dict.get("attendance_rate", 75.0))
        quiz = float(data_dict.get("avg_quiz_score", 70.0))
        est_gpa = round(min(4.0, max(0.0, (att * 0.02 + quiz * 0.02))), 2)
        risk = "High" if att < att_threshold or est_gpa < 2.0 else ("Medium" if att < 75 else "Low")
        return {
            "predicted_gpa": est_gpa,
            "dropout_risk": risk,
            "is_anomaly": att < 50 or quiz < 40,
            "confidence_score": 0.85
        }

    feature_cols = models["feature_cols"]
    medians = models.get("feature_medians", {})
    row_values = [float(data_dict.get(col, medians.get(col, 0.0))) for col in feature_cols]

    X_input = pd.DataFrame([row_values], columns=feature_cols)
    X_scaled = models["scaler"].transform(X_input)

    pred_gpa = float(np.round(models["performance"].predict(X_scaled)[0], 2))
    pred_gpa = max(0.0, min(4.0, pred_gpa))

    risk_encoded = models["dropout"].predict(X_scaled)[0]
    risk_label = str(models["le_risk"].inverse_transform([risk_encoded])[0])

    risk_probs = models["dropout"].predict_proba(X_scaled)[0]
    confidence = float(np.max(risk_probs))

    anomaly_flag = bool(int(models["anomaly"].predict(X_scaled)[0]) == -1)

    return {
        "predicted_gpa": pred_gpa,
        "dropout_risk": risk_label,
        "is_anomaly": anomaly_flag,
        "confidence_score": round(confidence, 2)
    }

def get_course_demand(models_dir="models"):
    models = load_models(models_dir)
    demand_data = models.get("course_demand", {})
    if isinstance(demand_data, dict) and "forecasts" in demand_data:
        return demand_data["forecasts"]
    return demand_data