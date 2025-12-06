import React, { useState } from 'react';
import './NavBar.css';

export default function NavBar({ sidebarOpen, setSidebarOpen }) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="navbar">
      <button 
        className="sidebar-toggle-nav"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label="Toggle sidebar"
      >
        ☰
      </button>

      <div className="nav-left">
        <div className="nav-brand">Sinhala Plagiarism Tool</div>
      </div>

      <div className="nav-right">
        <a className="nav-profile" href="#/">Home</a>
        <a className="nav-profile" href="#/">My Profile</a>
          <button
          className="nav-login"
          onClick={() => setMenuOpen(false)}
        >
          Login1
        </button>
      </div>
    </header>
  );
}
