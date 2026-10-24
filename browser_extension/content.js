/**
 * AI Exam Assistant Pro - Comprehensive Content Script
 * Extracts:
 * - Current portal status (dashboard, exams, session expiry)
 * - Questions, numbers, options, stems
 * - Handles radio buttons, check boxes, select menus, and text areas
 * - Provides non-invasive inspection
 */

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "EXTRACT_FULL_DATA") {
    try {
      const pageText = document.body ? document.body.innerText : "";
      const isExpired = pageText.includes("session has been expired") || pageText.includes("examination session has been finished");
      const isDashboard = window.location.href.includes("examinationhome") || document.title.includes("Dashboard") || document.title.includes("EXAMIND");

      // 1. Extract exams if on dashboard
      const examTabs = Array.from(document.querySelectorAll('ul.nav-tabs li a, .nav-tabs a, .tab-pane')).map(el => ({
        name: el.innerText.trim(),
        href: el.getAttribute('href') || ''
      })).filter(t => t.name.length > 0);

      // 2. Extract question elements
      const qHeading = document.querySelector('#questionHeading, h2, h3, .panel-title, .question-number, .q-num');
      const qTextEl = document.querySelector('#questionText, .question-text, .question, #question, .question-stem, .form-group label');

      // Options extraction with label matching
      const radioInputs = Array.from(document.querySelectorAll('input[type="radio"], input[type="checkbox"], .option-item, .option, .answers li'));
      const options = [];

      radioInputs.forEach((input, idx) => {
        const label = input.closest('label') || document.querySelector(`label[for="${input.id}"]`) || input.parentElement;
        const text = label ? label.innerText.trim() : (input.value || `Option ${idx + 1}`);
        if (text && !options.includes(text)) {
          options.push(text);
        }
      });

      // If no radio found, check standard list items or selection
      if (options.length === 0) {
        const listItems = Array.from(document.querySelectorAll('.panel-body li, .content li, ol li, ul li')).map(li => li.innerText.trim());
        if (listItems.length >= 2 && listItems.length <= 10) {
          listItems.forEach(item => {
            if (item && !options.includes(item)) options.push(item);
          });
        }
      }

      // Check if user selected highlighted text
      const selectedText = window.getSelection().toString().trim();

      sendResponse({
        success: true,
        url: window.location.href,
        title: document.title,
        isExpired: isExpired,
        isDashboard: isDashboard,
        exams: examTabs,
        heading: qHeading ? qHeading.innerText.trim() : "Current Question",
        question: selectedText || (qTextEl ? qTextEl.innerText.trim() : ""),
        options: options,
        rawSnippet: pageText.slice(0, 400)
      });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
    return true;
  }
});
