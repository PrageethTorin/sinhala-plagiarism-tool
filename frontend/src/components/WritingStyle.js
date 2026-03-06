import React, { useState } from 'react';
import NavBar from './NavBar';
import Sidebar from './Sidebar';
import './WritingStyle.css';

export default function WritingStyle({ sidebarOpen, setSidebarOpen }) {
  const [originalText, setOriginalText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [apiResult, setApiResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  // PANEL REQUIREMENT: Interactive Word Replacement
  // This function allows the user to manually normalize the style
  const handleReplace = (originalWord, replacement) => {
    // Replace the specific formal word in the source text
    const updatedText = originalText.replace(originalWord, replacement);
    setOriginalText(updatedText);
    
    // Auto-analyze the updated text
    setTimeout(() => {
      analyzeText(updatedText);
    }, 300);
  };

  // Auto-analyze helper function
  const analyzeText = async (textToAnalyze) => {
    if (!textToAnalyze.trim()) {
      setErrorMessage("Please enter text to analyze.");
      return;
    }

    setIsLoading(true);
    setErrorMessage('');

    try {
      const response = await fetch('http://127.0.0.1:8000/api/check-wsa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: textToAnalyze }),
      });

      if (!response.ok) throw new Error("Server communication failed.");
      const data = await response.json();
      console.log("✅ API Response:", data);
      setApiResult(data);
    } catch (error) {
      console.error("❌ Error:", error);
      setErrorMessage(error.message || "Connection to backend failed.");
    } finally {
      setIsLoading(false);
    }
  };

  // Copy output text to clipboard
  const handleCopy = () => {
    if (!apiResult?.ratio_data?.sentence_map) {
      setErrorMessage("Nothing to copy. Please analyze text first.");
      return;
    }

    const textToCopy = apiResult.ratio_data.sentence_map
      .map(s => s.words?.map(w => w.text).join('') || '')
      .join('\n');

    navigator.clipboard.writeText(textToCopy).then(() => {
      alert('✅ Text copied to clipboard!');
    }).catch(() => {
      setErrorMessage('Failed to copy text.');
    });
  };

  // Clear input and refresh
  const handleClear = () => {
    setOriginalText('');
    setApiResult(null);
    setErrorMessage('');
    window.location.reload();
  };

  const handleAnalyze = async () => {
    await analyzeText(originalText);
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
              <button className="ws-clear-btn" onClick={handleClear}>
                Clear Input
              </button>
            </div>
          </div>

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
                <div className="ws-header-with-copy">
                  <h3 className="ws-result-label">Granular Stylistic Analysis</h3>
                  <button className="ws-copy-btn" onClick={handleCopy} title="Copy analyzed text">
                    📋 Copy
                  </button>
                </div>
                <div className="ws-text-display">
                  {apiResult.ratio_data.sentence_map?.map((s) => (
                    <span 
                      key={s.id} 
                      className={s.is_outlier ? "ws-sentence-flagged" : "ws-sentence-normal"}
                    >
                      
{s.words?.map((word, idx) => (
  <span key={idx} className="ws-interactive-word-wrapper">
    <span className={word.is_style_shift ? "ws-word-formal" : ""}>
      {word.text}{' '}
    </span>

    {/* TOOLTIP LOGIC */}
    {word.is_style_shift && word.suggestions?.length > 0 && (
      <div className="ws-synonym-popover">
        <div className="popover-title">Suggestions:</div>
        {word.suggestions.map((syn, sIdx) => (
          <button 
            key={sIdx} 
            className="synonym-item-btn"
            onClick={() => handleReplace(word.text.trim(), syn)}
          >
            {syn}
          </button>
        ))}
      </div>
    )}
  </span>
))}
                    </span>
                  ))}
                </div>
                <div className="ws-legend">
                   <div className="legend-item"><span className="box flagged-bg"></span> Sentence Outlier</div>
                   <div className="legend-item"><span className="wavy-line">~~~~</span> Formal Shift (Hover to Replace)</div>
                </div>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}