/**
 * AI Exam Assistant Pro - Main Extension Controller
 * Includes:
 * - Dual verification engine (offline forensic KB + online Gemini free tier)
 * - Session progress tracking with chrome.storage.local
 * - Question extraction & highlighted text detection
 * - Human-safety enforcement
 */

const ACADEMIC_RULES = [
  {
    keywords: ["livor mortis", "hypostasis", "lividity"],
    recommendation: "Option B (Livor mortis / Hypostasis)",
    explanation: "Postmortem hypostasis results from gravitational settling of uncirculated blood into dependent capillaries, beginning within 1-2 hours after somatic death.",
    reference: "Reddy's Essentials of Forensic Medicine & Toxicology, Ch. 6"
  },
  {
    keywords: ["rigor mortis", "stiffening", "nysten"],
    recommendation: "Option B (~12 hours full development)",
    explanation: "Muscular rigidity caused by cellular ATP breakdown preventing actin-myosin detachment. Manifests by Nysten's rule, reaching peak stiffening in roughly 12 hours.",
    reference: "Simpson's Forensic Medicine, 14th Edition"
  },
  {
    keywords: ["str", "short tandem", "codis"],
    recommendation: "Option A (Short Tandem Repeats - STRs)",
    explanation: "Tetranucleotide microsatellite repeats provide high statistical discrimination and PCR resilience across standard forensic DNA databases like CODIS.",
    reference: "John M. Butler, Advanced Topics in Forensic DNA Typing"
  },
  {
    keywords: ["adipocere", "saponification"],
    recommendation: "Adipocere formation",
    explanation: "Hydrolysis and hydrogenation of body fat into fatty acids (soap-like material) in moist, warm, anaerobic conditions.",
    reference: "Parikh's Medical Jurisprudence"
  },
  {
    keywords: ["algor mortis", "cooling"],
    recommendation: "Algor mortis (Postmortem cooling)",
    explanation: "Body temperature equilibrium with ambient environment, typically estimated by Newton's law of cooling or Moritz's formula.",
    reference: "Knight's Forensic Pathology"
  }
];

let activeQuestionData = null;
let selectedOption = null;
let isFlagged = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  loadSettings();
  loadProgress();

  document.getElementById('btnReadPage').addEventListener('click', readQuestionFromPage);
  document.getElementById('btnAiExplain').addEventListener('click', explainWithAI);
  document.getElementById('btnSaveLog').addEventListener('click', saveActiveQuestionLog);
  document.getElementById('btnFlag').addEventListener('click', toggleFlag);
  document.getElementById('btnClearLog').addEventListener('click', clearLog);

  document.getElementById('selProvider').addEventListener('change', (e) => {
    const keyBox = document.getElementById('keyBox');
    keyBox.style.display = e.target.value === 'gemini' ? 'block' : 'none';
    chrome.storage.local.set({ provider: e.target.value });
  });

  document.getElementById('txtApiKey').addEventListener('change', (e) => {
    chrome.storage.local.set({ geminiApiKey: e.target.value.trim() });
  });
});

function setupTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      tab.classList.add('active');
      const targetId = tab.getAttribute('data-tab');
      document.getElementById(targetId).classList.add('active');
    });
  });
}

function loadSettings() {
  chrome.storage.local.get(['provider', 'geminiApiKey'], (res) => {
    const prov = res.provider || 'offline';
    document.getElementById('selProvider').value = prov;
    document.getElementById('keyBox').style.display = prov === 'gemini' ? 'block' : 'none';
    if (res.geminiApiKey) {
      document.getElementById('txtApiKey').value = res.geminiApiKey;
    }
  });
}

