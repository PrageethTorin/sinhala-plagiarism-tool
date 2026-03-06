import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api/auth';

// Create context
const AuthContext = createContext(null);

// Google Client ID - Replace with your actual client ID
const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || '';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Load user on mount if token exists
  useEffect(() => {
    const loadUser = async () => {
      if (token) {
        try {
          const response = await axios.get(`${API_URL}/me`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setUser(response.data);
        } catch (error) {
          console.error('Failed to load user:', error);
          // Token is invalid, clear it
          localStorage.removeItem('token');
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };

    loadUser();
  }, [token]);

  // Login with email and password
  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API_URL}/login`, {
        email,
        password
      });

      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      setToken(access_token);

      // Fetch user info
      const userResponse = await axios.get(`${API_URL}/me`, {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      setUser(userResponse.data);

      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return {
        success: false,
        message: error.response?.data?.detail || 'Login failed'
      };
    }
  };

  // Register with email and password
  const register = async (email, password) => {
    try {
      const response = await axios.post(`${API_URL}/register`, {
        email,
        password
      });

      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      setToken(access_token);

      // Set user info
      setUser({ email, auth_provider: 'email' });

      return { success: true };
    } catch (error) {
      console.error('Register error:', error);
      return {
        success: false,
        message: error.response?.data?.detail || 'Registration failed'
      };
    }
  };

  // Login with Google
  const googleLogin = async (credential) => {
    try {
      const response = await axios.post(`${API_URL}/google`, {
        credential
      });

      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      setToken(access_token);

      // Fetch user info
      const userResponse = await axios.get(`${API_URL}/me`, {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      setUser(userResponse.data);

      return { success: true };
    } catch (error) {
      console.error('Google login error:', error);
      return {
        success: false,
        message: error.response?.data?.detail || 'Google login failed'
      };
    }
  };

  // Logout
  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    window.location.hash = '#/';
  };

  // Check if user is authenticated
  const isAuthenticated = !!user && !!token;

  const value = {
    user,
    token,
    loading,
    isAuthenticated,
    login,
    register,
    googleLogin,
    logout,
    GOOGLE_CLIENT_ID
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook to use auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
