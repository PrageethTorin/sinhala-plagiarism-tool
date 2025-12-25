import React, { useState } from 'react';
import NavBar from './NavBar';
import Sidebar from './Sidebar';
import './Paraphrase.css';

export default function Paraphrase({ sidebarOpen, setSidebarOpen }) {
  // State to store input texts
  const [sourceText, setSourceText] = useState("");
  const [suspiciousText, setSuspiciousText] = useState("");
  
  // State to store the result from Python
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleCheck = async () => {
    if (!sourceText || !suspiciousText) {
      alert("Please enter text in both boxes!");
      return;
    }

    setLoading(true);
    setResult(null); // Clear previous results

    try {
      // Send data to your Python Backend
      const response = await fetch('http://localhost:5000/api/check-paraphrase', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sourceText, suspiciousText })
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Error:", error);
      alert("Could not connect to the Python backend. Is server.py running?");
    }
    setLoading(false);
  };

  return (
    <div className="par-wrap">
      <NavBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      <div className="par-body">
        <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <section className="par-main">
          <h1 className="par-title">Paraphrase Detection</h1>

          <div className="par-card">
            {/* Input 1: Original Text */}
            <label className="lbl-block">Original Source Text:</label>
            <textarea 
              className="original-box" 
              placeholder="Paste original content here..."
              value={sourceText}
              onChange={(e) => setSourceText(e.target.value)}
              style={{ marginBottom: '20px' }}
            />

            {/* Input 2: Suspicious Text */}
            <label className="lbl-block">Suspicious / Student Text:</label>
            <textarea 
              className="original-box" 
              placeholder="Paste suspicious content here..."
              value={suspiciousText}
              onChange={(e) => setSuspiciousText(e.target.value)}
            />

            <div className="par-actions">
              <input type="file" className="file-input" disabled title="Coming Soon" />
              
              <button 
                className="par-check" 
                onClick={handleCheck} 
                disabled={loading}
                style={{ opacity: loading ? 0.7 : 1 }}
              >
                {loading ? "Analyzing..." : "Check Paraphrase"}
              </button>
            </div>
          </div>

          {/* Result Section */}
          {result && (
            <div className="par-result" style={{ display: 'block', padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                <span className="result-label">Paraphrase Score:</span>
                <span className="result-pill" 
                      style={{ backgroundColor: result.is_paraphrased ? '#ff4d4f' : '#52c41a', fontSize: '24px', padding: '10px 20px' }}>
                  {result.paraphrase_score}%
                </span>
              </div>
              
              <hr style={{ borderColor: '#444', margin: '15px 0' }}/>
              
              <div style={{ fontSize: '0.95rem', color: '#d1cfe0', lineHeight: '1.6' }}>
                <p><strong>Lexical Match (Words):</strong> {result.lexical_score}%</p>
                <p><strong>Semantic Match (Meaning):</strong> {result.semantic_score}%</p>
                <p style={{ marginTop: '15px', fontWeight: 'bold', fontSize: '1.1rem', color: result.is_paraphrased ? '#ff7875' : '#95de64' }}>
                  {result.is_paraphrased ? "🚨 PARAPHRASE DETECTED" : "✅ CONTENT IS UNIQUE"}
                </p>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}