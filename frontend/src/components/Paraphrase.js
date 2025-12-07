import React from 'react';
import NavBar from './NavBar';
import Sidebar from './Sidebar';
import './Paraphrase.css';

export default function Paraphrase({ sidebarOpen, setSidebarOpen }) {
  return (
    <div className="par-wrap">
      <NavBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      <div className="par-body">
        <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <section className="par-main">
          <h1 className="par-title">Paraphrase Detection</h1>

          <div className="par-card">
            <label className="lbl-block">Original:</label>
            <div className="original-box" />
            <div className="par-actions">
              <input type="file" className="file-input" />
              <button className="par-check">Check</button>
            </div>
          </div>

          <div className="par-result">
            <div className="result-label">Paraphrase Level</div>
            <div className="result-pill">47%</div>
          </div>
        </section>
      </div>
    </div>
  );
}
