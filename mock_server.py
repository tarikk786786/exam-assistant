"""
Mock Portal Web Server for testing and verification.
Simulates:
1. Login form with Student ID & password
2. Exam dashboard with active & finished subject tabs
3. Question panel with questions, options, timer, and human submission button
"""

from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn

mock_app = FastAPI(title="Mock Exam Portal")

MOCK_USERS = {
    "SRU202300876314": "testpass123",
    "TESTSTUDENT": "password"
}

# In-memory mock sessions
MOCK_SESSIONS = set()

SAMPLE_QUESTIONS = [
    {
        "id": 1,
        "subject": "BSFS602 Forensic Medicine",
        "question": "Which of the following signs is the most definitive early postmortem change?",
        "options": {
            "A": "Rigor mortis",
            "B": "Livor mortis (hypostasis)",
            "C": "Algor mortis",
            "D": "Adipocere formation"
        },
        "correct": "B",
        "explanation": "Livor mortis begins immediately upon circulatory cessation (typically visible in 1-2 hours) as blood settles gravitationally, representing an established early indicator."
    },
    {
        "id": 2,
        "subject": "BSFS602 Forensic Medicine",
        "question": "What is the typical timeframe for rigor mortis to fully develop in temperate climates?",
        "options": {
            "A": "1-2 hours",
            "B": "12 hours",
            "C": "36-48 hours",
            "D": "72 hours"
        },
        "correct": "B",
        "explanation": "According to Nysten's rule and standard forensic texts, rigor mortis typically takes approximately 12 hours to establish completely, persists for 12 hours, and recedes over the next 12 hours."
    },
    {
        "id": 3,
        "subject": "BSFS604 DNA Typing",
        "question": "Which genetic markers are most standardly utilized in forensic CODIS databases?",
        "options": {
            "A": "Short Tandem Repeats (STRs)",
            "B": "Single Nucleotide Polymorphisms (SNPs)",
            "C": "Restriction Fragment Length Polymorphisms (RFLPs)",
            "D": "Mitochondrial D-loop sequencing"
        },
        "correct": "A",
        "explanation": "Tetranucleotide and pentanucleotide STRs are the primary core markers utilized across international criminal DNA databases such as CODIS due to their high power of discrimination and robust PCR amplification."
    }
]