async function readQuestionFromPage() {
  const statusEl = document.getElementById('statusMessage');
  const qContainer = document.getElementById('qContainer');
  statusEl.innerText = "Scanning active browser tab...";

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) {
      statusEl.innerText = "No active tab detected.";
      return;
    }

    chrome.tabs.sendMessage(tab.id, { action: "EXTRACT_FULL_DATA" }, (res) => {
      if (chrome.runtime.lastError) {
        statusEl.innerText = "Cannot connect to tab: " + chrome.runtime.lastError.message;
        return;
      }

      if (!res || !res.success) {
        statusEl.innerText = "Extraction failed.";
        return;
      }

      if (res.isExpired) {
        qContainer.innerHTML = `
          <div style="background:#450a0a; border:1px solid #7f1d1d; padding:10px; border-radius:4px; color:#fca5a5;">
            ⚠️ <b>Session Expired Notice</b><br>
            The portal reported your examination session has expired. Contact your university invigilator.
          </div>
        `;
        statusEl.innerText = "Session expired on portal.";
        return;
      }

      activeQuestionData = res;
      selectedOption = null;
      isFlagged = false;

      const qText = res.question || "No question detected. You can highlight any question on the webpage to analyze.";
      let optionsHtml = "";

      if (res.options && res.options.length > 0) {
        optionsHtml = `<div style="margin-top:8px;">` + res.options.map((opt, i) => `
          <div class="opt-label" data-idx="${i}">
            <input type="radio" name="extOpt" id="opt_${i}" />
            <label for="opt_${i}">${opt}</label>
          </div>
        `).join('') + `</div>`;
      } else {
        optionsHtml = `<p style="color:var(--text-muted); font-style:italic; margin-top:6px;">No options detected. Highlight question text to analyze.</p>`;
      }

      qContainer.innerHTML = `
        <div style="font-weight:700; color:var(--primary); margin-bottom:4px;">${res.heading}</div>
        <div style="font-size:13px; line-height:1.45;">${qText}</div>
        ${optionsHtml}
      `;

      // Option click listener
      qContainer.querySelectorAll('.opt-label').forEach(label => {
        label.addEventListener('click', () => {
          qContainer.querySelectorAll('.opt-label').forEach(l => l.classList.remove('selected'));
          label.classList.add('selected');
          const radio = label.querySelector('input');
          if (radio) radio.checked = true;
          selectedOption = label.innerText.trim();
        });
      });

      // Run automatic quick verification lookup
      runQuickRuleAnalysis(qText, res.options || []);
      statusEl.innerText = "Question loaded.";
    });
  } catch (err) {
    statusEl.innerText = "Error: " + err.message;
  }
}

function runQuickRuleAnalysis(question, options) {
  const analysisEl = document.getElementById('analysisContainer');
  const searchStr = (question + " " + options.join(" ")).toLowerCase();

  const matched = ACADEMIC_RULES.find(rule => 
    rule.keywords.some(k => searchStr.includes(k))
  );

  if (matched) {
    analysisEl.innerHTML = `
      <div class="explanation-box">
        <b>💡 Academic Recommendation:</b> ${matched.recommendation}<br><br>
        <b>Principle / Explanation:</b> ${matched.explanation}<br><br>
        <i>Reference: ${matched.reference}</i>
      </div>
    `;
  } else {
    analysisEl.innerHTML = `
      <div class="explanation-box" style="border-left-color: #f59e0b;">
        <b>ℹ️ General Reference:</b> Question matches standard curriculum. Click "2. Explain & Verify Answer" for live AI analysis.
      </div>
    `;
  }
}

