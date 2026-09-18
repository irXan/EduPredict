# EduPredict Developer Guide & API Documentation

## 1. Setup Instructions
1. Install Python 3.10+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Generate synthetic data & run preprocessor:
   ```bash
   python src/data_pipeline/generator.py
   python src/data_pipeline/preprocessing.py
   ```
4. Run PySpark distributed job (HDFS partitions + Impala SQL output):
   ```bash
   python src/data_pipeline/spark_hdfs_job.py
   ```
5. Train Machine Learning Models:
   ```bash
   python src/ml/train.py
   ```
6. (Optional) Simulate stream ingestion and MongoDB sync:
   ```bash
   python src/data_pipeline/stream_ingest.py
   python src/data_pipeline/mongo_sync.py
   ```
7. Start FastAPI REST Server:
   ```bash
   uvicorn src.backend.app:app --reload --port 8000
   ```
8. Run Pytest Automated Test Suite:
   ```bash
   pytest tests/ -v
   ```

Configuration: alert/risk thresholds and stream settings live in `config/thresholds.json`. Model metrics (R2, RMSE, dropout accuracy) are written to `models/metrics.json` after training and are surfaced on the dashboard.

## 2. Data Pipeline Modules
- `src/data_pipeline/generator.py` — synthetic multi-term dataset generation (5,000 student records).
- `src/data_pipeline/preprocessing.py` — merge, impute missing values, feature engineering, risk labeling.
- `src/data_pipeline/spark_hdfs_job.py` — PySpark parallel aggregations, HDFS partitioning, Impala SQL export.
- `src/data_pipeline/stream_ingest.py` — real-time stream ingestion (Spark Structured Streaming or local simulation).
- `src/data_pipeline/mongo_sync.py` — MongoDB sync + JSON export for mongoimport/Compass.

## 3. API Endpoints Reference
- `POST /api/auth/token` -> Authenticate & retrieve JWT bearer token.
- `GET /api/auth/me` -> Get current user profile (requires valid token).
- `GET /api/students` -> List student records (Requires Admin/Teacher/Analyst; Teachers only see their own course track).
- `GET /api/students/me` -> Get own student profile enriched with live ML predictions (Students).
- `GET /api/students/{id}` -> Get one student record (Requires Admin/Teacher/Analyst; Teacher scoped to own track).
- `PUT /api/students/{id}` -> Edit a student record (Requires Admin/Teacher). Recomputes engagement index, re-runs `predict_single_student`, persists to the master CSV and broadcasts a `RECORD_UPDATED` WebSocket event.
- `POST /api/predict/student` -> Generate real-time ML prediction (Requires Admin/Teacher).
- `GET /api/analytics/course-demand` -> Course demand forecasts (Requires Admin/Analyst).
- `GET /api/analytics/summary` -> Cohort KPIs + trained `dropout_accuracy` (Requires Admin/Teacher/Analyst).
- `GET /api/system/metrics` -> Get system CPU, Memory & Latency metrics (**Requires Admin role**).
- `POST /api/support/ticket` -> Submit a support ticket (Any authenticated user).
- `WS /ws/alerts` -> WebSocket connection for live academic alerts.
