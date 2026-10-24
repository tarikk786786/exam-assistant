"""
FastAPI Dashboard UI for the Exam Browser Assistant
Provides visual control, dashboard status, question breakdown, and safety indicators.
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from engine import ExamAssistantEngine
from config import settings
import uvicorn

app = FastAPI(title="Exam Browser Assistant Web Control")

engine_instance = ExamAssistantEngine(
    login_url=settings.PORTAL_LOGIN_URL,
    student_id=settings.DEFAULT_STUDENT_ID,
    headless=settings.HEADLESS,
    slow_mo=settings.SLOW_MO_MS
)

@app.get("/", response_class=HTMLResponse)
async def dashboard_index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Exam Assistant Dashboard</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 24px; }
            .container { max-width: 1000px; margin: 0 auto; }
            .card { background: #1e293b; border-radius: 8px; padding: 20px; margin-bottom: 20px; border: 1px solid #334155; }
            .badge { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }
            .badge-safe { background: #065f46; color: #6ee7b7; }
            .badge-warn { background: #854d0e; color: #fef08a; }
            button { background: #2563eb; color: white; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; font-weight: 600; margin-right: 8px; }
            button:hover { background: #1d4ed8; }
            .btn-secondary { background: #475569; }
            .btn-secondary:hover { background: #334155; }
            pre { background: #090d16; padding: 15px; border-radius: 6px; overflow-x: auto; color: #38bdf8; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <header style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2>🎓 University Exam Browser Assistant</h2>
                <span class="badge badge-safe">Safety Lock Active (No Auto-Submit)</span>
            </header>

            <div class="card">
                <h3>Controls & Browser Lifecycle</h3>
                <button onclick="apiCall('/api/start')">1. Launch Browser</button>
                <button onclick="apiCall('/api/navigate')">2. Navigate Portal</button>
                <button onclick="apiCall('/api/exams')" class="btn-secondary">3. Fetch Dashboard Exams</button>
                <button onclick="apiCall('/api/question')" class="btn-secondary">4. Inspect Question</button>
            </div>

            <div class="grid">
                <div class="card">
                    <h3>Exam Status & Dashboard</h3>
                    <div id="examStatus">Click 'Fetch Dashboard Exams' to query browser state.</div>
                </div>
                <div class="card">
                    <h3>Active Question Analysis</h3>
                    <div id="questionAnalysis">Click 'Inspect Question' when on a question page.</div>
                </div>
            </div>

            <div class="card">
                <h3>Live Console Output</h3>
                <pre id="consoleLog">Ready.</pre>
            </div>
        </div>

        <script>
            async function apiCall(endpoint) {
                const log = document.getElementById('consoleLog');
                log.innerText = `Calling ${endpoint}...`;
                try {
                    const res = await fetch(endpoint);
                    const data = await res.json();
                    log.innerText = JSON.stringify(data, null, 2);

                    if (endpoint === '/api/exams') {
                        renderExams(data);
                    } else if (endpoint === '/api/question') {
                        renderQuestion(data);
                    }
                } catch (e) {
                    log.innerText = `Error: ${e.message}`;
                }
            }

            function renderExams(data) {
                const el = document.getElementById('examStatus');
                if (!data.exams || data.exams.length === 0) {
                    el.innerHTML = '<p>No exams detected or not yet logged into dashboard.</p>';
                    return;
                }
                let html = '<ul>';
                data.exams.forEach(ex => {
                    html += `<li><b>${ex.name}</b> (${ex.status}) - Questions: ${ex.questionCount}</li>`;
                });
                html += '</ul>';
                el.innerHTML = html;
            }

            function renderQuestion(data) {
                const el = document.getElementById('questionAnalysis');
                if (data.error) {
                    el.innerHTML = `<p style="color:#f87171">${data.error}</p>`;
                    return;
                }
                const q = data.question || "None";
                const ana = data.analysis || {};
                el.innerHTML = `
                    <p><b>Question:</b> ${q}</p>
                    <p><b>Recommended:</b> Option ${ana.recommended_option || 'N/A'}</p>
                    <p><b>Confidence:</b> ${ana.confidence || 'N/A'}</p>
                    <p><b>Explanation:</b> ${ana.explanation || 'N/A'}</p>
                    <p><b>Reference:</b> <i>${ana.reference || 'N/A'}</i></p>
                `;
            }
        </script>
    </body>
    </html>
    """

@app.get("/api/start")
async def api_start():
    try:
        engine_instance.start()
        return {"status": "success", "message": "Browser started"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/navigate")
async def api_navigate():
    try:
        engine_instance.navigate_portal()
        return {
            "status": "success",
            "url": engine_instance.page.url if engine_instance.page else None,
            "authenticated": engine_instance.is_authenticated()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/exams")
async def api_exams():
    try:
        exams = engine_instance.get_dashboard_exams()
        return {
            "status": "success",
            "authenticated": engine_instance.is_authenticated(),
            "exams": exams
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/question")
async def api_question():
    try:
        q_data = engine_instance.extract_current_question()
        return q_data
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=settings.DASHBOARD_PORT)
