# EduPredict Application Working Demonstration Video Script

## Video Overview (Length: ~3-5 Minutes)

### Section 1: Introduction (0:00 - 0:45)
- **Visual**: Show project homepage (`http://localhost:8000`).
- **Narrator**: "Welcome to the EduPredict platform demonstration. Built according to Aptech eProject specifications, EduPredict combines Big Data analytics, PySpark parallel processing, ML forecasting, and role-based security to improve student retention and academic performance."

### Section 2: Data Engineering & PySpark HDFS Engine (0:45 - 1:30)
- **Visual**: Show `data/raw/` CSV files, terminal execution of `spark_hdfs_job.py`, and PySpark partitioned output in `data/processed/hdfs_partitioned_output/`.
- **Narrator**: "Here we demonstrate synthetic data ingestion across 5,000 student records and distributed data processing using PySpark."

### Section 3: Machine Learning & Real-Time Predictor (1:30 - 2:45)
- **Visual**: Open dashboard, select student attributes, click **Run Machine Learning Prediction**. Show immediate results for GPA prediction, Dropout Risk level, Anomaly flag, and model confidence.
- **Narrator**: "Our ML suite utilizes Random Forest models and Isolation Forest anomaly detection to deliver real-time risk assessment."

### Section 4: Role-Based Access Control & Live Alerts (2:45 - 3:45)
- **Visual**: Show login modal switching between Administrator, Teacher, Analyst, and Student roles. Demonstrate real-time WebSocket alert appearing when high-risk prediction is run.
- **Narrator**: "Notice how access controls restrict sensitive student endpoints based on user roles, while WebSockets broadcast live alerts for immediate academic intervention."

### Section 5: Conclusion & System Monitoring (3:45 - 4:30)
- **Visual**: Open System Metrics modal showing CPU, Memory, and Latency. Show test suite execution `pytest tests/`.
- **Narrator**: "System monitoring guarantees 99%+ uptime compliance. All source code, DFDs, user documentation, and test suites are included in the final submission package."
