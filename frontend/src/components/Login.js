import React from 'react';
import './Login.css';

export default function Login() {
  return (
    <div className="login-container">
      <div className="login-modal" role="dialog" aria-labelledby="login-title">
        <h2 id="login-title" className="login-title">Login</h2>
        <p style={{ color: '#d1cfe0', textAlign: 'center', marginTop: '20px' }}>
          Login functionality is not available.
        </p>
        <a href="#/" className="btn-continue" style={{ display: 'block', textAlign: 'center', marginTop: '20px', textDecoration: 'none' }}>
          Go to Home
        </a>
      </div>
    </div>
  );
}
