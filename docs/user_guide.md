# EduPredict User Guide & FAQs

## 1. Quick Start
1. Open your browser and navigate to `http://localhost:8000`.
2. The portal opens on the **login screen** — authentication is mandatory.
3. Enter the username/password for your assigned role (students use their `student_id` as both username and password; teachers use `teacher_cs101`/`teacher_ds201`/`teacher_ai301`/`teacher_db401`/`teacher_se501` with the same value as password; `admin` and `analyst_john` use `password123`).
4. The navigation menu and dashboard content automatically adapt to your role permissions.

## 2. Role Features
- **Administrator (`admin`)**: Full access to all tabs — Dashboard KPIs, Student Records roster, Risk Evaluation (ML predictions), Course Demand forecasting, and System Diagnostics (CPU/Memory/Uptime metrics). Can edit any student record.
- **Teacher (`teacher_cs101` etc.)**: One teacher per course track (CS101, DS201, AI301, DB401, SE501). Each sees and can edit **only their own track's students**, and runs individual ML risk evaluations on them. Edited records are re-read by the models instantly and dashboards update live via WebSockets.
- **Analyst (`analyst_john`)**: Dashboard, Student Records, and Course Demand forecasting — no access to individual Risk Evaluation or System Diagnostics.
- **Student (`STU10000` or any student ID)**: A single-screen **"My Academic Profile"** showing own GPA, attendance, quiz/LMS activity, current risk status, model predictions (predicted GPA, risk, anomaly, confidence), attendance performance charts, and the full academic record — no access to other students' data, Course Demand, or System Diagnostics.

## 3. Frequently Asked Questions (FAQs)
- **Q: How are dropout risks calculated?**
  A: Dropout risks are calculated using a Random Forest Classifier trained on attendance rates, exam scores, LMS logins, and quiz performance.
- **Q: How do real-time alerts work?**
  A: Whenever a student record is flagged with `High Risk` or `Is Anomaly`, the system broadcasts an instant alert via WebSockets to all active teacher/admin dashboards.
- **Q: What happens when a teacher edits a student record?**
  A: The change is saved to the master dataset, the engineer re-computes the engagement index, and the ML models immediately re-predict the student's GPA, dropout risk and anomaly status. The updated values, charts and dashboard KPIs refresh automatically for every open session.
