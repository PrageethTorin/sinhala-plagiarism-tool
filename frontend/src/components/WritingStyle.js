import React, { useState } from 'react';
import NavBar from './NavBar';
import Sidebar from './Sidebar';
import './WritingStyle.css';

export default function WritingStyle({ sidebarOpen, setSidebarOpen }) {
  const [originalText, setOriginalText] = useState('');
  // New states for handling API interactions
  const [isLoading, setIsLoading] = useState(false);
  const [apiResult, setApiResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const handleAnalyze = async () => {
    // 1. Basic validation
    if (!originalText.trim() || originalText.length < 50) {
        setErrorMessage("Please enter at least 50 characters to analyze.");
        return;
    }

    // 2. Reset states before requesting
    setIsLoading(true);
    setErrorMessage('');
    setApiResult(null);

    try {
      // 3. Connect to the Backend API
      // Ensure this URL matches your running FastAPI server address and port
      const response = await fetch('http://127.0.0.1:8000/api/check-wsa', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: originalText }),
      });

      if (!response.ok) {
        throw new Error(`Server Error: ${response.statusText}`);
      }

      const data = await response.json();
      // 4. Store the result data
      setApiResult(data);

    } catch (error) {
      console.error("Analysis failed:", error);
      setErrorMessage("Failed to connect to the analysis server. Please try again.");
    } finally {
      // 5. Stop loading regardless of outcome
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
            <label className="ws-label">Sinhala Text Input:</label>
            <textarea
              className="ws-textbox"
              placeholder="Paste your Sinhala text here for analysis..."
              value={originalText}
              onChange={(e) => setOriginalText(e.target.value.slice(0, 3000))} // Increased limit slightly
              rows={10}
              disabled={isLoading}
            />
            
            {/* Error Message Display */}
            {errorMessage && (
                <div className="ws-error-message">
                    {errorMessage}
                </div>
            )}

            <div className="ws-actions">
              {/* File input kept for UI consistency, though not hooked up yet */}
              <input type="file" className="ws-file-input" accept=".txt,.docx" disabled={isLoading} />
              
              <button 
                  className="ws-analyze-btn" 
                  onClick={handleAnalyze}
                  disabled={isLoading || originalText.length === 0}
              >
                {isLoading ? 'Analyzing...' : 'Analyze Style'}
              </button>
            </div>
          </div>

          {/* Conditional Rendering of Results */}
          {apiResult && !isLoading && (
            <div className="ws-result-container fade-in">
              
              {/* 1. Writing Style Changed Percentage */}
              <div className="ws-result-card">
                 <div className="ws-result-label">Style Change Percentage</div>
                 <div className="ws-score-pill">
                    {apiResult.style_change_ratio}%
                 </div>
              </div>

              {/* 2. Source Idea Matching Logic */}
              <div className="ws-source-card">
                {apiResult.matched_url === "No source found" ? (
                    // Case A: No matching idea found
                    <div className="ws-source-not-found">
                        <span className="ws-icon">✓</span> Not Found Out Source Idea Matching.
                    </div>
                ) : (
                    // Case B: Idea matched an external source
                    <div className="ws-source-found">
                        <div className="ws-source-alert">
                           <span className="ws-icon">⚠️</span> Detect Plaigiarisam And same Idea web Site URL:
                        </div>
                        <a 
                           href={apiResult.matched_url} 
                           target="_blank" 
                           rel="noopener noreferrer"
                           className="ws-source-link"
                        >
                           {apiResult.matched_url}
                        </a>
                    </div>
                )}
              </div>

            </div>
          )}
        </section>
      </div>
    </div>
  );
}