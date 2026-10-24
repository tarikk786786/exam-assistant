"""
SQLite Database Layer for Progress Tracking and Question Review
Stores:
- Sessions (ID, exam name, started_at, mode)
- Questions reviewed (question number, text, options, user selected answer, AI recommendation, status, flagged)
Does NOT store passwords, credentials, or sensitive authentication cookies.
"""

import sqlite3
import os
import json
from typing import List, Dict, Optional, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "exam_progress.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_name TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        mode TEXT DEFAULT 'learning_support', -- 'learning_support' or 'practice_ai'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS question_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        q_number INTEGER NOT NULL,
        q_text TEXT NOT NULL,
        options_json TEXT NOT NULL,
        user_selected_option TEXT,
        ai_recommended_option TEXT,
        ai_explanation TEXT,
        confidence TEXT,
        reference TEXT,
        is_flagged INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending', -- 'pending', 'reviewed', 'flagged'
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(session_id) REFERENCES sessions(id)
    );
    """)
    conn.commit()
    conn.close()

def create_session(subject_name: str, subject_id: str, mode: str = "learning_support") -> int:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (subject_name, subject_id, mode) VALUES (?, ?, ?)",
        (subject_name, subject_id, mode)
    )
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id

def save_or_update_question(
    session_id: int,
    q_number: int,
    q_text: str,
    options: List[str],
    user_option: Optional[str] = None,
    ai_option: Optional[str] = None,
    ai_explanation: Optional[str] = None,
    confidence: Optional[str] = None,
    reference: Optional[str] = None,
    is_flagged: bool = False,
    status: str = "reviewed"
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM question_reviews WHERE session_id = ? AND q_number = ?",
        (session_id, q_number)
    )
    row = cursor.fetchone()
    opts_json = json.dumps(options)
    
    if row:
        cursor.execute("""
            UPDATE question_reviews SET
                q_text = ?,
                options_json = ?,
                user_selected_option = COALESCE(?, user_selected_option),
                ai_recommended_option = COALESCE(?, ai_recommended_option),
                ai_explanation = COALESCE(?, ai_explanation),
                confidence = COALESCE(?, confidence),
                reference = COALESCE(?, reference),
                is_flagged = ?,
                status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (q_text, opts_json, user_option, ai_option, ai_explanation, confidence, reference, int(is_flagged), status, row["id"]))
    else:
        cursor.execute("""
            INSERT INTO question_reviews (
                session_id, q_number, q_text, options_json, user_selected_option,
                ai_recommended_option, ai_explanation, confidence, reference, is_flagged, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, q_number, q_text, opts_json, user_option,
            ai_option, ai_explanation, confidence, reference, int(is_flagged), status
        ))
    conn.commit()
    conn.close()

def get_progress_summary(session_id: int) -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM question_reviews WHERE session_id = ?", (session_id,))
    total = cursor.fetchone()["total"]
    
    cursor.execute("SELECT COUNT(*) as reviewed FROM question_reviews WHERE session_id = ? AND status = 'reviewed'", (session_id,))
    reviewed = cursor.fetchone()["reviewed"]

    cursor.execute("SELECT COUNT(*) as flagged FROM question_reviews WHERE session_id = ? AND is_flagged = 1", (session_id,))
    flagged = cursor.fetchone()["flagged"]

    cursor.execute("""
        SELECT q_number, q_text, options_json, user_selected_option, ai_recommended_option,
               ai_explanation, confidence, reference, is_flagged, status
        FROM question_reviews WHERE session_id = ? ORDER BY q_number ASC
    """, (session_id,))
    questions = []
    for r in cursor.fetchall():
        q_dict = dict(r)
        q_dict["options"] = json.loads(q_dict["options_json"])
        questions.append(q_dict)

    conn.close()
    return {
        "session_id": session_id,
        "total_recorded": total,
        "reviewed_count": reviewed,
        "flagged_count": flagged,
        "questions": questions
    }
