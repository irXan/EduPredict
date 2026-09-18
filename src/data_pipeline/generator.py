import os
import random
import numpy as np
import pandas as pd

TERMS = ["Fall 2023", "Spring 2024", "Fall 2024", "Spring 2025", "Fall 2025", "Spring 2026"]

def generate_educational_data(num_students=5000, seed=42, data_dir="data"):
    np.random.seed(seed)
    random.seed(seed)

    os.makedirs(f"{data_dir}/raw", exist_ok=True)
    os.makedirs(f"{data_dir}/processed", exist_ok=True)

    student_ids = [f"STU{10000 + i}" for i in range(num_students)]

    genders = np.random.choice(["Male", "Female", "Other"], size=num_students, p=[0.49, 0.49, 0.02])
    ages = np.random.randint(18, 26, size=num_students)
    socio_tiers = np.random.choice(["Low", "Medium", "High"], size=num_students, p=[0.30, 0.50, 0.20])
    dist_campus = np.round(np.random.exponential(scale=9.5, size=num_students), 1)
    internet = np.random.choice(["High-Speed", "Moderate", "Limited"], size=num_students, p=[0.60, 0.30, 0.10])
    parent_edu = np.random.choice(["High School", "Bachelors", "Masters", "Doctorate"], size=num_students, p=[0.40, 0.40, 0.15, 0.05])

    demographics_df = pd.DataFrame({
        "student_id": student_ids,
        "age": ages,
        "gender": genders,
        "socio_economic_tier": socio_tiers,
        "distance_from_campus_km": dist_campus,
        "internet_access": internet,
        "parent_education": parent_edu
    })

    lms_logins = np.random.poisson(lam=12, size=num_students)
    video_hours = np.round(np.random.normal(loc=15, scale=5, size=num_students).clip(1, 40), 1)
    forum_posts = np.random.poisson(lam=4, size=num_students)
    quiz_attempts = np.random.randint(2, 15, size=num_students)
    avg_quiz_score = np.round(np.random.normal(loc=72, scale=12, size=num_students).clip(30, 100), 1)

    lms_df = pd.DataFrame({
        "student_id": student_ids,
        "lms_logins_per_week": lms_logins,
        "video_watch_hours": video_hours,
        "forum_posts": forum_posts,
        "quiz_attempts": quiz_attempts,
        "avg_quiz_score": avg_quiz_score
    })

    total_classes = np.random.choice([40, 45, 50], size=num_students)
    attendance_rate = (0.5 * (lms_logins / 20.0) + 0.5 * np.random.beta(a=5, b=2, size=num_students)).clip(0.3, 1.0)
    attendance_rate = np.round(attendance_rate * 100, 1)
    classes_attended = np.round((attendance_rate / 100.0) * total_classes).astype(int)
    tardy_count = np.random.poisson(lam=3, size=num_students)

    attendance_df = pd.DataFrame({
        "student_id": student_ids,
        "total_classes": total_classes,
        "classes_attended": classes_attended,
        "attendance_rate": attendance_rate,
        "tardy_count": tardy_count
    })

    base_score = (0.4 * attendance_rate) + (0.4 * avg_quiz_score) + np.random.normal(loc=0, scale=8, size=num_students)
    midterm_score = np.round(base_score.clip(25, 100), 1)
    assignment_score = np.round((base_score + np.random.normal(0, 5, num_students)).clip(30, 100), 1)
    final_score = np.round((0.3 * midterm_score + 0.3 * assignment_score + 0.4 * base_score).clip(20, 100), 1)
    gpa = np.round((final_score / 100.0) * 4.0, 2)

    courses = np.random.choice(["CS101", "DS201", "AI301", "DB401", "SE501"], size=num_students)
    term_index = np.random.randint(0, len(TERMS), size=num_students)
    term = np.array(TERMS)[term_index]

    academic_df = pd.DataFrame({
        "student_id": student_ids,
        "course_id": courses,
        "term": term,
        "term_index": term_index,
        "midterm_score": midterm_score,
        "assignment_score": assignment_score,
        "final_score": final_score,
        "gpa": gpa,
        "credits": np.random.choice([3, 4], size=num_students)
    })

    demographics_df.to_csv(f"{data_dir}/raw/student_demographics.csv", index=False)
    lms_df.to_csv(f"{data_dir}/raw/lms_engagement.csv", index=False)
    attendance_df.to_csv(f"{data_dir}/raw/attendance_records.csv", index=False)
    academic_df.to_csv(f"{data_dir}/raw/academic_records.csv", index=False)

    print(f"[OK] Generated datasets for {num_students} students in {data_dir}/raw/")
    print(f"[OK] Academic terms: {TERMS}")
    return demographics_df, lms_df, attendance_df, academic_df

if __name__ == "__main__":
    generate_educational_data()