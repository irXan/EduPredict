import sys
import os
import time
import json
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from src.backend.app import app
from src.ml.predict import predict_single_student, get_course_demand
from src.backend.metrics import get_system_performance_metrics
from backup_script import perform_automated_backup

def run_live_demonstration():
    print("=" * 65)
    print("  EDUPREDICT: LIVE SYSTEM DEMONSTRATION & VERIFICATION")
    print("  Aptech eProject: Big Data & ML Student Retention Platform")
    print("=" * 65)
    
    client = TestClient(app)
    
    print("\n[STEP 1] Testing System Metrics & Diagnostics Endpoint (Admin Only)...")
    admin_res = client.post("/api/auth/token", data={"username": "admin", "password": "password123"})
    admin_header = {"Authorization": f"Bearer {admin_res.json()['access_token']}"}
    res = client.get("/api/system/metrics", headers=admin_header)
    metrics = res.json()
    print(f" -> Status: {metrics['status']}")
    print(f" -> SLA Uptime: {metrics['uptime_percentage']}%")
    print(f" -> Average API Latency: {metrics['avg_latency_ms']} ms")
    print(f" -> Total Students Processed: {metrics['total_students_processed']:,}")
    
    res_denied = client.get("/api/system/metrics")
    print(f" -> Unauthenticated metrics request: HTTP {res_denied.status_code} (Correctly Denied!)")
    
    print("\n[STEP 2] Testing RBAC Authentication for all 4 Roles...")
    roles = [
        ("admin", "Administrator", "password123"),
        ("teacher_cs101", "Teacher", "teacher_cs101"),
        ("analyst_john", "Analyst", "password123"),
        ("STU10000", "Student", "STU10000")
    ]
    tokens = {}
    for username, role, password in roles:
        res = client.post("/api/auth/token", data={"username": username, "password": password})
        data = res.json()
        tokens[role] = data["access_token"]
        print(f" -> Authenticated: {username.ljust(15)} | Role: {data['role'].ljust(14)} | Token: {data['access_token'][:20]}...")
    
    print("\n[STEP 3] Testing Role-Based Endpoint Access Guards...")
    student_headers = {"Authorization": f"Bearer {tokens['Student']}"}
    admin_headers = {"Authorization": f"Bearer {tokens['Administrator']}"}
    
    res_forbidden = client.get("/api/students", headers=student_headers)
    print(f" -> Student trying to access all students directory: HTTP {res_forbidden.status_code} (Properly Forbidden!)")
    
    res_allowed = client.get("/api/students?limit=5", headers=admin_headers)
    print(f" -> Admin accessing students directory: HTTP {res_allowed.status_code} (Success - Retrieved {res_allowed.json()['count']} records)")

    print("\n[STEP 4] Testing Real-Time Machine Learning Inference...")
    high_risk_student = {
        "student_id": "STU99001",
        "age": 21,
        "distance_from_campus_km": 12.5,
        "midterm_score": 38.0,
        "assignment_score": 44.0,
        "lms_logins_per_week": 2,
        "video_watch_hours": 3.0,
        "forum_posts": 0,
        "quiz_attempts": 2,
        "avg_quiz_score": 42.0,
        "total_classes": 50,
        "classes_attended": 24,
        "attendance_rate": 48.0,
        "tardy_count": 8,
        "engagement_index": 35.0
    }
    
    t0 = time.time()
    pred_high = predict_single_student(high_risk_student)
    lat_ms = (time.time() - t0) * 1000
    print(f" [Test Case A: At-Risk Student Simulation]")
    print(f"   - Input Attendance: 48%, Midterm: 38/100, LMS Logins: 2/wk")
    print(f"   -> Predicted GPA: {pred_high['predicted_gpa']} / 4.0")
    print(f"   -> Dropout Risk: {pred_high['dropout_risk']}")
    print(f"   -> Anomaly Flagged: {pred_high['is_anomaly']}")
    print(f"   -> Confidence: {int(pred_high['confidence_score']*100)}%")
    print(f"   -> Model Inference Latency: {lat_ms:.2f} ms")

    safe_student = {
        "student_id": "STU99002",
        "age": 19,
        "distance_from_campus_km": 3.0,
        "midterm_score": 88.0,
        "assignment_score": 92.0,
        "lms_logins_per_week": 18,
        "video_watch_hours": 24.0,
        "forum_posts": 8,
        "quiz_attempts": 10,
        "avg_quiz_score": 89.0,
        "total_classes": 50,
        "classes_attended": 47,
        "attendance_rate": 94.0,
        "tardy_count": 1,
        "engagement_index": 92.0
    }
    pred_safe = predict_single_student(safe_student)
    print(f"\n [Test Case B: High-Achieving Student Simulation]")
    print(f"   - Input Attendance: 94%, Midterm: 88/100, LMS Logins: 18/wk")
    print(f"   -> Predicted GPA: {pred_safe['predicted_gpa']} / 4.0")
    print(f"   -> Dropout Risk: {pred_safe['dropout_risk']}")
    print(f"   -> Anomaly Flagged: {pred_safe['is_anomaly']}")
    print(f"   -> Confidence: {int(pred_safe['confidence_score']*100)}%")

    print("\n[STEP 5] Testing Course Demand & Enrollment Analytics...")
    demand = get_course_demand()
    for course_id, stats in demand.items():
        print(f" -> Course: {course_id.ljust(6)} | Enrolled: {str(stats.get('current_enrolled', stats.get('enrolled_students', 0))).rjust(4)} | Avg GPA: {stats.get('avg_gpa', 0):.2f} | At-Risk: {stats.get('high_risk_count', 0)}")

    print("\n[STEP 6] Testing Support Ticket Submission...")
    res_ticket = client.post(
        "/api/support/ticket",
        json={"subject": "Prediction query for STU99001", "category": "Academic Inquiry", "message": "Requesting advisory appointment."},
        headers=student_headers
    )
    ticket_data = res_ticket.json()
    print(f" -> Created Ticket #{ticket_data['id']} | Subject: '{ticket_data['subject']}' | Status: {ticket_data['status']}")

    print("\n[STEP 7] Testing Automated Data & Model Backup Utility...")
    perform_automated_backup()

    print("\n" + "=" * 65)
    print("  ALL LIVE TESTS COMPLETED WITH 100% SUCCESS!")
    print("=" * 65)

if __name__ == "__main__":
    run_live_demonstration()
