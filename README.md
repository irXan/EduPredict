# EduPredict - Educational Analytics & Predictive Platform
**Aptech eProject Submission Package**

---

## 1. Project Overview & Problem Statement
Education institutions worldwide face challenges such as declining student retention rates, inefficient resource allocation, and the need to personalize learning experiences. **EduPredict** is an enterprise-grade Big Data & Machine Learning analytics platform leveraging Hadoop/PySpark distributed processing, predictive ML algorithms, real-time alert streaming, and role-based access security to enhance the educational experience and maximize student retention.

---

## 2. Aptech eProject Requirements Compliance Matrix

| Requirement | Description | Compliance Status | Location in Codebase |
| :--- | :--- | :--- | :--- |
| **Authentication & RBAC** | Secure system for Admin, Teacher, Student, Analyst | ✅ Fully Implemented | `src/backend/auth.py` |
| **Data Ingestion** | Ingestion of Academic, Demographics, LMS & Attendance | ✅ Fully Implemented | `src/data_pipeline/generator.py` |
| **HDFS Storage** | Scalable HDFS data partitioning & storage strategy | ✅ Fully Implemented | `src/data_pipeline/spark_hdfs_job.py` |
| **Data Processing** | Parallel batch processing, missing value handling | ✅ Fully Implemented | `src/data_pipeline/preprocessing.py` |
| **Real-time Streaming** | Streaming integration with batch processing | ✅ Fully Implemented | `src/backend/app.py` (`/ws/alerts`) |
| **Machine Learning** | Performance, Dropout Risk, Course Demand & Anomalies | ✅ Fully Implemented | `src/ml/train.py`, `src/ml/predict.py` |
| **Data Visualization** | Interactive, customizable dashboards for stakeholders | ✅ Fully Implemented | `frontend/index.html` |
| **Notifications & Alerts** | Automated real-time alerts on risk threshold breach | ✅ Fully Implemented | `frontend/index.html` & WebSockets |
| **Feedback & Support** | User assistance ticket system | ✅ Fully Implemented | `src/backend/support.py` |
| **Non-Functional** | Security (JWT/bcrypt), Uptime, Automated Backups | ✅ Fully Implemented | `backup_script.py`, `metrics.py` |
| **Documentation** | DFDs, Flowcharts, User/Dev Guides, Video Script | ✅ Fully Implemented | `docs/` directory |

---

## 3. Project Directory Structure

```
s6/
├── notebooks/                   # Jupyter Notebooks (Google Colab ready)
│   └── 01_EduPredict_Data_Engineering_Colab.ipynb
├── data/                        # Datasets
│   ├── raw/                     # 4 Raw CSV Datasets (Demographics, Academic, LMS, Attendance)
│   └── processed/               # Merged Cleaned Master CSV & HDFS Partitioned Outputs
├── models/                      # Saved ML Models (.joblib)
│   ├── performance_model.joblib # GPA Predictor
│   ├── dropout_model.joblib     # Dropout Risk Classifier
│   ├── course_demand_model.joblib # Course Demand Forecaster
│   └── anomaly_detector.joblib  # Isolation Forest Anomaly Flagger
├── src/                         # Application Source Code
│   ├── data_pipeline/           # Generator, Preprocessor, PySpark HDFS Job
│   ├── ml/                      # Training & Inference Engines
│   ├── backend/                 # FastAPI REST Server, Auth, Database, Metrics, Support
│   └── ml/                      # Training & Inference Engines
├── frontend/                    # Web Dashboard Interface
│   └── index.html
├── tests/                       # Automated Pytest Suite
│   ├── test_api.py
│   ├── test_pipeline.py
│   └── test_ml.py
├── docs/                        # Complete Aptech Deliverables Suite
│   ├── architecture.md          # Architecture Specs
│   ├── dfd_diagrams.md          # Level 0 & Level 1 DFDs
│   ├── flowcharts.md            # System Flowcharts
│   ├── user_guide.md            # User Manual & FAQs
│   ├── developer_guide.md       # API & Developer Specs
│   └── video_script.md          # Demonstration Video Script
├── backup_script.py             # Automated Backup Executor
├── requirements.txt             # Python Dependencies
└── README.md                    # Consolidated Documentation
```

---

