import React, { useState } from 'react';
import './Login.css';

export default function Login({ onSubmit }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const validateEmail = (e) => /\S+@\S+\.\S+/.test(e);

  function handleContinue(e) {
    e.preventDefault();
    setError('');
    if (!email) {
      setError('Email is required');
      return;
    }
    if (!validateEmail(email)) {
      setError('Enter a valid email');
      return;
    }
    if (!password) {
      setError('Password is required');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    if (onSubmit) onSubmit(email, password);
    console.log('Login with', email, password);
  }

  function handleOAuth(provider) {
    console.log('OAuth:', provider);
  }

  return (
    <div className="login-container">
      <div className="login-modal" role="dialog" aria-labelledby="login-title">
        <h2 id="login-title" className="login-title">Sign in</h2>
        <a className="login-create" href="#/">I don't have an account</a>

        <form className="login-form" onSubmit={handleContinue}>
          <label className="lbl-block" htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            className="login-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@example.com"
            autoComplete="email"
          />

          <label className="lbl-block" htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            className="login-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            autoComplete="current-password"
          />

          {error && <div className="login-error">{error}</div>}

          <button type="submit" className="btn-continue">Continue</button>
        </form>

        <a className="login-help" href="#/">Can't sign in?</a>

        <div className="oauth-list">
          <button type="button" className="oauth-btn" onClick={() => handleOAuth('google')}>
            <span className="oauth-icon">G</span> Sign in with Google
          </button>
          <button type="button" className="oauth-btn" onClick={() => handleOAuth('facebook')}>
            <span className="oauth-icon">f</span> Sign in with Facebook
          </button>
          <button type="button" className="oauth-btn" onClick={() => handleOAuth('apple')}>
            <span className="oauth-icon"></span> Sign in with Apple
          </button>
          <button type="button" className="oauth-btn" onClick={() => handleOAuth('sso')}>
            <span className="oauth-icon">🔒</span> Sign in with Single Sign-On
          </button>
        </div>

        <p className="recaptcha-note">
          This site is protected by reCAPTCHA and the Google Privacy Policy and Terms of Service apply.
        </p>
      </div>
    </div>
  );
}