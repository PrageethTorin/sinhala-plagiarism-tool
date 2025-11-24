import React from 'react';
import NavBar from './NavBar';
import Sidebar from './Sidebar';
import './SemanticSimilarity.css';

export default function SemanticSimilarity({ sidebarOpen, setSidebarOpen }) {
  return (
    <div className="semantic-wrap">
      <NavBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      <div className="semantic-body">
        <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <section className="semantic-main">
          <h1 className="semantic-title">Semantic Similarity</h1>

          <div className="semantic-card">
            <label className="lbl-block">Original:</label>
            <div className="text-box" />
            <div className="semantic-actions">
              <input type="file" className="file-input" />
              <button className="semantic-check">Check</button>
            </div>
          </div>


          <div className="semantic-result">
            <div className="result-label">Similarity Score</div>
            <div className="result-pill">75%</div>
          </div>
        </section>
      </div>
    </div>
  );
}
