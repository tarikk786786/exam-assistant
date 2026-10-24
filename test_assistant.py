"""
Automated Pytest Suite using Mock Exam Environment
Validates:
1. Mock portal endpoints & credentials validation
2. Playwright browser navigation & prefill
3. Dashboard exam extraction
4. Question text & options parsing
5. Academic verification & explanation matching
6. Safety constraint check: verify that Final Submit is NEVER clicked autonomously
"""

import pytest
import subprocess
import sys
import os
import time
import requests
from engine import ExamAssistantEngine

MOCK_PORT = 8089
MOCK_BASE_URL = f"http://127.0.0.1:{MOCK_PORT}"

@pytest.fixture(scope="session", autouse=True)
def run_mock_server():
    """Spawns mock exam portal server in background subprocess."""
    mock_script = os.path.join(os.path.dirname(__file__), "mock_server.py")
    proc = subprocess.Popen(
        [sys.executable, mock_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to boot
    connected = False
    for _ in range(25):
        try:
            res = requests.get(f"{MOCK_BASE_URL}/examsignin.php")
            if res.status_code == 200:
                connected = True
                break
        except Exception:
            time.sleep(0.3)
            
    assert connected, "Failed to connect to mock exam server"
    yield
    proc.terminate()
    proc.wait()

def test_mock_portal_login_flow():
    """Tests authentication endpoint behavior."""
    # Bad credentials
    bad_resp = requests.post(f"{MOCK_BASE_URL}/examlogin.php", data={"txtUserId": "bad", "txtPass": "wrong"})
    assert bad_resp.status_code == 401

    # Good credentials
    good_resp = requests.post(
        f"{MOCK_BASE_URL}/examlogin.php",
        data={"txtUserId": "SRU202300876314", "txtPass": "testpass123"},
        allow_redirects=False
    )
    assert good_resp.status_code == 303
    assert "examinationhome" in good_resp.headers["location"]

def test_engine_browser_automation():
    """Tests engine with headless browser on mock portal."""
    engine = ExamAssistantEngine(
        login_url=f"{MOCK_BASE_URL}/examsignin.php",
        student_id="SRU202300876314",
        headless=True
    )
    try:
        engine.start()
        engine.navigate_portal()
        
        # Verify student ID pre-fill
        val = engine.page.input_value("#txtUserId")
        assert val == "SRU202300876314"

        # Complete login
        engine.page.fill("#txtPass", "testpass123")
        engine.page.click("input[type='submit']")
        engine.page.wait_for_url("**/examinationhome.php")
        assert engine.is_authenticated()

        # Check exams listed
        exams = engine.get_dashboard_exams()
        assert len(exams) >= 3
        subject_names = [e["name"] for e in exams]
        assert any("Forensic Medicine" in s for s in subject_names)
        assert any("DNA Typing" in s for s in subject_names)

        # Navigate to a question panel
        engine.page.goto(f"{MOCK_BASE_URL}/onlineexamination/examinationpanel.php?subjectId=12295&qIndex=1")
        q_data = engine.extract_current_question()
        
        assert "Question" in q_data["heading"]
        assert "postmortem change" in q_data["question"].lower()
        assert len(q_data["options"]) >= 4

        # Test verification logic
        analysis = q_data["analysis"]
        assert analysis["recommended_option"] == "B"
        assert "hypostasis" in analysis["explanation"].lower() or "blood" in analysis["explanation"].lower()
        assert "Reddy" in analysis["reference"]

        # Safety Verification: Ensure Final Submit button is present but NEVER triggered
        submit_btn = engine.page.query_selector("#btnFinalSubmit")
        assert submit_btn is not None
        # Verify page URL has not navigated to any submitted/finished state
        assert "examinationpanel.php" in engine.page.url

    finally:
        engine.close()
