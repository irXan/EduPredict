from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class StudentPredictionRequest(BaseModel):
    student_id: Optional[str] = "STU10001"
    age: int = Field(default=20, ge=16, le=60)
    distance_from_campus_km: float = Field(default=5.0, ge=0.0)
    midterm_score: float = Field(default=75.0, ge=0.0, le=100.0)
    assignment_score: float = Field(default=80.0, ge=0.0, le=100.0)
    lms_logins_per_week: int = Field(default=12, ge=0)
    video_watch_hours: float = Field(default=15.0, ge=0.0)
    forum_posts: int = Field(default=4, ge=0)
    quiz_attempts: int = Field(default=8, ge=0)
    avg_quiz_score: float = Field(default=78.0, ge=0.0, le=100.0)
    total_classes: int = Field(default=50, ge=1)
    classes_attended: int = Field(default=42, ge=0)
    attendance_rate: float = Field(default=84.0, ge=0.0, le=100.0)
    tardy_count: int = Field(default=2, ge=0)
    engagement_index: Optional[float] = 80.0

class StudentPredictionResponse(BaseModel):
    predicted_gpa: float
    dropout_risk: str
    is_anomaly: bool
    confidence_score: float

class StudentUpdateRequest(BaseModel):
    age: Optional[int] = Field(default=None, ge=16, le=60)
    distance_from_campus_km: Optional[float] = Field(default=None, ge=0.0)
    midterm_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    assignment_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    lms_logins_per_week: Optional[int] = Field(default=None, ge=0)
    video_watch_hours: Optional[float] = Field(default=None, ge=0.0)
    forum_posts: Optional[int] = Field(default=None, ge=0)
    quiz_attempts: Optional[int] = Field(default=None, ge=0)
    avg_quiz_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    total_classes: Optional[int] = Field(default=None, ge=1)
    classes_attended: Optional[int] = Field(default=None, ge=0)
    attendance_rate: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    tardy_count: Optional[int] = Field(default=None, ge=0)
    engagement_index: Optional[float] = Field(default=None, ge=0.0)

class StudentEditResponse(BaseModel):
    record: dict
    predicted_gpa: float
    dropout_risk: str
    is_anomaly: bool
    confidence_score: float

class SupportTicketCreate(BaseModel):
    subject: str
    category: str
    message: str

class SupportTicketResponse(BaseModel):
    id: int
    subject: str
    category: str
    message: str
    status: str
    created_at: str

class SystemMetricsResponse(BaseModel):
    status: str
    uptime_percentage: float
    cpu_utilization_pct: float
    memory_utilization_pct: float
    avg_latency_ms: float
    total_students_processed: int
