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
        <a href="#/" className="nav-brand">Sinhala Plagiarism Tool</a>
      </div>

      <button 
        className="nav-hamburger"
        onClick={() => setMenuOpen(!menuOpen)}
        aria-label="Toggle menu"
      >
        <span className={menuOpen ? 'open' : ''}></span>
        <span className={menuOpen ? 'open' : ''}></span>
        <span className={menuOpen ? 'open' : ''}></span>
      </button>

      <div className={`nav-right ${menuOpen ? 'active' : ''}`}>
        <a className="nav-profile" href="#/" onClick={() => setMenuOpen(false)}>Home</a>
        <a className="nav-profile" href="#/" onClick={() => setMenuOpen(false)}>My Profile</a>

        {/* FIXED login link */}
        <a
          href="#/login"
          className="nav-login"
          onClick={() => setMenuOpen(false)}
        >
          Login
        </a>
      </div>
    </header>
  );
}
