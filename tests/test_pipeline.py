import sys
import os
sys.path.insert(0, os.path.abspath("."))

from src.data_pipeline.generator import generate_educational_data
from src.data_pipeline.preprocessing import preprocess_and_merge_datasets
from src.data_pipeline.spark_hdfs_job import run_spark_hdfs_pipeline

TEST_DATA = "data/test"

def test_data_generation():
    demographics, lms, attendance, academic = generate_educational_data(num_students=100, data_dir=TEST_DATA)
    assert len(demographics) == 100
    assert len(lms) == 100
    assert len(attendance) == 100
    assert len(academic) == 100
    assert os.path.exists("data/test/raw/student_demographics.csv")
    assert "term_index" in academic.columns

def test_data_preprocessing():
    df = preprocess_and_merge_datasets(data_dir=TEST_DATA)
    assert not df.empty
    assert "dropout_risk" in df.columns
    assert "is_anomaly" in df.columns
    assert "engagement_index" in df.columns
    assert df["dropout_risk"].isin(["High", "Medium", "Low"]).all()

def test_config_file_exists():
    from src.data_pipeline.preprocessing import load_config
    cfg = load_config()
    assert "risk_score" in cfg
    assert "alert_thresholds" in cfg

def test_spark_hdfs_pipeline():
    correlations = run_spark_hdfs_pipeline("data/test/processed/edupredict_master_clean.csv")
    assert "attendance_vs_gpa" in correlations
    assert os.path.exists("data/test/processed/hdfs_partitioned_output")
    assert os.path.exists("data/test/processed/impala_queries.sql")

def test_stream_and_mongo_modules_importable():
    from src.data_pipeline import stream_ingest
    from src.data_pipeline import mongo_sync
    assert callable(stream_ingest.ingest_stream_events)
    assert callable(mongo_sync.export_json)