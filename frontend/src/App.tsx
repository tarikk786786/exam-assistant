import React, { useState, useEffect } from 'react';

interface Exam {
  name: string;
  subjectId: string;
  status: string;
  questionCount: string;
}

interface QuestionAnalysis {
  recommended_option?: string;
  confidence?: string;
  explanation?: string;
  reference?: string;
  mode_notice?: string;
  requires_manual_verification?: boolean;
}

interface QuestionData {
  heading?: string;
  question?: string;
  options?: string[];
  analysis?: QuestionAnalysis;
  currentUrl?: string;
}

export default function App() {
  const [browserStatus, setBrowserStatus] = useState<any>({});
  const [exams, setExams] = useState<Exam[]>([]);
  const [activeQuestion, setActiveQuestion] = useState<QuestionData | null>(null);
  const [selectedExam, setSelectedExam] = useState<string>('');
  const [examMode, setExamMode] = useState<string>('learning_support');
  const [userChoice, setUserChoice] = useState<string>('');
  const [isFlagged, setIsFlagged] = useState<boolean>(false);
  const [progress, setProgress] = useState<any>({ total_recorded: 0, reviewed_count: 0, flagged_count: 0 });
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>('');

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/browser/status');
      const data = await res.json();
      setBrowserStatus(data);
    } catch (e) {
      console.error(e);
    }
  };

  const launchBrowser = async () => {
    setLoading(true);
    setMessage('Launching browser & navigating to portal...');
    try {
      const res = await fetch('/api/browser/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ headless: false })
      });
      const data = await res.json();
      setMessage(data.message || 'Browser ready.');
      fetchStatus();
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadExams = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/exams');
      const data = await res.json();
      if (data.exams) {
        setExams(data.exams);
        setMessage(`Found ${data.exams.length} exams on dashboard.`);
      }
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const selectExamSubject = async (ex: Exam) => {
    try {
      const res = await fetch('/api/exams/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject_id: ex.subjectId,
          subject_name: ex.name,
          mode: examMode
        })
      });
      const data = await res.json();
      setSelectedExam(ex.name);
      setMessage(`Selected: ${ex.name} (${examMode === 'learning_support' ? 'Learning Support Mode' : 'Practice Mode'})`);
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    }
  };

  const extractQuestion = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/question/extract');
      const data = await res.json();
      setActiveQuestion(data);
      setUserChoice('');
      setIsFlagged(false);
      setMessage('Question extracted successfully.');
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const saveQuestionReview = async () => {
    if (!activeQuestion) return;
    try {
      await fetch('/api/question/record', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          q_number: 1,
          q_text: activeQuestion.question || '',
          options: activeQuestion.options || [],
          user_selected_option: userChoice,
          ai_recommended_option: activeQuestion.analysis?.recommended_option,
          ai_explanation: activeQuestion.analysis?.explanation,
          confidence: activeQuestion.analysis?.confidence,
          reference: activeQuestion.analysis?.reference,
          is_flagged: isFlagged
        })
      });
      // Refresh progress
      const pRes = await fetch('/api/progress');
      const pData = await pRes.json();
      setProgress(pData);
      setMessage('Saved question review to local audit log.');
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px' }}>
      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1e293b', paddingBottom: '16px' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0, color: '#38bdf8' }}>
            🎓 AI University Exam Assistant
          </h1>
          <p style={{ margin: '4px 0 0 0', color: '#94a3b8', fontSize: '0.9rem' }}>
            Safe, Transparent & Student-Controlled Question Assistance
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <span style={{
            padding: '6px 12px',
            borderRadius: '20px',
            fontSize: '0.8rem',
            fontWeight: 600,
            background: browserStatus.connected ? '#064e3b' : '#334155',
            color: browserStatus.connected ? '#34d399' : '#94a3b8'
          }}>
            {browserStatus.connected ? '● Browser Connected' : '○ Browser Offline'}
          </span>
          <span style={{
            padding: '6px 12px',
            borderRadius: '20px',
            fontSize: '0.8rem',
            fontWeight: 600,
            background: '#1e1b4b',
            color: '#a5b4fc',
            border: '1px solid #3730a3'
          }}>
            🛡️ Human Control Lock Active
          </span>
        </div>
      </header>

      {/* Notification banner */}
      {message && (
        <div style={{ background: '#1e293b', borderLeft: '4px solid #38bdf8', padding: '10px 16px', margin: '16px 0', borderRadius: '4px', fontSize: '0.9rem' }}>
          {message}
        </div>
      )}

      {/* Grid Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px', marginTop: '20px' }}>
        
        {/* Left Sidebar: Controls & Exam List */}
        <aside style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ background: '#111827', padding: '16px', borderRadius: '8px', border: '1px solid #1f2937' }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '1rem', color: '#f3f4f6' }}>Browser Operations</h3>
            <button
              onClick={launchBrowser}
              disabled={loading}
              style={{ width: '100%', padding: '10px', background: '#2563eb', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer', marginBottom: '8px' }}
            >
              1. Open Portal in Browser
            </button>
            <button
              onClick={loadExams}
              disabled={loading}
              style={{ width: '100%', padding: '10px', background: '#374151', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer' }}
            >
              2. Inspect Dashboard Exams
            </button>
          </div>

          <div style={{ background: '#111827', padding: '16px', borderRadius: '8px', border: '1px solid #1f2937' }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '1rem', color: '#f3f4f6' }}>Assistance Mode</h3>
            <select
              value={examMode}
              onChange={(e) => setExamMode(e.target.value)}
              style={{ width: '100%', padding: '8px', background: '#1f2937', color: 'white', border: '1px solid #374151', borderRadius: '4px' }}
            >
              <option value="learning_support">Learning Support Mode (Live Exam)</option>
              <option value="practice_ai">Practice Mode (Authorized AI)</option>
            </select>
            <p style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: '8px' }}>
              In Learning Support Mode, AI provides concept understanding; answer choices remain strictly user-selected.
            </p>
          </div>

          <div style={{ background: '#111827', padding: '16px', borderRadius: '8px', border: '1px solid #1f2937' }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '1rem', color: '#f3f4f6' }}>Detected Exams</h3>
            {exams.length === 0 ? (
              <p style={{ color: '#6b7280', fontSize: '0.85rem' }}>No exams retrieved. Launch browser and click 'Inspect Dashboard Exams'.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {exams.map((ex, i) => (
                  <div
                    key={i}
                    onClick={() => selectExamSubject(ex)}
                    style={{
                      padding: '10px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      background: selectedExam === ex.name ? '#1e3a8a' : '#1f2937',
                      border: '1px solid #374151'
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{ex.name}</div>
                    <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Status: {ex.status}</div>
                    <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Questions: {ex.questionCount}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={{ background: '#111827', padding: '16px', borderRadius: '8px', border: '1px solid #1f2937' }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '1rem', color: '#f3f4f6' }}>Session Progress</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div style={{ background: '#1f2937', padding: '8px', borderRadius: '4px', textAlign: 'center' }}>
                <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#38bdf8' }}>{progress.reviewed_count}</div>
                <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Reviewed</div>
              </div>
              <div style={{ background: '#1f2937', padding: '8px', borderRadius: '4px', textAlign: 'center' }}>
                <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#f87171' }}>{progress.flagged_count}</div>
                <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Flagged</div>
              </div>
            </div>
          </div>
        </aside>

        {/* Right Main Panel: Question Viewer & Verification */}
        <main style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ background: '#111827', padding: '24px', borderRadius: '8px', border: '1px solid #1f2937' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem', color: '#f3f4f6' }}>
                {activeQuestion?.heading || 'Question Workspace'}
              </h2>
              <button
                onClick={extractQuestion}
                disabled={loading}
                style={{ padding: '8px 16px', background: '#0284c7', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer' }}
              >
                📥 Read Active Question from Browser
              </button>
            </div>

            {activeQuestion?.question ? (
              <div>
                <p style={{ fontSize: '1.1rem', lineHeight: '1.6', background: '#1e293b', padding: '16px', borderRadius: '6px', borderLeft: '4px solid #38bdf8' }}>
                  {activeQuestion.question}
                </p>

                <h4 style={{ color: '#cbd5e1', margin: '20px 0 10px 0' }}>Options (Select to mark your answer):</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {activeQuestion.options?.map((opt, i) => {
                    const optLetter = opt.trim().slice(0, 1);
                    return (
                      <label
                        key={i}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          padding: '12px',
                          background: userChoice === optLetter ? '#1e3a8a' : '#1f2937',
                          border: '1px solid #374151',
                          borderRadius: '6px',
                          cursor: 'pointer'
                        }}
                      >
                        <input
                          type="radio"
                          name="userOption"
                          value={optLetter}
                          checked={userChoice === optLetter}
                          onChange={() => setUserChoice(optLetter)}
                        />
                        <span style={{ fontSize: '0.95rem' }}>{opt}</span>
                      </label>
                    );
                  })}
                </div>

                <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginTop: '16px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: '#f87171', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={isFlagged}
                      onChange={(e) => setIsFlagged(e.target.checked)}
                    />
                    Flag for later review
                  </label>
                  <button
                    onClick={saveQuestionReview}
                    style={{ marginLeft: 'auto', padding: '8px 18px', background: '#16a34a', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer' }}
                  >
                    💾 Save to Local Review Log
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
                <p>No active question extracted.</p>
                <p style={{ fontSize: '0.85rem' }}>Open the subject exam in the browser, then click 'Read Active Question from Browser'.</p>
              </div>
            )}
          </div>

          {/* AI Academic Analysis Panel */}
          {activeQuestion?.analysis && (
            <div style={{ background: '#111827', padding: '24px', borderRadius: '8px', border: '1px solid #1f2937' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#a78bfa' }}>
                  📖 AI Academic Verification & Reasoning
                </h3>
                <span style={{
                  padding: '4px 10px',
                  borderRadius: '12px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  background: '#2e1065',
                  color: '#c084fc'
                }}>
                  Confidence: {activeQuestion.analysis.confidence || 'Evaluated'}
                </span>
              </div>

              {activeQuestion.analysis.mode_notice && (
                <div style={{ background: '#451a03', color: '#fed7aa', padding: '8px 12px', borderRadius: '4px', fontSize: '0.85rem', marginBottom: '12px' }}>
                  ⚠️ {activeQuestion.analysis.mode_notice}
                </div>
              )}

              <div style={{ background: '#1e293b', padding: '16px', borderRadius: '6px' }}>
                <p style={{ margin: '0 0 10px 0', fontSize: '0.95rem' }}>
                  <b>Academic Recommendation:</b> Option {activeQuestion.analysis.recommended_option}
                </p>
                <p style={{ margin: '0 0 10px 0', fontSize: '0.9rem', color: '#cbd5e1', lineHeight: '1.5' }}>
                  <b>Detailed Explanation:</b> {activeQuestion.analysis.explanation}
                </p>
                <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8' }}>
                  <b>Reference:</b> <i>{activeQuestion.analysis.reference}</i>
                </p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
