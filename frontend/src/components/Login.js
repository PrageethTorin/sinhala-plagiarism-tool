import React from 'react';
import './Login.css';

export default function Login() {
  return (
    <div className="login-page">
      <div className="login-card">
        <h2 className="login-title">Sign in</h2>
        <p className="login-sub">Access the Sinhala Plagiarism Tool</p>

        <form className="login-form" onSubmit={(e) => e.preventDefault()}>
          <label className="lbl">Email</label>
          <input className="input" type="email" placeholder="you@example.com" />

          <label className="lbl">Password</label>
          <input className="input" type="password" placeholder="••••••••" />

          <button className="submit">Login</button>
        </form>
      </div>
    </div>
  );
}
