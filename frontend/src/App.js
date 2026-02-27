import React, { useEffect, useState } from 'react';
import './App.css';
import { AuthProvider } from './context/AuthContext';
import Home from './components/Home';
import Login from './components/Login';
import Signup from './components/Signup';
import SemanticSimilarity from './components/SemanticSimilarity';

function AppRoutes() {
  const [route, setRoute] = useState(window.location.hash || '#/');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const onHash = () => setRoute(window.location.hash || '#/');
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  // simple hash router
  const path = route.replace('#', '') || '/';

  if (path === '/login') return <Login />;
  if (path === '/signup') return <Signup />;

  if (path === '/writing-style-2') return <SemanticSimilarity sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />;

  return <Home sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />;
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

export default App;