## 4. Setup & Running Instructions

> **Quick start?** See the complete step-by-step guide in [`RUNNING.md`](RUNNING.md). The short version is below.

### Prerequisites
- Python 3.10 or higher
- Web Browser (Chrome, Firefox, Edge)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run Data Generation & Cleaning Pipeline
```bash
python src/data_pipeline/generator.py
python src/data_pipeline/preprocessing.py
```

### Step 3: Run PySpark Distributed Data Processing
```bash
python src/data_pipeline/spark_hdfs_job.py
```
This writes HDFS-style partitions (by `dropout_risk` + `term`) and generates `data/processed/impala_queries.sql` for execution in the Impala Server. It attempts Spark first (uses HDFS paths in Hadoop/YARN mode) and falls back to a local PySpark/Pandas run on desktops.

### Step 4: Train Machine Learning Suite
```bash
python src/ml/train.py
```

### Step 5: Simulate Real-Time Stream Ingestion (optional)
```bash
python src/data_pipeline/stream_ingest.py
```
Appends live LMS/attendance events to `data/raw/lms_stream.csv`. For a cluster demo, `run_spark_streaming()` reads a socket stream and lands it into the same partitioned HDFS table as the batch job.

### Step 6: Sync Master Data to MongoDB (optional)
```bash
python src/data_pipeline/mongo_sync.py
```
Inserts records into MongoDB (`edupredict.students`) for browsing in MongoDB Compass/Shell, and exports `data/processed/students.json` for `mongoimport`.

### Step 7: Launch FastAPI Web Dashboard Server
```bash
uvicorn src.backend.app:app --reload --port 8000
```
Open `http://localhost:8000` in your web browser. The server also starts an automated backup thread (snapshots database, data, and models every 6 hours into `backups/`).

---

## 5. Pre-seeded Demo Credentials (RBAC Roles)

On first launch the portal opens a **login screen** — authentication is mandatory before any institutional data is shown. After signing in, the menu adapts to your role.

| Role | Username | Password | Permissions (Tabs / Features) |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `password123` | Full access: Dashboard, Student Records, Risk Evaluation, Course Demand + System Diagnostics (metrics/backups) |
| **Analyst** | `analyst_john` | `password123` | Dashboard, Student Records, Course Demand |
| **Teacher – CS101** | `teacher_cs101` | `teacher_cs101` | Own course track only: sees & edits its students, runs risk evaluations |
| **Teacher – DS201** | `teacher_ds201` | `teacher_ds201` | Own course track only: sees & edits its students, runs risk evaluations |
| **Teacher – AI301** | `teacher_ai301` | `teacher_ai301` | Own course track only: sees & edits its students, runs risk evaluations |
| **Teacher – DB401** | `teacher_db401` | `teacher_db401` | Own course track only: sees & edits its students, runs risk evaluations |
| **Teacher – SE501** | `teacher_se501` | `teacher_se501` | Own course track only: sees & edits its students, runs risk evaluations |
| **Student** | `STU10000` (any student ID) | same as username | Single-screen "My Academic Profile" with own record, model results & charts |

Every student of the 5,000-student dataset can log in using their own `student_id` as the username and the **same value as the password**. Teacher edits save instantly — the ML models re-evaluate the student and all visible data/charts update live over WebSockets.

Quick-fill demo buttons on the login screen populate the credentials for each role.

---

## 6. Assumptions Made
1. **Zero-Dependency Fallback**: SQLite, Pandas fallbacks, and local HDFS partition folders are included so the application can run instantly on any desktop without requiring local Hadoop/MongoDB/Spark cluster installations. The data pipeline includes a Spark Streaming and MongoDB path for cluster/Hybrid deployments.
2. **Synthetic Dataset Scale**: Data generator produces 5,000 realistic student records across 6 academic terms simulating multi-department university enrollments.
3. **Alert Thresholds**: Configurable via `config/thresholds.json`. Default High Risk triggers when the weighted composite `risk_score` falls below 55.0 (combining attendance, quiz, LMS, and exam indicators with Gaussian noise).
4. **Automated Backups**: A scheduler thread runs at server startup, immediately performing a snapshot and then repeating every 6 hours. Snapshots go to `backups/backup_<timestamp>/`.
