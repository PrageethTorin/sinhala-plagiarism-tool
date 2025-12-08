import React, { useState } from 'react';
import NavBar from './NavBar';
import Sidebar from './Sidebar';
import './WritingStyle.css';

export default function WritingStyle({ sidebarOpen, setSidebarOpen }) {
  const [originalText, setOriginalText] = useState('');

  return (
    <div className="ws-wrap">
      <NavBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      <div className="ws-body">
        <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <section className="ws-main">
          <h1 className="ws-title">Writing Style Analysis</h1>

          <div className="ws-card">
            <label className="ws-label">Original Text:</label>
            <textarea
              className="ws-textbox"
              placeholder="Paste your Sinhala text here (max 2000 characters)..."
              value={originalText}
              onChange={(e) => setOriginalText(e.target.value.slice(0, 2000))}
              rows={10}
            />
            <div className="ws-actions">
              <input type="file" className="ws-file-input" accept=".txt,.docx" />
              <button className="ws-analyze-btn">Analyze Style</button>
            </div>
          </div>

          <div className="ws-result">
            <div className="ws-result-label">Style Score</div>
            <div className="ws-score-pill">87%</div>
            <div className="ws-metrics">
              <span>Vocabulary Diversity: High</span>
              <span>Sentence Complexity: Medium</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
