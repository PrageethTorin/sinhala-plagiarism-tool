<<<<<<< HEAD
import React, { useState } from 'react';
import './Login.css';

export default function Login({ onSubmit }) {
=======
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import './Login.css';

export default function Login() {
  const { login, googleLogin, isAuthenticated, GOOGLE_CLIENT_ID } = useAuth();
>>>>>>> 5673241b182fadae9c0cb3ec5af5138f234b4b13
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

<<<<<<< HEAD
=======
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
  }, [GOOGLE_CLIENT_ID]);

  const handleGoogleResponse = async (response) => {
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
  };

>>>>>>> 5673241b182fadae9c0cb3ec5af5138f234b4b13
  const validateEmail = (e) => /\S+@\S+\.\S+/.test(e);

  async function handleContinue(e) {
    e.preventDefault();
    setError('');
<<<<<<< HEAD
    
=======

>>>>>>> 5673241b182fadae9c0cb3ec5af5138f234b4b13
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

<<<<<<< HEAD
    if (!onSubmit) {
      window.location.hash = '#/';
      return;
    }

    setLoading(true);
    try {
      const result = await onSubmit(email, password);
      if (!result || !result.success) {
        setError(result?.message || 'Invalid credentials');
=======
    setLoading(true);
    try {
      const result = await login(email, password);
      if (!result.success) {
        setError(result.message);
>>>>>>> 5673241b182fadae9c0cb3ec5af5138f234b4b13
      }
    } catch (err) {
      setError(err?.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  }

<<<<<<< HEAD
  function handleOAuth(provider) {
    console.log('OAuth:', provider);
  }

=======
>>>>>>> 5673241b182fadae9c0cb3ec5af5138f234b4b13
  return (
    <div className="login-container">
      <div className="login-modal" role="dialog" aria-labelledby="login-title">
        <h2 id="login-title" className="login-title">Sign in</h2>
<<<<<<< HEAD
        <a className="login-create" href="#/">I don't have an account</a>
=======
        <a className="login-create" href="#/signup">Don't have an account? Sign up</a>
>>>>>>> 5673241b182fadae9c0cb3ec5af5138f234b4b13

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

<<<<<<< HEAD
        <div className="oauth-list">
          <button type="button" className="oauth-btn" onClick={() => handleOAuth('google')}>
            <span className="oauth-icon">G</span> Sign in with Google
          </button>
          <button type="button" className="oauth-btn" onClick={() => handleOAuth('facebook')}>
            <span className="oauth-icon">f</span> Sign in with Facebook
          </button>
          
=======
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
>>>>>>> 5673241b182fadae9c0cb3ec5af5138f234b4b13
        </div>

        <p className="recaptcha-note">
          This site is protected by reCAPTCHA and the Google Privacy Policy and Terms of Service apply.
        </p>
      </div>
    </div>
  );
<<<<<<< HEAD
}
=======
}
>>>>>>> 5673241b182fadae9c0cb3ec5af5138f234b4b13
