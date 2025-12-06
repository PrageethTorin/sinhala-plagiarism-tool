import React from 'react';
import './Sidebar.css';

export default function Sidebar({ sidebarOpen, setSidebarOpen }) {
  return (
    <aside className="side-wrap">
      <nav className="side-nav">
        <a href="#/paraphrase" className="side-btn">Paraphrase Detection</a>
        <a href="#/writing-style-2" className="side-btn">Semantic Similarity</a>
        <a href="#/writing-style-1" className="side-btn">Writing Style</a>
        <a href="#/writing-style-3" className="side-btn">Pretrained Language Models</a>
      </nav>
    </aside>
  );
}
