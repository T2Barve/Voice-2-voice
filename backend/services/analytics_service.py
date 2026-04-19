import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "analytics.db"

def init_analytics_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create the unified analytics table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS interview_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id TEXT UNIQUE,
        candidate_name TEXT,
        company TEXT,
        role TEXT,
        interview_type TEXT,
        difficulty TEXT,
        score REAL,
        strengths TEXT,
        weaknesses TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def log_interview_result(data: dict):
    init_analytics_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR REPLACE INTO interview_sessions 
    (thread_id, candidate_name, company, role, interview_type, difficulty, score, strengths, weaknesses)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get("thread_id", "unknown"),
        data.get("candidate_name", "Anonymous"),
        data.get("company", "Unknown"),
        data.get("role", "Engineer"),
        data.get("interview_type", "General"),
        data.get("difficulty", "medium"),
        float(data.get("score", 0)),
        data.get("strengths", ""),
        data.get("weaknesses", "")
    ))
    
    conn.commit()
    conn.close()

def get_dashboard_metrics():
    init_analytics_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Total interviews
        cursor.execute("SELECT COUNT(*) FROM interview_sessions")
        total = cursor.fetchone()[0]
        
        # Average score
        cursor.execute("SELECT AVG(score) FROM interview_sessions")
        avg = cursor.fetchone()[0] or 0.0
        
        # Recent sessions
        cursor.execute('''
            SELECT interview_type, company, score, date(created_at) as date
            FROM interview_sessions 
            ORDER BY created_at DESC 
            LIMIT 5
        ''')
        recent = [{"type": r[0], "company": r[1], "score": f"{r[2]:.1f}/10", "date": r[3]} for r in cursor.fetchall()]
        
        return {
            "total_interviews": total,
            "average_score": round(avg, 1),
            "recent_sessions": recent
        }
    finally:
        conn.close()

# Initialize DB on load
init_analytics_db()
