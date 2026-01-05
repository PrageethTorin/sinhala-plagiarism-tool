import React, { useState } from 'react';
import NavBar from './NavBar';
import Sidebar from './Sidebar';
import './WritingStyle.css';

export default function WritingStyle({ sidebarOpen, setSidebarOpen }) {
  const [originalText, setOriginalText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [apiResult, setApiResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const handleAnalyze = async () => {
    if (!originalText.trim()) {
        setErrorMessage("Please enter text to analyze.");
        return;
    }

    setIsLoading(true);
    setErrorMessage('');
    setApiResult(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/check-wsa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: originalText }),
      });

      if (!response.ok) throw new Error("Server error occurred.");
      const data = await response.json();
      setApiResult(data);
    } catch (error) {
      setErrorMessage("Connection to backend failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="ws-wrap">
      <NavBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      <div className="ws-body">
        <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
        <section className="ws-main">
          <h1 className="ws-title">Writing Style Analysis</h1>
          <div className="ws-card">
            <textarea
              className="ws-textbox"
              placeholder="Paste Sinhala text here..."
              value={originalText}
              onChange={(e) => setOriginalText(e.target.value)}
              disabled={isLoading}
            />
            {errorMessage && <div className="ws-error-message">{errorMessage}</div>}
            <div className="ws-actions">
              <button className="ws-analyze-btn" onClick={handleAnalyze} disabled={isLoading}>
                {isLoading ? 'Analyzing...' : 'Analyze Style'}
              </button>
            </div>
          </div>

          {apiResult && (
            <div className="ws-result-container fade-in">
              <div className="ws-result-card">
                <div className="ws-result-label">Style Change Ratio</div>
                <div className="ws-score-pill">{apiResult.style_change_ratio}%</div>
              </div>

              <div className="ws-source-card">
                {apiResult.matched_url === "No source found" ? (
                  <div className="ws-source-not-found">✓ No Matching Idea Found Online.</div>
                ) : (
                  <div className="ws-source-found">
                    <div className="ws-source-alert">⚠️ Plagiarism Detected:</div>
                    <a href={apiResult.matched_url} target="_blank" rel="noreferrer" className="ws-source-link">
                      {apiResult.matched_url}
                    </a>
                  </div>
                )}
              </div>

              {/* Highlighting Section */}
              <div className="ws-highlight-box">
                <h3 className="ws-result-label">Sentence Level Analysis</h3>
                <div className="ws-text-display">
                  {apiResult.sentence_map.map((s) => (
                    <span key={s.id} className={s.is_outlier ? "ws-sentence-flagged" : "ws-sentence-normal"}>
                      {s.text}.{" "}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}