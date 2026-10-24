"""
University Exam Portal Assistant & Question Verifier
Target Portal: http://13.228.179.22/
"""

import sys
import time
import json
import os
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, Page, BrowserContext

PORTAL_LOGIN_URL = "http://13.228.179.22/examsignin.php?session=true"
DEFAULT_STUDENT_ID = "SRU202300876314"

class UniversityExamAssistant:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.session_log: List[Dict] = []

    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            channel="chrome" if os.name == "nt" else None
        )
        self.context = self.browser.new_context(viewport={"width": 1280, "height": 800})
        self.page = self.context.new_page()

    def navigate_login(self, student_id: str = DEFAULT_STUDENT_ID):
        print(f"[*] Navigating to exam portal: {PORTAL_LOGIN_URL}")
        self.page.goto(PORTAL_LOGIN_URL)
        self.page.wait_for_load_state("domcontentloaded")
        
        # Check if already logged in or on login page
        user_input = self.page.query_selector("#txtUserId")
        if user_input:
            user_input.fill(student_id)
            print(f"[+] Prefilled Student ID: {student_id}")
            print("[!] Please complete login (password entry, credentials check) directly in the browser.")
        else:
            print("[*] Already on dashboard or custom view.")

    def wait_for_dashboard(self, timeout_sec: int = 120) -> bool:
        print("[*] Waiting for user to complete login...")
        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            if "examinationhome" in self.page.url:
                print("[+] Successfully reached Examination Dashboard!")
                return True
            time.sleep(1)
        return False

    def list_available_exams(self) -> List[Dict]:
        """Inspects tabs on the dashboard and extracts exams with their statuses."""
        exams = self.page.evaluate('''() => {
            const tabs = Array.from(document.querySelectorAll('ul.nav-tabs li a, .nav-tabs a'));
            return tabs.map(tab => {
                const name = tab.innerText.trim();
                const targetId = tab.getAttribute('href') ? tab.getAttribute('href').replace('#', '') : '';
                const pane = document.getElementById(targetId);
                let status = "Not active";
                let questionCount = "Unknown";
                if (pane) {
                    const text = pane.innerText.trim();
                    if (text.includes("finished")) {
                        status = "Finished";
                    } else if (text.includes("No. of Questions")) {
                        status = "Available / Active";
                        const match = text.match(/No\\.\\s*of\\s*Questions:\\s*(\\d+)/i);
                        if (match) questionCount = match[1];
                    }
                }
                return {
                    name: name,
                    subjectId: targetId,
                    status: status,
                    questionCount: questionCount
                };
            });
        }''')
        return exams

    def switch_subject_tab(self, subject_id: str):
        """Switches to the requested subject tab."""
        self.page.evaluate(f'''() => {{
            const tab = document.querySelector(`a[href="#{subject_id}"]`);
            if (tab) tab.click();
        }}''')
        time.sleep(1)

    def extract_visible_question(self) -> Optional[Dict]:
        """Extracts the current visible question on the examination panel."""
        data = self.page.evaluate('''() => {
            // Find question body / options on examinationpanel.php
            const questionBody = document.querySelector('.question-text, .question, #question, .panel-body');
            const options = Array.from(document.querySelectorAll('input[type="radio"], .option, .answers li'));
            
            return {
                url: window.location.href,
                body: questionBody ? questionBody.innerText.trim() : document.body.innerText.slice(0, 1000),
                optionCount: options.length
            };
        }''')
        return data

    def log_question_study(self, q_num: int, q_text: str, answer: str, confidence: str, explanation: str):
        record = {
            "question_number": q_num,
            "question_text": q_text,
            "recommended_answer": answer,
            "confidence": confidence,
            "explanation": explanation,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.session_log.append(record)
        with open("session_study_log.json", "w", encoding="utf-8") as f:
            json.dump(self.session_log, f, indent=2)
        print(f"[+] Logged verification for Question {q_num}")

    def close(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
