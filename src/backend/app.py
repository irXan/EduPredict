import os
import json
import asyncio
import threading
import time
import numpy as np
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from src.backend.auth import (
    create_access_token, get_current_user, RoleChecker,
    verify_password, User, Token
)
from src.backend.database import get_db_connection, load_student_records
from src.backend.schemas import (
    StudentPredictionRequest, StudentPredictionResponse,
    SupportTicketCreate, SystemMetricsResponse,
    StudentUpdateRequest, StudentEditResponse
)
from src.ml.predict import predict_single_student, get_course_demand
from src.backend.metrics import get_system_performance_metrics
from src.backend.support import create_support_ticket, get_user_support_tickets
from backup_script import perform_automated_backup

app = FastAPI(
    title="EduPredict Portal API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_alert(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.post("/api/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, password_hash, full_name, role, course_id FROM users WHERE username = ?", (form_data.username,))
    user_row = cursor.fetchone()
    conn.close()
    
    if not user_row or not verify_password(form_data.password, user_row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(
        data={"sub": user_row["username"], "role": user_row["role"], "full_name": user_row["full_name"], "course_id": user_row["course_id"]}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user_row["role"],
        "username": user_row["username"],
        "course_id": user_row["course_id"]
    }

@app.get("/api/auth/me", response_model=User)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

def get_model_metrics():
    path = "models/metrics.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"dropout_accuracy": 0.0}

def _all_records():
    return load_student_records(limit=5000)

def _teacher_records(course_id):
    records = _all_records()
    return [r for r in records if r.get("course_id") == course_id]

def _find_student(student_id):
    for r in _all_records():
        if r.get("student_id") == student_id:
            return r
    return None

def backup_scheduler_loop():
    while True:
        try:
            perform_automated_backup()
            print("[BACKUP] Scheduled backup completed.")
        except Exception:
            pass
        time.sleep(6 * 60 * 60)

@app.on_event("startup")
async def on_startup():
    worker = threading.Thread(target=backup_scheduler_loop, daemon=True)
    worker.start()

@app.get("/api/students")
async def get_students(
    limit: int = 50,
    current_user: User = Depends(RoleChecker(["Administrator", "Teacher", "Analyst"]))
):
    if current_user.role == "Teacher":
        records = _teacher_records(current_user.course_id)
    else:
        records = _all_records()
    return {"count": len(records), "students": records[:limit]}

@app.get("/api/students/me")
async def get_my_student_profile(
    current_user: User = Depends(get_current_user)
):
    username_to_student = {
        "student_alice": "STU10000",
    }
    student_id = username_to_student.get(current_user.username)
    if student_id is None:
        records = _all_records()
        for student in records:
            if student.get("student_id") == current_user.username:
                student_id = current_user.username
                break
    
    if not student_id:
        records = _all_records()
        if records:
            return records[0]
        raise HTTPException(status_code=404, detail="No student profile linked to this account")
    
    for student in _all_records():
        if student.get("student_id") == student_id:
            evaluation = predict_single_student(student)
            return {
                **student,
                "predicted_gpa": evaluation["predicted_gpa"],
                "predicted_risk": evaluation["dropout_risk"],
                "predicted_anomaly": evaluation["is_anomaly"],
                "confidence_score": evaluation["confidence_score"]
            }
    raise HTTPException(status_code=404, detail="Student record not found")

@app.get("/api/students/{student_id}")
async def get_student_by_id(
    student_id: str,
    current_user: User = Depends(RoleChecker(["Administrator", "Teacher", "Analyst"]))
):
    student = _find_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")
    if current_user.role == "Teacher" and student.get("course_id") != current_user.course_id:
        raise HTTPException(status_code=403, detail="Access restricted to your course track students only")
    return student

@app.post("/api/predict/student", response_model=StudentPredictionResponse)
async def predict_student(
    request: StudentPredictionRequest,
    current_user: User = Depends(RoleChecker(["Administrator", "Teacher"]))
):
    if current_user.role == "Teacher":
        student = _find_student(request.student_id)
        if student and student.get("course_id") != current_user.course_id:
            raise HTTPException(status_code=403, detail="Access restricted to your course track students only")

    input_data = request.model_dump()
    result = predict_single_student(input_data)
    
    if result["dropout_risk"] == "High" or result["is_anomaly"]:
        alert_msg = json.dumps({
            "type": "ACADEMIC_ALERT",
            "student_id": request.student_id,
            "risk": result["dropout_risk"],
            "predicted_gpa": result["predicted_gpa"],
            "is_anomaly": result["is_anomaly"],
            "timestamp": "Just now"
        })
        await manager.broadcast_alert(alert_msg)
        
    return result

@app.put("/api/students/{student_id}", response_model=StudentEditResponse)
async def update_student_record(
    student_id: str,
    updates: StudentUpdateRequest,
    current_user: User = Depends(RoleChecker(["Administrator", "Teacher"]))
):
    import pandas as pd
    
    master_file = "data/processed/edupredict_master_clean.csv"
    if not os.path.exists(master_file):
        raise HTTPException(status_code=404, detail="Master dataset not found")
    
    df = pd.read_csv(master_file)
    match_idx = df.index[df["student_id"] == student_id].tolist()
    if not match_idx:
        raise HTTPException(status_code=404, detail="Student record not found")
    idx = match_idx[0]
    
    if current_user.role == "Teacher" and df.at[idx, "course_id"] != current_user.course_id:
        raise HTTPException(status_code=403, detail="Access restricted to your course track students only")
    
    update_fields = updates.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in update_fields.items():
        df.at[idx, key] = float(value)
    
    df.at[idx, "engagement_index"] = round(
        (0.5 * float(df.at[idx, "attendance_rate"])) +
        (0.3 * (min(100.0, float(df.at[idx, "lms_logins_per_week"]) / 20.0 * 100))) +
        (0.2 * float(df.at[idx, "avg_quiz_score"])),
        2
    )
    
    evaluation = predict_single_student(dict(df.loc[idx]))
    df.at[idx, "gpa"] = float(evaluation["predicted_gpa"])
    df.at[idx, "dropout_risk"] = evaluation["dropout_risk"]
    df.at[idx, "is_anomaly"] = bool(evaluation["is_anomaly"])
    
    df.to_csv(master_file, index=False)
    
    updated_record = {}
    for key, value in dict(df.loc[idx]).items():
        if isinstance(value, np.integer):
            updated_record[key] = int(value)
        elif isinstance(value, np.floating):
            updated_record[key] = float(value)
        elif isinstance(value, np.bool_):
            updated_record[key] = bool(value)
        else:
            updated_record[key] = value
    updated_record["dropout_risk"] = str(updated_record.get("dropout_risk"))
    
    update_msg = json.dumps({
        "type": "RECORD_UPDATED",
        "student_id": student_id,
        "course_id": df.at[idx, "course_id"],
        "dropout_risk": evaluation["dropout_risk"],
        "predicted_gpa": evaluation["predicted_gpa"]
    })
    await manager.broadcast_alert(update_msg)
    
    if evaluation["dropout_risk"] == "High" or evaluation["is_anomaly"]:
        alert_msg = json.dumps({
            "type": "ACADEMIC_ALERT",
            "student_id": student_id,
            "risk": evaluation["dropout_risk"],
            "predicted_gpa": evaluation["predicted_gpa"],
            "is_anomaly": evaluation["is_anomaly"],
            "timestamp": "Just now"
        })
        await manager.broadcast_alert(alert_msg)
    
    return {
        "record": updated_record,
        "predicted_gpa": evaluation["predicted_gpa"],
        "dropout_risk": evaluation["dropout_risk"],
        "is_anomaly": evaluation["is_anomaly"],
        "confidence_score": evaluation["confidence_score"]
    }

@app.get("/api/analytics/course-demand")
async def get_course_demand_analytics(
    current_user: User = Depends(RoleChecker(["Administrator", "Analyst"]))
):
    return {"course_demand": get_course_demand()}

@app.get("/api/analytics/summary")
async def get_analytics_summary(
    current_user: User = Depends(RoleChecker(["Administrator", "Teacher", "Analyst"]))
):
    if current_user.role == "Teacher":
        records = _teacher_records(current_user.course_id)
    else:
        records = _all_records()
    if not records:
        return {"total_students": 0, "avg_gpa": 0, "high_risk_count": 0, "anomaly_count": 0}
        
    total = len(records)
    avg_gpa = round(sum(r.get("gpa", 0) for r in records) / total, 2)
    high_risk = sum(1 for r in records if r.get("dropout_risk") == "High")
    medium_risk = sum(1 for r in records if r.get("dropout_risk") == "Medium")
    low_risk = sum(1 for r in records if r.get("dropout_risk") == "Low")
    anomalies = sum(1 for r in records if r.get("is_anomaly") == True)
    model_metrics = get_model_metrics()

    course_stats = {}
    for r in records:
        cid = r.get("course_id", "Unknown")
        if cid not in course_stats:
            course_stats[cid] = {"enrolled": 0, "gpa_sum": 0.0, "high_risk_count": 0}
        course_stats[cid]["enrolled"] += 1
        course_stats[cid]["gpa_sum"] += r.get("gpa", 0)
        if r.get("dropout_risk") == "High":
            course_stats[cid]["high_risk_count"] += 1
    for cid, c in course_stats.items():
        c["avg_gpa"] = round(c["gpa_sum"] / c["enrolled"], 2)
        del c["gpa_sum"]

    return {
        "scope": current_user.course_id if current_user.role == "Teacher" else "all",
        "total_students": total,
        "avg_gpa": avg_gpa,
        "high_risk_count": high_risk,
        "medium_risk_count": medium_risk,
        "low_risk_count": low_risk,
        "high_risk_percentage": round((high_risk / total) * 100, 1),
        "anomaly_count": anomalies,
        "attendance_average": round(sum(r.get("attendance_rate", 0) for r in records) / total, 1),
        "dropout_accuracy": model_metrics.get("dropout_accuracy", 0.0),
        "course_stats": course_stats
    }

@app.websocket("/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"PONG: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/system/metrics", response_model=SystemMetricsResponse)
async def get_metrics(
    current_user: User = Depends(RoleChecker(["Administrator"]))
):
    return get_system_performance_metrics()

@app.post("/api/support/ticket")
async def submit_support_ticket(
    ticket: SupportTicketCreate,
    current_user: User = Depends(get_current_user)
):
    return create_support_ticket(
        username=current_user.username,
        subject=ticket.subject,
        category=ticket.category,
        message=ticket.message
    )

@app.get("/api/support/tickets")
async def list_user_tickets(current_user: User = Depends(get_current_user)):
    return get_user_support_tickets(current_user.username)

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    index_file = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>EduPredict API Server is Running</h1><p>Visit <a href='/docs'>/docs</a> for API Swagger documentation.</p>"
