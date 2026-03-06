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

      if (!response.ok) throw new Error("Server communication failed.");
      const data = await response.json();
      
      // Debug: log the response
      console.log("✅ API Response:", data);
      console.log("✅ Has ratio_data:", !!data?.ratio_data);
      
      // Store the result which now contains ratio_data
      setApiResult(data);
    } catch (error) {
      console.error("❌ Error:", error);
      setErrorMessage(error.message || "Connection to backend failed.");
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

          {/* FIXED: Using Optional Chaining and deep pathing */}
          {apiResult?.ratio_data && (
            <div className="ws-result-container fade-in">
              <div className="ws-result-card">
                <div className="ws-result-label">Style Change Ratio</div>
                <div className="ws-score-pill">{apiResult.ratio_data.style_change_ratio}%</div>
              </div>

              <div className="ws-source-card">
                <div className="ws-source-alert">
                  <span className="ws-icon">🔍</span> Status Report:
                </div>
                <div className="ws-source-link-box">
                  {apiResult.ratio_data.matched_url?.startsWith('http') ? (
                    <a href={apiResult.ratio_data.matched_url} target="_blank" rel="noreferrer" className="ws-source-link">
                      {apiResult.ratio_data.matched_url}
                    </a>
                  ) : (
                    <span className="ws-internal-label">
                      {apiResult.ratio_data.matched_url} ({apiResult.ratio_data.similarity_score}%)
                    </span>
                  )}
                </div>
              </div>

              <div className="ws-highlight-box">
                <h3 className="ws-result-label">Granular Stylistic Analysis</h3>
                <div className="ws-text-display">
                  {/* Mapping through ratio_data.sentence_map to prevent crash */}
                  {apiResult.ratio_data.sentence_map?.map((s) => (
                    <span 
                      key={s.id} 
                      className={s.is_outlier ? "ws-sentence-flagged" : "ws-sentence-normal"}
                    >
                      {/* Mapping through individual words for wavy underlines */}
                      {s.words?.map((word, idx) => (
                        <span 
                          key={idx} 
                          className={word.is_style_shift ? "ws-word-formal" : ""}
                        >
                          {word.text}{' '}
                        </span>
                      ))}
                    </span>
                  ))}
                </div>
                <div className="ws-legend">
                   <div className="legend-item"><span className="box flagged-bg"></span> Sentence Level Outlier</div>
                   <div className="legend-item"><span className="wavy-line">~~~~</span> Morphological Complexity</div>
                </div>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}