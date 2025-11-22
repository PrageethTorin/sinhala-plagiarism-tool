import React from 'react';
import './NavBar.css';

export default function NavBar() {
  return (
    <header className="navbar">
      <div className="nav-left">
        <div className="nav-brand">Sinhala Plagiarism Tool</div>
      </div>

      <div className="nav-right">
        <a className="nav-profile" href="#/">Home</a>
        <a className="nav-profile" href="#/">My Profile</a>
        <button
          className="nav-login"
          onClick={() => {
            // navigate to login page via hash router
            window.location.hash = '#/login';
          }}
        >
          Login
        </button>
      </div>
    </header>
  );
}
