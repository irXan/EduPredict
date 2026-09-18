# EduPredict — Complete "How to Run" Guide

---

## 1. Prerequisites
- **Python 3.10+** (this machine: Python 3.13.1 via the `py` launcher)
- Modern web browser (Chrome/Edge/Firefox)
- *(Optional for cluster demos)* MongoDB, Java/Hadoop + Spark, Impala — **not required** to run; the project auto-falls back to local equivalents.

> Windows note: commands below use `py`. If `python` is on your PATH, you can swap `py` → `python`.

---

## 2. Open the Project
```powershell
cd C:\Users\pc\Desktop\EduPredict
```

---

## 3. Install Dependencies (once)
```powershell
py -m pip install -r requirements.txt
```

---

## 4. Run the Data Pipeline (order matters)
```powershell
py src\data_pipeline\generator.py          # generates 5,000 students / 6 terms -> data/raw/
py src\data_pipeline\preprocessing.py      # merges + cleans -> data/processed/edupredict_master_clean.csv
py src\data_pipeline\spark_hdfs_job.py     # HDFS-style partitions by risk+term + generates impala_queries.sql
py src\ml\train.py                         # trains all 4 models -> models/ + models/metrics.json
```
Expected output: dropout accuracy ~70%, R² ~0.91, 5 course-demand forecasts.

---

## 5. (Optional) Big-Data Integrations
```powershell
py src\data_pipeline\stream_ingest.py      # simulates live LMS/attendance stream -> data/raw/lms_stream.csv
py src\data_pipeline\mongo_sync.py         # syncs to MongoDB edupredict.students or exports JSON for mongoimport
```
- Run the generated `data\processed\impala_queries.sql` in Impala Server to show analytic SQL.
- `spark_hdfs_job.py` honors env vars `HDFS_URI` / `SPARK_MASTER` when you run it on a real Hadoop/YARN cluster.

---

## 6. Launch the Web Dashboard
```powershell
py -m uvicorn src.backend.app:app --reload --port 8000
```
Open **http://localhost:8000** in your browser. A login screen appears (auth is mandatory). The server also auto-starts a **backup scheduler** (snapshot to `backups/` every 6 hours).

---

## 7. Demo Login
Roles and their credentials:
| Role | Username | Password |
| :-- | :-- | :-- |
| Administrator | `admin` | `password123` |
| Analyst | `analyst_john` | `password123` |
| Teacher (per course track) | `teacher_cs101` / `teacher_ds201` / `teacher_ai301` / `teacher_db401` / `teacher_se501` | same as username |
| Student | `STU10000` (any student ID) | same as username |

Every student of the 5,000-student dataset logs in with their own `student_id` (username and password are the same value). A teacher only sees and edits their own course track's students; saved edits are re-evaluated by the ML models in real time and pushed to open dashboards via WebSockets.

Demo quick-fill buttons are on the login screen. The menu adapts per role (e.g. only Admin sees System Diagnostics; Students see only their own single-screen profile).

---

## 8. Run the Automated Test Suite
```powershell
py -m pytest tests\ -v
```
All 13 tests should pass. Tests use isolated `data/test` + `models/test` folders, so the production 5,000-student dataset and models are never overwritten.

---

## 9. Troubleshooting
- **`No supported WebSocket library detected` / `GET /ws/alerts` returns 404** → uvicorn is missing its WebSocket backend. Fix: `py -m pip install "uvicorn[standard]"`, then restart the server.
- **`python` not recognized** → use `py` (as above).
- **Missing module** → `py -m pip install <package>`.
- **`impala-shell` / Spark "not available" (`HADOOP_HOME` / `winutils`)** → expected on Windows without Hadoop; the pipeline prints a warning and falls back to the local Pandas run. To enable the real PySpark path, set `HADOOP_HOME` (with `winutils.exe` in its `bin`), or set `SPARK_MASTER=hdfs://...`. Run the generated SQL manually in Impala for the demo.
- **Mongo "server not reachable"** → expected if MongoDB isn't installed; it will still export `data/processed/students.json` for `mongoimport`.
- **Port 8000 busy** → change `--port 8001`.
- **Thresholds/tuning** → edit `config\thresholds.json` then re-run `preprocessing.py` → `train.py`.