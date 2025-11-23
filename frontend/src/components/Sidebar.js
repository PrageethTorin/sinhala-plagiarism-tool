import React from 'react';
import './Sidebar.css';

export default function Sidebar({ sidebarOpen, setSidebarOpen }) {
  return (
    <aside className={`side-wrap ${sidebarOpen ? 'active' : ''}`}>
      <nav className="side-nav">
        <a href="#/paraphrase" className="side-btn" onClick={() => setSidebarOpen(false)}>Paraphrase Detection</a>
        <a href="#/writing-style-2" className="side-btn" onClick={() => setSidebarOpen(false)}>Semantic Similarity</a>
        <a href="#/writing-style-1" className="side-btn" onClick={() => setSidebarOpen(false)}>Writing Style</a>
        <a href="#/writing-style-3" className="side-btn" onClick={() => setSidebarOpen(false)}>Pretrained Language Models</a>
      </nav>
    </aside>
  );
}
