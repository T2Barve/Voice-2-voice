import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "interview.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            session_id TEXT UNIQUE,
            report_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_report(session_id: str, report_data: dict):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    report_json = json.dumps(report_data)
    now = datetime.utcnow().isoformat()
    
    # Store or update
    cursor.execute('''
        INSERT INTO reports (id, session_id, report_json, created_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET report_json = excluded.report_json, created_at = excluded.created_at
    ''', (str(uuid.uuid4()), session_id, report_json, now))
    
    conn.commit()
    conn.close()

def get_report(session_id: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT report_json FROM reports WHERE session_id = ?', (session_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0])
    return None
