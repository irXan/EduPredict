import os
import json
import time
import numpy as np
import pandas as pd

DEFAULT_STREAM_FILE = "data/raw/lms_stream.csv"

def load_config():
    path = "config/thresholds.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"streaming": {"batch_size": 5, "interval_seconds": 1.0, "socket_host": "localhost", "socket_port": 9999, "spark_master": "local[*]"}}

def simulate_stream_row():
    row = {
        "student_id": f"STU{np.random.randint(15000, 16000)}",
        "course_id": np.random.choice(["CS101", "DS201", "AI301", "DB401", "SE501"]),
        "lms_logins_per_week": int(np.random.poisson(lam=12)),
        "video_watch_hours": round(float(np.random.normal(15, 5)), 1),
        "forum_posts": int(np.random.poisson(lam=4)),
        "avg_quiz_score": round(float(np.random.uniform(40, 95)), 1),
        "attendance_rate": round(float(np.random.uniform(40, 100)), 1),
        "event_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    return row

def ingest_stream_events(stream_file=DEFAULT_STREAM_FILE, rounds=None):
    cfg = load_config().get("streaming", {})
    batch_size = cfg.get("batch_size", 5)
    interval = cfg.get("interval_seconds", 1.0)
    if rounds is None:
        rounds = batch_size

    os.makedirs(os.path.dirname(stream_file), exist_ok=True)
    for i in range(rounds):
        row = simulate_stream_row()
        header = not os.path.exists(stream_file) or os.path.getsize(stream_file) == 0
        pd.DataFrame([row]).to_csv(stream_file, mode="a", header=header, index=False)
        print(f"[STREAM] Event {i + 1}: {row['student_id']} | {row['course_id']} | quiz={row['avg_quiz_score']} | att={row['attendance_rate']}%")
        time.sleep(interval)
    print(f"[STREAM] {rounds} live events appended to {stream_file}")
    return stream_file

def run_spark_streaming(spark_master="local[*]", socket_host="localhost", socket_port=9999):
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.appName("EduPredict_Stream_Ingest").master(spark_master).getOrCreate()
        lines = (spark.readStream.format("socket")
                 .option("host", socket_host)
                 .option("port", socket_port)
                 .load())
        query = lines.writeStream \
            .format("parquet") \
            .option("path", "data/processed/stream_landing") \
            .option("checkpointLocation", "data/processed/stream_checkpoint") \
            .trigger(processingTime="10 seconds") \
            .start()
        print(f"[STREAM] Spark Structured Streaming listening on {socket_host}:{socket_port}")
        query.awaitTermination()
    except Exception as e:
        print(f"[STREAM] Spark streaming unavailable: {e}")
        print("[STREAM] Use ingest_stream_events() for the local simulation path.")

if __name__ == "__main__":
    ingest_stream_events()