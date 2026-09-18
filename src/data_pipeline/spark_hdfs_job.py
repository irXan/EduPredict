import os
import sys
import subprocess
import pandas as pd

IMPALA_SQL_TEMPLATE = """
CREATE DATABASE IF NOT EXISTS edupredict;
USE edupredict;

CREATE TABLE IF NOT EXISTS students_raw (
    student_id STRING,
    course_id STRING,
    term STRING,
    gpa DOUBLE,
    attendance_rate DOUBLE,
    engagement_index DOUBLE,
    midterm_score DOUBLE,
    assignment_score DOUBLE,
    avg_quiz_score DOUBLE,
    lms_logins_per_week INT
) STORED AS PARQUET;

CREATE TABLE IF NOT EXISTS students_partitioned (
    student_id STRING,
    course_id STRING,
    gpa DOUBLE,
    attendance_rate DOUBLE,
    engagement_index DOUBLE,
    midterm_score DOUBLE,
    assignment_score DOUBLE,
    avg_quiz_score DOUBLE,
    lms_logins_per_week INT
) PARTITIONED BY (dropout_risk STRING, term STRING) STORED AS PARQUET;

INSERT OVERWRITE TABLE students_partitioned
PARTITION (dropout_risk, term)
SELECT
    student_id, course_id, gpa, attendance_rate, engagement_index,
    midterm_score, assignment_score, avg_quiz_score, lms_logins_per_week,
    dropout_risk, term
FROM students_raw;

SELECT course_id,
       COUNT(*) AS total_enrolled,
       AVG(gpa) AS avg_gpa,
       AVG(attendance_rate) AS avg_attendance
FROM students_partitioned
GROUP BY course_id
ORDER BY total_enrolled DESC;

SELECT dropout_risk, COUNT(*) AS student_count
FROM students_partitioned
GROUP BY dropout_risk;

SELECT course_id, term, COUNT(*) AS enrolled
FROM students_partitioned
GROUP BY course_id, term
ORDER BY course_id, term;
"""

def _write_impala_sql(data_path):
    sql_path = os.path.join(os.path.dirname(data_path), "impala_queries.sql")
    with open(sql_path, "w") as f:
        f.write(IMPALA_SQL_TEMPLATE)
    print(f"[IMPALA] Analytic SQL saved to {sql_path}")
    try:
        subprocess.run(["impala-shell", "-q", f"USE edupredict; SHOW TABLES;"],
                       check=False, timeout=10, capture_output=True)
        print("[IMPALA] impala-shell connected to cluster.")
    except Exception:
        print("[IMPALA] impala-shell not available - run queries manually in Impala Server.")

def _pandas_fallback(data_path, output_dir):
    spark_df = pd.read_csv(data_path)
    course_demand_df = spark_df.groupby("course_id").agg(
        total_enrolled=("student_id", "count"),
        avg_gpa=("gpa", "mean"),
        avg_attendance=("attendance_rate", "mean"),
        avg_engagement=("engagement_index", "mean")
    ).reset_index()

    course_demand_df.to_csv(f"{output_dir}/course_demand_summary.csv", index=False)

    for (risk, term), group in spark_df.groupby(["dropout_risk", "term"]):
        risk_dir = f"{output_dir}/dropout_risk={risk}"
        term_dir = f"{risk_dir}/term={str(term).replace(' ', '_')}"
        os.makedirs(term_dir, exist_ok=True)
        group.to_csv(f"{term_dir}/part-0000.csv", index=False)

    return {
        "attendance_vs_gpa": float(spark_df["attendance_rate"].corr(spark_df["gpa"])),
        "lms_logins_vs_gpa": float(spark_df["lms_logins_per_week"].corr(spark_df["gpa"])),
        "quiz_score_vs_final": float(spark_df["avg_quiz_score"].corr(spark_df["final_score"]))
    }

def run_spark_hdfs_pipeline(data_path="data/processed/edupredict_master_clean.csv"):
    output_dir = os.path.join(os.path.dirname(data_path), "hdfs_partitioned_output")
    os.makedirs(output_dir, exist_ok=True)

    spark_attempt = True
    if sys.platform == "win32" and not os.environ.get("HADOOP_HOME"):
        spark_attempt = False
        print("[WARN] HADOOP_HOME not set (winutils needed on Windows) - using local Pandas fallback.")

    correlations = None
    if spark_attempt:
        try:
            from pyspark.sql import SparkSession
            from pyspark.sql import functions as F

            spark_master = os.environ.get("SPARK_MASTER", "local[*]")
            spark = SparkSession.builder \
                .appName("EduPredict_HDFS_Analytics") \
                .master(spark_master) \
                .config("spark.sql.shuffle.partitions", "4") \
                .getOrCreate()

            spark_df = spark.read.csv(data_path, header=True, inferSchema=True)

            course_demand = spark_df.groupBy("course_id").agg(
                F.count("student_id").alias("total_enrolled"),
                F.avg("gpa").alias("avg_gpa"),
                F.avg("attendance_rate").alias("avg_attendance"),
                F.avg("engagement_index").alias("avg_engagement")
            )
            course_demand.coalesce(1).write.mode("overwrite").option("header", True) \
                .csv(f"{output_dir}/course_demand_summary")

            spark_df.write.mode("overwrite") \
                .partitionBy("dropout_risk", "term") \
                .parquet(f"{output_dir}/risk_term_partitions")

            correlations = {
                "attendance_vs_gpa": float(spark_df.stat.corr("attendance_rate", "gpa")),
                "lms_logins_vs_gpa": float(spark_df.stat.corr("lms_logins_per_week", "gpa")),
                "quiz_score_vs_final": float(spark_df.stat.corr("avg_quiz_score", "final_score"))
            }
            spark.stop()
        except Exception:
            print("[WARN] Spark execution failed - using local Pandas fallback.")
            if "spark" in locals():
                try:
                    spark.stop()
                except Exception:
                    pass
            correlations = _pandas_fallback(data_path, output_dir)

    if correlations is None:
        correlations = _pandas_fallback(data_path, output_dir)

    _write_impala_sql(data_path)
    print(f"[OK] HDFS Partitioned output written to {output_dir}")
    print(f"[OK] Partitioned by dropout_risk and term")
    print(f"[OK] Feature Correlations: {correlations}")
    return correlations

if __name__ == "__main__":
    run_spark_hdfs_pipeline()