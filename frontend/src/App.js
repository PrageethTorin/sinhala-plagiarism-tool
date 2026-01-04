import React, { useEffect, useState } from 'react';
import './App.css';
import { AuthProvider } from './context/AuthContext';
import Home from './components/Home';
import Login from './components/Login';
import Signup from './components/Signup';
import Paraphrase from './components/Paraphrase';
import Pretrained from './components/Pretrained';
import WritingStyle from './components/WritingStyle';

function Feature({ title }) {
  return (
    <div style={{ padding: 40 }}>
      <h2 style={{ color: '#fff' }}>{title}</h2>
      <p style={{ color: '#d1cfe0' }}>Placeholder page for {title}.</p>
    </div>
  );
}

function AppRoutes() {
  const [route, setRoute] = useState(window.location.hash || '#/');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const onHash = () => setRoute(window.location.hash || '#/');
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const path = route.replace('#', '') || '/';

  if (path === '/login') return <Login />;
  if (path === '/signup') return <Signup />;

  // merged correctly
  if (path === '/paraphrase')
    return <Paraphrase sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />;

  // keep your original pretrained route
  if (path === '/pretrained') return <Pretrained sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />;

  if (path === '/writing-style') return <WritingStyle sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />;
  if (path === '/writing-style-2') return <Feature title="Writing Style" />;
  if (path === '/writing-style-3') return <Feature title="Writing Style" />;
  

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
