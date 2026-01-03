import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import './NavBar.css';

export default function NavBar({ sidebarOpen, setSidebarOpen }) {
  const { user, isAuthenticated, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = () => {
    setMenuOpen(false);
    logout();
  };

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

        {isAuthenticated ? (
          <>
            <span className="nav-user-email">{user?.email}</span>
            <button
              className="nav-logout-btn"
              onClick={handleLogout}
            >
              Logout
            </button>
          </>
        ) : (
          <a
            href="#/login"
            className="nav-login"
            onClick={() => setMenuOpen(false)}
          >
            Login
          </a>
        )}
      </div>
    </header>
  );
}
