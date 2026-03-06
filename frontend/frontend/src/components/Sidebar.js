import React, { useState, useEffect } from 'react';
import './Sidebar.css';

export default function Sidebar({ sidebarOpen, setSidebarOpen }) {
  const [activeItem, setActiveItem] = useState('#/writing-style-2');

  useEffect(() => {
    const updateActive = () => {
      setActiveItem(window.location.hash || '#/');
    };
    window.addEventListener('hashchange', updateActive);
    updateActive();
    return () => window.removeEventListener('hashchange', updateActive);
  }, []);
  return (
    <aside className={`sidebar-wrap ${sidebarOpen ? 'open' : ''}`}>
      <div className="sidebar-logo">
        <div className="logo-dots">
          <span className="dot purple"></span>
          <span className="dot orange"></span>
          <span className="dot yellow"></span>
        </div>
        <span className="logo-text">SINHALA</span>
      </div>

      <button className="sidebar-upgrade">Upgrade</button>

      <div className="sidebar-section">
        <h3 className="sidebar-title">Start Here</h3>

        <nav className="sidebar-menu">

          <a
            href="#/writing-style-2"
            className={`sidebar-item ${activeItem === '#/writing-style-2' ? 'sidebar-active' : ''}`}
            onClick={() => setSidebarOpen(false)}
          >
            <span className="sidebar-icon">🔍</span>
            <span>Semantic Similarity</span>
          </a>

          <a
            href="#/paraphrase"
            className={`sidebar-item ${activeItem === '#/paraphrase' ? 'sidebar-active' : ''}`}
            onClick={() => setSidebarOpen(false)}
          >
            <span className="sidebar-icon">📝</span>
            <span>Paraphrase Detection</span>
          </a>

          <a
            href="#/pretrained"
            className={`sidebar-item ${activeItem === '#/pretrained' ? 'sidebar-active' : ''}`}
            onClick={() => setSidebarOpen(false)}
          >
            <span className="sidebar-icon">🤖</span>
            <span>Pretrained Detection</span>
          </a>

        </nav>
      </div>

      <div className="sidebar-footer">
        <div className="sidebar-divider"></div>
        <p className="sidebar-credit">© 2024 Sinhala Plagiarism Tool</p>
      </div>
    </aside>
  );
}
