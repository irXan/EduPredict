import sys
import os
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from src.backend.app import app

client = TestClient(app)

def get_admin_token():
    response = client.post("/api/auth/token", data={"username": "admin", "password": "password123"})
    assert response.status_code == 200
    return response.json()["access_token"]

def test_health_check_and_metrics():
    headers = {"Authorization": f"Bearer {get_admin_token()}"}
    response = client.get("/api/system/metrics", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Healthy"
    assert "uptime_percentage" in data

def test_metrics_requires_admin_role():
    response = client.get("/api/system/metrics")
    assert response.status_code == 401

def test_login_authentication():
    response = client.post("/api/auth/token", data={"username": "admin", "password": "password123"})
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["role"] == "Administrator"

def test_unauthorized_access():
    response = client.get("/api/students")
    assert response.status_code == 401

def test_summary_contains_model_accuracy():
    headers = {"Authorization": f"Bearer {get_admin_token()}"}
    response = client.get("/api/analytics/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "dropout_accuracy" in data
    assert data["total_students"] > 0

def test_student_cannot_access_predict_endpoint():
    res_student = client.post("/api/auth/token", data={"username": "student_alice", "password": "password123"})
    headers = {"Authorization": f"Bearer {res_student.json()['access_token']}"}
    payload = {
        "student_id": "STU10001",
        "age": 20,
        "distance_from_campus_km": 5.0,
        "midterm_score": 75.0,
        "assignment_score": 80.0,
        "lms_logins_per_week": 12,
        "video_watch_hours": 15.0,
        "forum_posts": 4,
        "quiz_attempts": 8,
        "avg_quiz_score": 78.0,
        "total_classes": 50,
        "classes_attended": 42,
        "attendance_rate": 84.0,
        "tardy_count": 2
    }
    response = client.post("/api/predict/student", json=payload, headers=headers)
    assert response.status_code == 403