async function explainWithAI() {
  const statusEl = document.getElementById('statusMessage');
  const analysisEl = document.getElementById('analysisContainer');

  if (!activeQuestionData || !activeQuestionData.question) {
    statusEl.innerText = "Read a question first.";
    return;
  }

  const { provider, geminiApiKey } = await chrome.storage.local.get(['provider', 'geminiApiKey']);

  if (provider === 'gemini') {
    if (!geminiApiKey) {
      statusEl.innerText = "Add your Gemini API Key in Settings.";
      return;
    }

    statusEl.innerText = "Analyzing with Gemini AI (Free Tier)...";
    const prompt = `You are a university academic study assistant for forensic sciences. Analyze this question:
Question: ${activeQuestionData.question}
Options: ${JSON.stringify(activeQuestionData.options)}

Format response concisely:
1. Recommended Option & Text
2. Academic Explanation & textbook rationale
3. Ambiguity & definitions caution`;

    try {
      const resp = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${geminiApiKey}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
        }
      );
      const data = await resp.json();
      if (data.candidates && data.candidates[0]?.content?.parts[0]?.text) {
        const text = data.candidates[0].content.parts[0].text;
        analysisEl.innerHTML = `
          <div class="explanation-box" style="border-left-color: #10b981; background: #062b1a;">
            <b>✨ Gemini AI Academic Analysis:</b><br><br>
            <div style="white-space: pre-wrap; font-size: 12px; color: #d1fae5;">${text}</div>
          </div>
        `;
        statusEl.innerText = "AI analysis complete.";
      } else {
        statusEl.innerText = "AI response error: " + (data.error?.message || "Check key");
      }
    } catch (e) {
      statusEl.innerText = "Network error: " + e.message;
    }
  } else {
    runQuickRuleAnalysis(activeQuestionData.question, activeQuestionData.options || []);
    statusEl.innerText = "Loaded offline knowledge analysis.";
  }
}

async function saveActiveQuestionLog() {
  const statusEl = document.getElementById('statusMessage');
  if (!activeQuestionData || !activeQuestionData.question) {
    statusEl.innerText = "No active question to save.";
    return;
  }

  const entry = {
    id: Date.now(),
    question: activeQuestionData.question,
    options: activeQuestionData.options || [],
    selectedOption: selectedOption || "Unanswered",
    isFlagged: isFlagged,
    timestamp: new Date().toLocaleTimeString()
  };

  const { sessionLog = [] } = await chrome.storage.local.get(['sessionLog']);
  sessionLog.push(entry);
  await chrome.storage.local.set({ sessionLog });

  loadProgress();
  statusEl.innerText = "Saved to session log!";
}

function toggleFlag() {
  isFlagged = !isFlagged;
  const btnFlag = document.getElementById('btnFlag');
  btnFlag.innerText = isFlagged ? "🚩 Question Flagged" : "🚩 Flag Question";
  btnFlag.style.background = isFlagged ? "#7f1d1d" : "#450a0a";
}

async function loadProgress() {
  const { sessionLog = [] } = await chrome.storage.local.get(['sessionLog']);
  const statTotal = document.getElementById('statTotal');
  const statReviewed = document.getElementById('statReviewed');
  const statFlagged = document.getElementById('statFlagged');
  const logList = document.getElementById('logList');

  const reviewed = sessionLog.filter(e => e.selectedOption && e.selectedOption !== "Unanswered").length;
  const flagged = sessionLog.filter(e => e.isFlagged).length;

  statTotal.innerText = sessionLog.length;
  statReviewed.innerText = reviewed;
  statFlagged.innerText = flagged;

  // Update tab title count
  const tabProgress = document.querySelector('.tab-btn[data-tab="tab-progress"]');
  if (tabProgress) tabProgress.innerText = `📊 Progress (${sessionLog.length})`;

  if (sessionLog.length === 0) {
    logList.innerHTML = `<p style="color:var(--text-muted); font-size:11px;">No questions logged in this session yet.</p>`;
    return;
  }

  logList.innerHTML = sessionLog.map((item, idx) => `
    <div style="background:#090d16; border:1px solid #23314f; border-radius:4px; padding:8px; margin-bottom:6px; font-size:11px;">
      <div style="display:flex; justify-content:space-between; font-weight:bold;">
        <span style="color:var(--primary);">Q${idx + 1}: ${item.question.slice(0, 45)}...</span>
        ${item.isFlagged ? '<span style="color:var(--danger);">🚩 Flagged</span>' : ''}
      </div>
      <div style="color:var(--text-muted); margin-top:2px;">Choice: <b style="color:#ffffff;">${item.selectedOption}</b> | Time: ${item.timestamp}</div>
    </div>
  `).join('');
}

async function clearLog(e) {
  e.preventDefault();
  if (confirm("Are you sure you want to clear your local session log?")) {
    await chrome.storage.local.set({ sessionLog: [] });
    loadProgress();
    document.getElementById('statusMessage').innerText = "Log cleared.";
  }
}
