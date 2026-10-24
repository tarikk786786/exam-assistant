# AI University Exam Assistant

A secure, reliable, browser-assisted examination preparation and question verification system built with **FastAPI**, **Playwright**, and **React + Vite**.

---

## 🏛️ Portal Details
- **Portal URL:** `http://13.228.179.22/examsignin.php?session=true`
- **Dashboard URL:** `http://13.228.179.22/onlineexamination/examinationhome.php`
- **Student ID:** `SRU202300876314`

---

## 🛡️ Core Security & Safety Policies
1. **Student-Controlled Submissions:** The assistant **never** autonomously selects live exam answers, skips through questions, or submits live assessments. Final submissions and option selections remain entirely under human control.
2. **Secure Credentials:** Passwords, OTPs, and authentication tokens are **never** hardcoded, stored in logs, or written to disk. The student inputs credentials directly into the browser window.
3. **Transparent Uncertainty:** The verification engine highlights uncertainty, cites relevant reference literature, and flags questions requiring manual verification.
4. **Dual Modes:**
   - **Learning Support Mode (Default):** Explains concepts, outlines principles, and helps clarify terminology without taking over the assessment.
   - **Authorized Practice Mode:** For verified mock exams and practice tests where AI assistance is explicitly authorized.

---

## 🚀 Quick Start (Windows PowerShell)

### 1. Install Backend Dependencies
```powershell
cd "c:\Users\tarik\Desktop\MY TOOLS\apps\exam_assistant"
pip install -r requirements.txt
playwright install chromium
```

### 2. Run the Backend API
```powershell
python backend.py
```
*Backend runs on `http://127.0.0.1:8000`*

### 3. Run Automated Tests with Mock Portal
```powershell
pytest test_assistant.py -v
```

### 4. (Optional) Run the React Frontend
```powershell
cd frontend
npm install
npm run dev
```
*Frontend runs on `http://localhost:5173`*

---

## 📁 Architecture Overview
- `engine.py`: Playwright browser automation and question extraction engine.
- `backend.py`: FastAPI REST API managing browser status, exams, question analysis, and safety locks.
- `storage.py`: SQLite local audit store (`exam_progress.db`) tracking reviewed questions and user flags.
- `mock_server.py`: Synthetic test portal replicating the exact forms, DOM structure, and examination panel.
- `test_assistant.py`: Pytest automated verification suite testing login, extraction, and human safety controls.
- `frontend/`: Modern responsive React + TypeScript interface for review and progress monitoring.
