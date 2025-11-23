import React, { useEffect, useState } from 'react';
import './App.css';
import Home from './components/Home';
import Login from './components/Login';
import Paraphrase from './components/Paraphrase';

function Feature({ title }) {
  return (
    <div style={{ padding: 40 }}>
      <h2 style={{ color: '#fff' }}>{title}</h2>
      <p style={{ color: '#d1cfe0' }}>Placeholder page for {title}.</p>
    </div>
  );
}


function App() {
  const [route, setRoute] = useState(window.location.hash || '#/');

  useEffect(() => {
    const onHash = () => setRoute(window.location.hash || '#/');
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  // simple hash router
  const path = route.replace('#', '') || '/';

  if (path === '/login') return <Login />;
  if (path === '/paraphrase') return <Paraphrase />;
  if (path === '/writing-style-1') return <Feature title="Writing Style" />;
  if (path === '/writing-style-2') return <Feature title="Writing Style" />;
  if (path === '/writing-style-3') return <Feature title="Writing Style" />;

  return <Home />;
}

export default App;
