import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import './Signup.css';

export default function Signup() {
  const { register, googleLogin, isAuthenticated, GOOGLE_CLIENT_ID } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
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
        { theme: 'outline', size: 'large', text: 'signup_with', width: 320 }
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
      setError('Google signup failed');
    } finally {
      setLoading(false);
    }
  }, [googleLogin]);

  const validateEmail = (e) => /\S+@\S+\.\S+/.test(e);

  async function handleSubmit(e) {
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
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      const result = await register(email, password);
      if (!result.success) {
        setError(result.message);
      }
    } catch (err) {
      setError(err?.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="signup-container">
      <div className="signup-modal" role="dialog" aria-labelledby="signup-title">
        <h2 id="signup-title" className="signup-title">Create Account</h2>
        <a className="signup-login-link" href="#/login">Already have an account? Sign in</a>

        <form className="signup-form" onSubmit={handleSubmit}>
          <label className="lbl-block" htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            className="signup-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@example.com"
            autoComplete="email"
          />

          <label className="lbl-block" htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            className="signup-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="At least 6 characters"
            autoComplete="new-password"
          />

          <label className="lbl-block" htmlFor="confirmPassword">Confirm Password</label>
          <input
            id="confirmPassword"
            type="password"
            className="signup-input"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirm your password"
            autoComplete="new-password"
          />

          {error && <div className="signup-error">{error}</div>}

          <button type="submit" className="btn-signup" disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <div className="divider">
          <span>or</span>
        </div>

        <div className="oauth-section">
          {GOOGLE_CLIENT_ID ? (
            <div id="google-signin-btn"></div>
          ) : (
            <button type="button" className="oauth-btn" disabled>
              <span className="oauth-icon">G</span> Google Sign-In not configured
            </button>
          )}
        </div>

        <p className="terms-note">
          By creating an account, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </div>
  );
}
