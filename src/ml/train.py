import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, IsolationForest
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score

FEATURE_COLS = [
    "age", "distance_from_campus_km", "midterm_score", "assignment_score",
    "lms_logins_per_week", "video_watch_hours", "forum_posts", "quiz_attempts",
    "avg_quiz_score", "total_classes", "classes_attended", "attendance_rate",
    "tardy_count", "engagement_index"
]

def train_all_models(data_path="data/processed/edupredict_master_clean.csv", models_dir="models"):
    df = pd.read_csv(data_path)

    os.makedirs(models_dir, exist_ok=True)

    X = df[FEATURE_COLS]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    feature_medians = {col: float(df[col].median()) for col in FEATURE_COLS}

    joblib.dump(scaler, f"{models_dir}/scaler.joblib")
    joblib.dump(FEATURE_COLS, f"{models_dir}/feature_cols.joblib")
    joblib.dump(feature_medians, f"{models_dir}/feature_medians.joblib")

    y_gpa = np.clip(df["gpa"] + np.random.normal(0, 0.12, size=len(df)), 0, 4)
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_gpa, test_size=0.2, random_state=42)

    perf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    perf_model.fit(X_train, y_train)

    gpa_preds = perf_model.predict(X_test)
    r2 = r2_score(y_test, gpa_preds)
    rmse = np.sqrt(mean_squared_error(y_test, gpa_preds))
    print(f"[TRAIN] Performance Predictor R2: {r2:.4f}, RMSE: {rmse:.4f}")
    joblib.dump(perf_model, f"{models_dir}/performance_model.joblib")

    le_risk = LabelEncoder()
    y_risk = le_risk.fit_transform(df["dropout_risk"])

    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X_scaled, y_risk, test_size=0.2, random_state=42)
    dropout_model = RandomForestClassifier(n_estimators=100, random_state=42)
    dropout_model.fit(X_train_r, y_train_r)

    risk_preds = dropout_model.predict(X_test_r)
    acc = accuracy_score(y_test_r, risk_preds)
    print(f"[TRAIN] Dropout Risk Accuracy: {acc * 100:.2f}%")
    joblib.dump(dropout_model, f"{models_dir}/dropout_model.joblib")
    joblib.dump(le_risk, f"{models_dir}/label_encoder_risk.joblib")

    metrics = {
        "performance_r2": round(float(r2), 4),
        "performance_rmse": round(float(rmse), 4),
        "dropout_accuracy": round(float(acc) * 100, 2),
        "n_students": int(len(df))
    }
    with open(f"{models_dir}/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[TRAIN] Metrics saved to {models_dir}/metrics.json")

    course_terms = df.groupby(["course_id", "term_index"]).agg(
        enrolled_students=("student_id", "count"),
        avg_gpa=("gpa", "mean"),
        avg_attendance=("attendance_rate", "mean"),
        avg_engagement=("engagement_index", "mean"),
        avg_midterm=("midterm_score", "mean"),
        high_risk_count=("dropout_risk", lambda x: (x == "High").sum())
    ).reset_index()

    forecast_stats = {}
    for course_id in sorted(course_terms["course_id"].unique()):
        ct = course_terms[course_terms["course_id"] == course_id].sort_values("term_index")
        X_term = ct["term_index"].values.reshape(-1, 1)
        y_term = ct["enrolled_students"].values.astype(float)
        reg = LinearRegression().fit(X_term, y_term)
        next_term = int(ct["term_index"].max()) + 1
        prediction = int(round(max(0.0, float(reg.predict([[next_term]])[0]))))
        last = ct.iloc[-1]
        current = int(last["enrolled_students"])
        forecast_stats[course_id] = {
            "course_id": course_id,
            "current_enrolled": current,
            "predicted_next_term": prediction,
            "avg_gpa": round(float(last["avg_gpa"]), 2),
            "avg_attendance": round(float(last["avg_attendance"]), 1),
            "avg_engagement": round(float(last["avg_engagement"]), 1),
            "high_risk_count": int(last["high_risk_count"]),
            "trend": "Growing" if prediction > current else "Declining"
        }

    demand_result = {
        "features": ["term_index"],
        "forecasts": forecast_stats
    }

    print(f"[TRAIN] Course Demand Forecaster trained on {len(course_terms)} course-term records")
    for fc in forecast_stats.values():
        print(f"  -> {fc['course_id']}: Current={fc['current_enrolled']}, Predicted Next Term={fc['predicted_next_term']} ({fc['trend']})")
    joblib.dump(demand_result, f"{models_dir}/course_demand_model.joblib")

    anomaly_detector = IsolationForest(contamination=0.05, random_state=42)
    anomaly_detector.fit(X_scaled)
    joblib.dump(anomaly_detector, f"{models_dir}/anomaly_detector.joblib")

    print(f"[TRAIN] All models trained and saved to {models_dir}/")
    return metrics

if __name__ == "__main__":
    train_all_models()