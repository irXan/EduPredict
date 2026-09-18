import sqlite3
from src.backend.database import get_db_connection

def create_support_ticket(username: str, subject: str, category: str, message: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO support_tickets (user_id, subject, category, message, status) VALUES (?, ?, ?, ?, ?)",
        (username, subject, category, message, "Open")
    )
    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": ticket_id,
        "user_id": username,
        "subject": subject,
        "category": category,
        "message": message,
        "status": "Open"
    }

def get_user_support_tickets(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, subject, category, message, status, created_at FROM support_tickets WHERE user_id = ? ORDER BY id DESC", (username,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]