@mock_app.get("/examsignin.php", response_class=HTMLResponse)
async def login_page(session: str = "true"):
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Sign in</title></head>
    <body>
        <h2>Student Login</h2>
        <form action="/examlogin.php" method="POST">
            <div>
                <label>User Id</label>
                <input type="text" id="txtUserId" name="txtUserId" placeholder="User Id" required />
            </div>
            <div>
                <label>Password</label>
                <input type="password" id="txtPass" name="txtPass" placeholder="Password" required />
            </div>
            <div>
                <input type="submit" value="Login" />
            </div>
        </form>
    </body>
    </html>
    """

@mock_app.post("/examlogin.php")
async def login_submit(txtUserId: str = Form(...), txtPass: str = Form(...)):
    if txtUserId in MOCK_USERS and MOCK_USERS[txtUserId] == txtPass:
        MOCK_SESSIONS.add(txtUserId)
        resp = RedirectResponse(url="/onlineexamination/examinationhome.php", status_code=303)
        resp.set_cookie(key="mock_sess", value=txtUserId)
        return resp
    return HTMLResponse("<h3>Invalid credentials. <a href='/examsignin.php'>Try again</a></h3>", status_code=401)

@mock_app.get("/onlineexamination/examinationhome.php", response_class=HTMLResponse)
async def examination_home(request: Request):
    user = request.cookies.get("mock_sess")
    if not user or user not in MOCK_SESSIONS:
        return RedirectResponse(url="/examsignin.php")
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>EXAMIND</title>
        <style>
            .tab-content { border: 1px solid #ccc; padding: 15px; margin-top: 10px; }
            .nav-tabs { display: flex; list-style: none; padding: 0; gap: 10px; }
            .nav-tabs li a { padding: 8px 12px; background: #eee; text-decoration: none; border-radius: 4px; }
            .nav-tabs li a.active { background: #007bff; color: white; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>SUNRISE UNIVERSITY, ALWAR</h1>
            <p>Online Examination Dashboard</p>
            <a href="/logout.php">Log Out</a>
        </div>

        <ul class="nav-tabs">
            <li><a href="#12294" class="nav-link">BSFS601 Forensic Anthropology</a></li>
            <li><a href="#12295" class="nav-link active">BSFS602 Forensic Medicine</a></li>
            <li><a href="#12296" class="nav-link">BSFS603 Accident Investigation</a></li>
            <li><a href="#12297" class="nav-link">BSFS604 DNA Typing</a></li>
        </ul>

        <div class="tab-content">
            <div id="12294" class="tab-pane">
                <p>Examination for this subject has been finished.</p>
            </div>
            <div id="12295" class="tab-pane active in" style="display:block;">
                <div class="text-center">
                    No. of Questions:<b>60</b><br><br>
                    <input type="button" class="btn btn-success" id="btnStartExam" onclick="window.location.href='/onlineexamination/examinationpanel.php?subjectId=12295'" value="Start Exam. Wish you a good luck!" />
                </div>
            </div>
            <div id="12296" class="tab-pane" style="display:none;">
                <div class="text-center">
                    No. of Questions:<b>60</b><br><br>
                    <input type="button" class="btn btn-success" onclick="window.location.href='/onlineexamination/examinationpanel.php?subjectId=12296'" value="Start Exam. Wish you a good luck!" />
                </div>
            </div>
            <div id="12297" class="tab-pane" style="display:none;">
                <div class="text-center">
                    No. of Questions:<b>60</b><br><br>
                    <input type="button" class="btn btn-success" onclick="window.location.href='/onlineexamination/examinationpanel.php?subjectId=12297'" value="Start Exam. Wish you a good luck!" />
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@mock_app.get("/onlineexamination/examinationpanel.php", response_class=HTMLResponse)
async def examination_panel(subjectId: str = "12295", qIndex: int = 1):
    q_data = SAMPLE_QUESTIONS[(qIndex - 1) % len(SAMPLE_QUESTIONS)]
    
    options_html = "".join([
        f'<div class="option-item"><label><input type="radio" name="optAnswer" value="{k}"> <b>{k}.</b> {v}</label></div>'
        for k, v in q_data["options"].items()
    ])
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Examination Panel - {q_data['subject']}</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; }}
            .question-box {{ border: 1px solid #007bff; padding: 20px; border-radius: 6px; max-width: 800px; }}
            .option-item {{ margin: 10px 0; }}
            .btn-nav {{ padding: 8px 16px; margin-right: 10px; cursor: pointer; }}
            .btn-danger {{ background: #dc3545; color: white; border: none; padding: 8px 16px; }}
        </style>
    </head>
    <body>
        <h2>Online Examination: {q_data['subject']}</h2>
        <div class="question-box">
            <h3 id="questionHeading">Question {qIndex} of 60</h3>
            <div id="questionText" class="question-text" style="font-size: 1.1em; margin-bottom: 15px;">
                {q_data['question']}
            </div>
            <div id="optionsContainer">
                {options_html}
            </div>
            <hr>
            <div class="controls">
                <a class="btn-nav" href="/onlineexamination/examinationpanel.php?subjectId={subjectId}&qIndex={max(1, qIndex - 1)}">&laquo; Previous</a>
                <a class="btn-nav" href="/onlineexamination/examinationpanel.php?subjectId={subjectId}&qIndex={min(60, qIndex + 1)}">Next &raquo;</a>
                <button type="button" class="btn-danger" id="btnFinalSubmit" onclick="if(confirm('Are you sure you want to finish the exam?')) alert('Submitted!');">Final Submit</button>
            </div>
        </div>
    </body>
    </html>
    """

@mock_app.get("/logout.php")
async def logout(request: Request):
    user = request.cookies.get("mock_sess")
    if user in MOCK_SESSIONS:
        MOCK_SESSIONS.remove(user)
    resp = RedirectResponse(url="/examsignin.php")
    resp.delete_cookie("mock_sess")
    return resp

if __name__ == "__main__":
    uvicorn.run(mock_app, host="127.0.0.1", port=8089)
