import React, { useState } from 'react';
import NavBar from './NavBar';
import Sidebar from './Sidebar';
import './Paraphrase.css';
import React from 'react';  


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

  // LOGIC: Filter for matches > 0% and then find the one with the HIGHEST percentage
  const reports = result?.reports || [];
  const matches = reports.filter(r => r.overall_paraphrase_percentage > 0);
  const topMatch = matches.length > 0 
    ? matches.reduce((prev, current) => (prev.overall_paraphrase_percentage > current.overall_paraphrase_percentage) ? prev : current) 
    : null;

  const hasPlagiarism = topMatch !== null;
  return (
    <div className="par-wrap">
      <NavBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      <div className="par-body">
        <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <section className="par-main">
          <h1 className="par-title">Internet Paraphrase Detection</h1>

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

          {/* CASE 1: Display ONLY the Highest Detection Website...*/}
          {topMatch && (
            <div className="par-result" style={{ display: 'block', marginBottom: '20px', padding: '20px', borderLeft: '5px solid #ff4d4f' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                   <span style={{ backgroundColor: '#ffccc7', color: '#a8071a', padding: '4px 8px', borderRadius: '4px', fontSize: '0.8rem', marginRight: '10px', fontWeight: 'bold' }}>HIGHEST MATCH</span>
                   <a href={topMatch.url} target="_blank" rel="noreferrer" style={{ color: '#52c41a', fontWeight: 'bold', fontSize: '1.1rem' }}>
                     Source: {topMatch.url.substring(0, 60)}...
                   </a>
                </div>
                <span className="result-pill" style={{ backgroundColor: '#ff4d4f', padding: '10px 20px', fontSize: '1.2rem', fontWeight: 'bold' }}>
                  {topMatch.overall_paraphrase_percentage}% Match
                </span>
              </div>
              
              <div style={{ marginTop: '15px', fontSize: '1rem', color: '#ccc', borderTop: '1px solid #333', paddingTop: '10px' }}>
                <p><strong>Total Sentences Analyzed:</strong> {topMatch.total_sentences}</p>
                <p><strong>Plagiarized Sentences Found:</strong> {topMatch.plagiarized_count}</p>
              </div>

              <details style={{ marginTop: '15px' }} open>
                <summary style={{ cursor: 'pointer', color: '#1890ff', fontWeight: 'bold' }}>View Matching Sentences Breakdown</summary>
                <div style={{ padding: '15px', background: '#222', borderRadius: '8px', marginTop: '10px' }}>
                  {topMatch.detailed_matches.map((m, i) => (
                    <div key={i} style={{ marginBottom: '15px', borderBottom: '1px solid #444', paddingBottom: '15px' }}>
                      <p style={{ color: '#ff7875', marginBottom: '5px' }}><strong>🔴 Student:</strong> {m.student_sentence}</p>
                      <p style={{ color: '#95de64', marginBottom: '8px' }}><strong>🟢 Source:</strong> {m.source_sentence}</p>
                      
                      {/* Breakdown of Hybrid Scores */}
                      <div style={{ display: 'flex', gap: '20px', marginTop: '10px', fontSize: '0.9rem', backgroundColor: '#333', padding: '8px', borderRadius: '5px' }}>
                        <span style={{ color: '#bae637' }}>
                          🧠 <strong>Sinhala Model:</strong> {m.semantic_score}%
                        </span>
                        <span style={{ color: '#40a9ff' }}>
                          ⚙️ <strong>Lexical:</strong> {m.lexical_score}%
                        </span>
                        <span style={{ color: '#fff', fontWeight: 'bold', marginLeft: 'auto' }}>
                           🛡️ Final Score: {m.paraphrase_score}%
                        </span>
                      </div>
                      <div style={{ marginTop: '5px', fontSize: '0.8rem', color: '#888', textAlign: 'right' }}>
                         Mode: {m.mode || "Hybrid"}
                      </div>
                    </div>
                  ))}
                </div>
              </details>
            </div>
          )}

          {/* CASE 2: 0% Matches across all sources */}
          {reports.length > 0 && !hasPlagiarism && (
            <div className="par-result" style={{ display: 'block', padding: '30px', textAlign: 'center', backgroundColor: '#1a1a1a', border: '1px solid #333' }}>
              <div style={{ fontSize: '3rem', marginBottom: '15px' }}>✅</div>
              <h2 style={{ color: '#52c41a' }}>0% Match Detected</h2>
              <p style={{ color: '#d1cfe0', fontSize: '1.1rem' }}>
                The system successfully analyzed the top internet resources. 
                No paraphrased content exceeding the 50% threshold was found.
              </p>
            </div>
          )}
      </div>
    </div>
  );
}