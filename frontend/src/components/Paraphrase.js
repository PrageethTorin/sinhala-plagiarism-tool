import React, { useState } from 'react';
import NavBar from './NavBar';
import Sidebar from './Sidebar';
import './Paraphrase.css';

export default function Paraphrase({ sidebarOpen, setSidebarOpen }) {
  const [studentText, setStudentText] = useState("");
  const [reports, setReports] = useState([]); 
  const [loading, setLoading] = useState(false);

  const handleInternetCheck = async () => {
    if (!studentText) {
      alert("Please enter the student's text to scan the internet!");
      return;
    }

    setLoading(true);
    setReports([]); 

    try {
      const response = await fetch('http://localhost:5000/api/check-internet', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ studentText })
      });

      const data = await response.json();
      if (data.error) throw new Error(data.error);
      setReports(data);
    } catch (error) {
      console.error("Error:", error);
      alert("Error: " + error.message);
    }
    setLoading(false);
  };

  const hasPlagiarism = reports.some(r => r.overall_paraphrase_percentage > 0);

  return (
    <div className="par-wrap">
      <NavBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      <div className="par-body">
        <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <section className="par-main">
          <h1 className="par-title">Internet Paraphrase Detection</h1>

          <div className="par-card">
            <label className="lbl-block">Paste Student's Work (to scan the web):</label>
            <textarea 
              className="original-box" 
              placeholder="Paste Sinhala content here to search for paraphrased matches online..."
              value={studentText}
              onChange={(e) => setStudentText(e.target.value)}
              style={{ height: '200px' }}
            />

            <div className="par-actions">
              <button 
                className="par-check" 
                onClick={handleInternetCheck} 
                disabled={loading}
              >
                {loading ? "🔍 Scanning Web..." : "Scan Internet for Paraphrase"}
              </button>
            </div>
          </div>

          {/* CASE 1: Display only the websites where plagiarism was detected */}
          {reports.filter(r => r.overall_paraphrase_percentage > 0).map((report, index) => (
            <div key={index} className="par-result" style={{ display: 'block', marginBottom: '20px', padding: '20px', borderLeft: '5px solid #ff4d4f' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <a href={report.url} target="_blank" rel="noreferrer" style={{ color: '#52c41a', fontWeight: 'bold' }}>
                  Source: {report.url.substring(0, 50)}...
                </a>
                <span className="result-pill" style={{ backgroundColor: '#ff4d4f', padding: '8px 15px' }}>
                  {report.overall_paraphrase_percentage}% Match
                </span>
              </div>
              
              <div style={{ marginTop: '10px', fontSize: '0.9rem', color: '#ccc' }}>
                <p><strong>Sentences Analyzed:</strong> {report.total_sentences}</p>
                <p><strong>Paraphrased Sentences Found:</strong> {report.plagiarized_count}</p>
              </div>

              <details style={{ marginTop: '10px' }}>
                <summary style={{ cursor: 'pointer', color: '#1890ff' }}>View Matching Sentences</summary>
                <div style={{ padding: '10px', background: '#222', borderRadius: '5px', marginTop: '5px' }}>
                  {report.detailed_matches.map((m, i) => (
                    <div key={i} style={{ marginBottom: '15px', borderBottom: '1px solid #333', paddingBottom: '10px' }}>
                      <p style={{ color: '#ff7875' }}><strong>Student:</strong> {m.student_sentence}</p>
                      <p style={{ color: '#95de64' }}><strong>Source:</strong> {m.source_sentence}</p>
                      
                      {/* Breakdown of Hybrid Scores */}
                      <div style={{ display: 'flex', gap: '15px', marginTop: '8px', fontSize: '0.85rem' }}>
                        <span style={{ color: '#bae637' }}>
                          🧠 <strong>Semantic :</strong> {m.semantic_score}%
                        </span>
                        <span style={{ color: '#40a9ff' }}>
                          ⚙️ <strong>Lexical Engine :</strong> {m.lexical_score}%
                        </span>
                      </div>

                      <p style={{ fontSize: '0.9rem', marginTop: '5px', fontWeight: 'bold' }}>
                        Final Hybrid Score: {m.paraphrase_score}%
                      </p>
                    </div>
                  ))}
                </div>
              </details>
            </div>
          ))}

          {/* CASE 2: 0% Matches across all sources */}
          {reports.length > 0 && !hasPlagiarism && (
            <div className="par-result" style={{ display: 'block', padding: '30px', textAlign: 'center', backgroundColor: '#1a1a1a' }}>
              <div style={{ fontSize: '2rem', marginBottom: '10px' }}>✅</div>
              <h2 style={{ color: '#52c41a' }}>0% Match Detected</h2>
              <p style={{ color: '#d1cfe0' }}>
                The system successfully analyzed the top internet resources. 
                No paraphrased content exceeding the 70% threshold was found.
              </p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}