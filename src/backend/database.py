import os
import sqlite3
import pandas as pd
from passlib.context import CryptContext
from passlib.hash import ldap_salted_sha256

DB_FILE = "edupredict.db"
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "ldap_salted_sha256"], deprecated="auto")

def init_sqlite_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS support_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        subject TEXT NOT NULL,
        category TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'Open',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN course_id TEXT")
    except Exception:
        pass
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_meta (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    
    def_hash = pwd_context.hash("password123")
    seed_users = [
        ("admin", def_hash, "System Administrator", "Administrator", None),
        ("analyst_john", def_hash, "John Data Analyst", "Analyst", None),
        ("student_alice", def_hash, "Alice Cooper", "Student", None)
    ]
    
    for username, p_hash, full_name, role, course_id in seed_users:
        cursor.execute("INSERT OR REPLACE INTO users (username, password_hash, full_name, role, course_id) VALUES (?, ?, ?, ?, ?)",
                       (username, p_hash, full_name, role, course_id))
    
    teacher_mapping = {
        "teacher_cs101": "CS101",
        "teacher_ds201": "DS201",
        "teacher_ai301": "AI301",
        "teacher_db401": "DB401",
        "teacher_se501": "SE501"
    }
    for username, course_id in teacher_mapping.items():
        teacher_hash = ldap_salted_sha256.hash(username)
        cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, full_name, role, course_id) VALUES (?, ?, ?, ?, ?)",
                       (username, teacher_hash, f"{course_id} Track Teacher", "Teacher", course_id))
    
    seeded_row = cursor.execute("SELECT value FROM app_meta WHERE key = 'students_seeded'").fetchone()
    if not seeded_row:
        master_file = "data/processed/edupredict_master_clean.csv"
        student_ids = []
        if os.path.exists(master_file):
            student_ids = pd.read_csv(master_file, usecols=["student_id"])["student_id"].tolist()
        if student_ids:
            seed_rows = [
                (sid, ldap_salted_sha256.hash(sid), f"Student {sid}", "Student", None)
                for sid in student_ids
            ]
            cursor.executemany(
                "INSERT OR IGNORE INTO users (username, password_hash, full_name, role, course_id) VALUES (?, ?, ?, ?, ?)",
                seed_rows
            )
            cursor.execute("INSERT OR REPLACE INTO app_meta (key, value) VALUES ('students_seeded', ?)", (str(len(student_ids)),))
            print(f"[DB] Seeded {len(student_ids)} student login accounts.")
            
    conn.commit()
    conn.close()

def get_db_connection():
    init_sqlite_db()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def load_student_records(limit=100):
    processed_file = "data/processed/edupredict_master_clean.csv"
    if os.path.exists(processed_file):
        df = pd.read_csv(processed_file)
        return df.head(limit).to_dict(orient="records")
    return []
