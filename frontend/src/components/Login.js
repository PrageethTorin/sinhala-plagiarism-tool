import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import './Login.css';

export default function Login() {
  const { login, googleLogin, isAuthenticated, GOOGLE_CLIENT_ID } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      window.location.hash = '#/';
    }
  }, [isAuthenticated]);

  // Initialize Google Sign-In
  useEffect(() => {
    if (GOOGLE_CLIENT_ID && window.google) {
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleGoogleResponse
      });
      window.google.accounts.id.renderButton(
        document.getElementById('google-signin-btn'),
        { theme: 'outline', size: 'large', text: 'signin_with', width: 320 }
      );
    }
  }, [GOOGLE_CLIENT_ID, handleGoogleResponse]);

  const handleGoogleResponse = useCallback(async (response) => {
    setLoading(true);
    setError('');
    try {
      const result = await googleLogin(response.credential);
      if (!result.success) {
        setError(result.message);
      }
    } catch (err) {
      setError('Google sign-in failed');
    } finally {
      setLoading(false);
    }
  }, [googleLogin]);

  const validateEmail = (e) => /\S+@\S+\.\S+/.test(e);

  async function handleContinue(e) {
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

    setLoading(true);
    try {
      const result = await login(email, password);
      if (!result.success) {
        setError(result.message);
      }
    } catch (err) {
      setError(err?.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-container">
      <div className="login-modal" role="dialog" aria-labelledby="login-title">
        <h2 id="login-title" className="login-title">Sign in</h2>
        <a className="login-create" href="#/signup">Don't have an account? Sign up</a>

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

          <button type="submit" className="btn-continue" disabled={loading}>
            {loading ? 'Signing in...' : 'Continue'}
          </button>
        </form>

        <a className="login-help" href="#/">Can't sign in?</a>

        <div className="divider">
          <span>or</span>
        </div>

        <div className="oauth-list">
          {GOOGLE_CLIENT_ID ? (
            <div id="google-signin-btn"></div>
          ) : (
            <button type="button" className="oauth-btn" disabled>
              <span className="oauth-icon">G</span> Google Sign-In not configured
            </button>
          )}
        </div>

        <p className="recaptcha-note">
          This site is protected by reCAPTCHA and the Google Privacy Policy and Terms of Service apply.
        </p>
      </div>
    </div>
  );
}
