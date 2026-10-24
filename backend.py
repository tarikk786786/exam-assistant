"""
FastAPI Backend with REST endpoints for:
- Browser lifecycle & authentication checking
- Dashboard exam inspection
- Question extraction & academic evaluation
- Local review and progress tracking (SQLite)
- Mode switching (Learning Support vs Authorized Practice)
"""

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import uvicorn

from engine import ExamAssistantEngine
from config import settings
from storage import init_db, create_session, save_or_update_question, get_progress_summary

app = FastAPI(
    title="AI University Exam Assistant API",
    description="Browser automation and question verification service with strict human controls"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SQLite database
init_db()

# Engine singleton
engine = ExamAssistantEngine(
    login_url=settings.PORTAL_LOGIN_URL,
    student_id=settings.DEFAULT_STUDENT_ID,
    headless=settings.HEADLESS,
    slow_mo=settings.SLOW_MO_MS
)

# Active session tracking
active_session_id: Optional[int] = None
current_mode: str = "learning_support" # 'learning_support' or 'practice_ai'

class StartBrowserRequest(BaseModel):
    headless: Optional[bool] = None
    portal_url: Optional[str] = None
    student_id: Optional[str] = None

class SelectExamRequest(BaseModel):
    subject_id: str
    subject_name: str
    mode: Optional[str] = "learning_support"

class RecordReviewRequest(BaseModel):
    q_number: int
    q_text: str
    options: List[str]
    user_selected_option: Optional[str] = None
    ai_recommended_option: Optional[str] = None
    ai_explanation: Optional[str] = None
    confidence: Optional[str] = None
    reference: Optional[str] = None
    is_flagged: bool = False

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "browser_active": engine.browser is not None,
        "is_authenticated": engine.is_authenticated(),
        "active_session_id": active_session_id,
        "mode": current_mode,
        "human_control_lock": settings.STRICT_HUMAN_CONTROL
    }

@app.post("/api/browser/start")
def start_browser(req: StartBrowserRequest):
    global engine
    try:
        if engine.browser:
            engine.close()
            
        headless = req.headless if req.headless is not None else settings.HEADLESS
        portal_url = req.portal_url or settings.PORTAL_LOGIN_URL
        student_id = req.student_id or settings.DEFAULT_STUDENT_ID
        
        engine = ExamAssistantEngine(
            login_url=portal_url,
            student_id=student_id,
            headless=headless,
            slow_mo=settings.SLOW_MO_MS
        )
        engine.start()
        engine.navigate_portal()
        
        return {
            "status": "started",
            "url": engine.page.url if engine.page else None,
            "message": "Browser opened and pre-filled with student ID. Complete password / CAPTCHA manually."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/browser/status")
def get_browser_status():
    if not engine.page:
        return {"connected": False, "authenticated": False, "current_url": None}
    return {
        "connected": True,
        "authenticated": engine.is_authenticated(),
        "current_url": engine.page.url,
        "mode": current_mode
    }

@app.get("/api/exams")
def get_exams():
    if not engine.page:
        raise HTTPException(status_code=400, detail="Browser is not running. Start browser first.")
    exams = engine.get_dashboard_exams()
    return {
        "authenticated": engine.is_authenticated(),
        "exams": exams
    }

@app.post("/api/exams/select")
def select_exam(req: SelectExamRequest):
    global active_session_id, current_mode
    active_session_id = create_session(
        subject_name=req.subject_name,
        subject_id=req.subject_id,
        mode=req.mode or "learning_support"
    )
    current_mode = req.mode or "learning_support"
    return {
        "status": "selected",
        "session_id": active_session_id,
        "subject_name": req.subject_name,
        "mode": current_mode,
        "notice": "Assessment selected. All navigation and submissions remain under user control."
    }

@app.get("/api/question/extract")
def extract_question():
    if not engine.page:
        raise HTTPException(status_code=400, detail="Browser is not running.")
    data = engine.extract_current_question()
    
    # In learning-support mode, label clearly
    if current_mode == "learning_support":
        if "analysis" in data:
            data["analysis"]["mode_notice"] = "Learning Support Mode: Review concepts and verify independently."
            
    return data

@app.post("/api/question/record")
def record_question(req: RecordReviewRequest):
    global active_session_id
    if not active_session_id:
        active_session_id = create_session(subject_name="General Review", subject_id="0")
        
    save_or_update_question(
        session_id=active_session_id,
        q_number=req.q_number,
        q_text=req.q_text,
        options=req.options,
        user_option=req.user_selected_option,
        ai_option=req.ai_recommended_option,
        ai_explanation=req.ai_explanation,
        confidence=req.confidence,
        reference=req.reference,
        is_flagged=req.is_flagged,
        status="reviewed"
    )
    return {"status": "saved", "session_id": active_session_id}

@app.get("/api/progress")
def get_progress():
    global active_session_id
    if not active_session_id:
        return {"session_id": None, "total_recorded": 0, "reviewed_count": 0, "flagged_count": 0, "questions": []}
    return get_progress_summary(active_session_id)

@app.post("/api/browser/close")
def close_browser():
    engine.close()
    return {"status": "closed"}

if __name__ == "__main__":
    uvicorn.run("backend:app", host="127.0.0.1", port=settings.DASHBOARD_PORT, reload=False)
