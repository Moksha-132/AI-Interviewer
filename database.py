import sqlite3
import uuid
from datetime import datetime

DB_NAME = "interviews.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_name TEXT NOT NULL,
            candidate_email TEXT NOT NULL,
            interview_time DATETIME NOT NULL,
            token TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'scheduled'
        )
    ''')
    conn.commit()
    conn.close()

def schedule_interview(name, email, interview_time):
    token = str(uuid.uuid4())
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO interviews (candidate_name, candidate_email, interview_time, token)
        VALUES (?, ?, ?, ?)
    ''', (name, email, interview_time, token))
    conn.commit()
    conn.close()
    return token

def get_interview_by_token(token):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM interviews WHERE token = ?', (token,))
    row = c.fetchone()
    conn.close()
    return row

if __name__ == "__main__":
    init_db()
