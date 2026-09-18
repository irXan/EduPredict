import sys
import os
sys.path.insert(0, os.path.abspath("."))

from src.data_pipeline.generator import generate_educational_data
from src.data_pipeline.preprocessing import preprocess_and_merge_datasets
from src.ml.train import train_all_models
from src.ml.predict import predict_single_student

TEST_DATA = "data/test"
TEST_MODELS = "models/test"

def test_ml_training_and_inference():
    generate_educational_data(num_students=300, data_dir=TEST_DATA)
    preprocess_and_merge_datasets(data_dir=TEST_DATA)
    train_all_models(data_path="data/test/processed/edupredict_master_clean.csv", models_dir=TEST_MODELS)

    sample_student = {
        "age": 21,
        "distance_from_campus_km": 8.0,
        "midterm_score": 42.0,
        "assignment_score": 50.0,
        "lms_logins_per_week": 3,
        "video_watch_hours": 4.0,
        "forum_posts": 0,
        "quiz_attempts": 2,
        "avg_quiz_score": 45.0,
        "total_classes": 50,
        "classes_attended": 25,
        "attendance_rate": 50.0,
        "tardy_count": 8,
        "engagement_index": 40.0
    }

    res = predict_single_student(sample_student, models_dir=TEST_MODELS)
    assert "predicted_gpa" in res
    assert 0.0 <= res["predicted_gpa"] <= 4.0
    assert res["dropout_risk"] in ["High", "Medium", "Low"]
    assert isinstance(res["is_anomaly"], bool)

def test_training_metrics_saved():
    assert os.path.exists("models/test/metrics.json")
    assert os.path.exists("models/test/feature_medians.joblib")