import React from 'react';
import './NavBar.css';

export default function NavBar() {
  return (
    <header className="navbar">
      <div className="nav-left">
        <div className="nav-brand">Sinhala Plagiarism Tool</div>
      </div>

      <div className="nav-right">
        <span className="nav-profile">My profile</span>
        <button className="nav-login">Login</button>
      </div>
    </header>
  );
}
