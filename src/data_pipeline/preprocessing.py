import os
import json
import pandas as pd
import numpy as np

CONFIG_PATH = "config/thresholds.json"

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {
        "alert_thresholds": {
            "attendance_low": 60.0,
            "gpa_low": 1.8,
            "engagement_low": 45.0,
            "medium_attendance": 75.0,
            "medium_gpa": 2.5,
            "medium_engagement": 65.0
        },
        "risk_score": {"high_below": 55.0, "medium_below": 68.0}
    }

def preprocess_and_merge_datasets(data_dir="data"):
    raw_dir = f"{data_dir}/raw"
    processed_dir = f"{data_dir}/processed"
    demographics = pd.read_csv(f"{raw_dir}/student_demographics.csv")
    lms = pd.read_csv(f"{raw_dir}/lms_engagement.csv")
    attendance = pd.read_csv(f"{raw_dir}/attendance_records.csv")
    academic = pd.read_csv(f"{raw_dir}/academic_records.csv")

    df = academic.merge(demographics, on="student_id", how="inner")
    df = df.merge(lms, on="student_id", how="inner")
    df = df.merge(attendance, on="student_id", how="inner")

    df.fillna({
        "midterm_score": df["midterm_score"].median(),
        "final_score": df["final_score"].median(),
        "attendance_rate": df["attendance_rate"].mean(),
        "lms_logins_per_week": 0,
        "avg_quiz_score": df["avg_quiz_score"].mean()
    }, inplace=True)

    df["engagement_index"] = np.round(
        (0.5 * df["attendance_rate"]) +
        (0.3 * (df["lms_logins_per_week"] / 20.0 * 100).clip(0, 100)) +
        (0.2 * df["avg_quiz_score"]),
        2
    )

    cfg = load_config()
    risk_cfg = cfg.get("risk_score", {})
    high_below = risk_cfg.get("high_below", 55.0)
    medium_below = risk_cfg.get("medium_below", 68.0)

    risk_score = (
        0.45 * (df["attendance_rate"] / 100.0) +
        0.25 * (df["avg_quiz_score"] / 100.0) +
        0.20 * (df["lms_logins_per_week"] / 20.0).clip(0, 1) +
        0.10 * ((df["midterm_score"] + df["assignment_score"]) / 200.0)
    ) * 100.0
    risk_score = risk_score + np.random.normal(0, 6, size=len(df))

    conditions = [
        risk_score < high_below,
        risk_score < medium_below
    ]
    choices = ["High", "Medium"]
    df["dropout_risk"] = np.select(conditions, choices, default="Low")

    df["is_anomaly"] = (
        ((df["lms_logins_per_week"] >= 10) & (df["final_score"] < 45)) |
        ((df["attendance_rate"] >= 85) & (df["avg_quiz_score"] < 40)) |
        (df["tardy_count"] >= 8)
    )

    os.makedirs(processed_dir, exist_ok=True)
    output_path = f"{processed_dir}/edupredict_master_clean.csv"
    df.to_csv(output_path, index=False)

    print(f"[OK] Cleaned master dataset saved to {output_path}")
    print(f"[OK] Total Student Records: {len(df)}")
    print(f"[OK] Dropout Risk Counts: {df['dropout_risk'].value_counts().to_dict()}")
    print(f"[OK] Anomalies Count: {df['is_anomaly'].sum()}")
    return df

if __name__ == "__main__":
    preprocess_and_merge_datasets()