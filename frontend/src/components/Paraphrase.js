import React, { useState } from 'react';
import NavBar from './NavBar';
import Sidebar from './Sidebar';
import './Paraphrase.css';

export default function Paraphrase({ sidebarOpen, setSidebarOpen }) {
  const [studentText, setStudentText] = useState("");
  const [reports, setReports] = useState([]); 
  const [loading, setLoading] = useState(false);
  const [ocrLoading, setOcrLoading] = useState(false);

  // --- 📸 NEW: OCR Image-to-Text Logic (FastAPI Compatible) ---
  const handleOcrUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setOcrLoading(true);
    const formData = new FormData();
    formData.append('image', file); // 'image' key must match FastAPI UploadFile parameter

    try {
      const response = await fetch('http://localhost:5000/api/ocr-extract', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "OCR Extraction Failed");

      // Automatically fill the textarea with the cleaned Sinhala text
      setStudentText(data.extractedText);
      alert("✅ Sinhala text extracted successfully!");
    } catch (err) {
      console.error("OCR Error:", err);
      alert("❌ OCR Error: " + err.message);
    } finally {
      setOcrLoading(false);
      e.target.value = null; // Clear input to allow re-upload of same file
    }
  };

  // --- 📡 Existing: Internet Plagiarism Check Logic ---
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
      if (data.error || data.detail) throw new Error(data.error || data.detail);
      setReports(data);
    } catch (error) {
      console.error("Error:", error);
      alert("Error: " + error.message);
    }
    setLoading(false);
  };

  // --- 📊 UPDATED LOGIC: Get Top 3 Matches ---
  const topThreeMatches = reports
    .filter(r => r.overall_paraphrase_percentage > 0)
    .sort((a, b) => b.overall_paraphrase_percentage - a.overall_paraphrase_percentage)
    .slice(0, 3);

  const hasPlagiarism = topThreeMatches.length > 0;

  return (
    <div className="par-wrap">
      <NavBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      <div className="par-body">
        <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <section className="par-main">
          <h1 className="par-title">Internet Paraphrase Detection</h1>

          <div className="par-card">
            {/* OCR UPLOAD BUTTON */}
            <div style={{ marginBottom: '15px', textAlign: 'right' }}>
                <input 
                    type="file" 
                    accept="image/*" 
                    id="ocr-upload-input" 
                    style={{ display: 'none' }} 
                    onChange={handleOcrUpload} 
                    disabled={ocrLoading}
                />
                <label htmlFor="ocr-upload-input" className="par-check" style={{ 
                    backgroundColor: '#722ed1', 
                    padding: '8px 15px', 
                    cursor: ocrLoading ? 'not-allowed' : 'pointer',
                    borderRadius: '5px',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '8px',
                    opacity: ocrLoading ? 0.7 : 1
                }}>
                    📷 {ocrLoading ? "Extracting Sinhala Text..." : "Extract Text from Photo (OCR)"}
                </label>
            </div>

            <label className="lbl-block">Paste Student's Work (to scan the web):</label>
            <textarea 
              className="original-box" 
              placeholder="Paste content or upload an image to start the scan..."
              value={studentText}
              onChange={(e) => setStudentText(e.target.value)}
              style={{ height: '200px' }}
            />

            <div className="par-actions">
              <button 
                className="par-check" 
                onClick={handleInternetCheck} 
                disabled={loading || ocrLoading}
              >
                {loading ? "🔍 Scanning Wikipedia & Web..." : "Scan Internet for Paraphrase"}
              </button>
            </div>
          </div>

          {/* --- RESULTS SECTION: Top 3 Matches --- */}
          {hasPlagiarism && (
            <div style={{ marginBottom: '20px', color: '#ff4d4f', fontWeight: 'bold', fontSize: '1.2rem' }}>
               🚨 Top {topThreeMatches.length} Matching Sources Found:
            </div>
          )}

          {topThreeMatches.map((report, index) => (
            <div key={index} className="par-result" style={{ 
              display: 'block', 
              marginBottom: '30px', 
              padding: '20px', 
              borderLeft: `5px solid ${index === 0 ? '#ff4d4f' : '#faad14'}`, // Red for Rank #1
              backgroundColor: '#1a1a1a',
              borderRadius: '8px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                   <span style={{ 
                     backgroundColor: index === 0 ? '#ffccc7' : '#fffbe6', 
                     color: index === 0 ? '#a8071a' : '#874d00', 
                     padding: '4px 8px', 
                     borderRadius: '4px', 
                     fontSize: '0.8rem', 
                     marginRight: '10px', 
                     fontWeight: 'bold' 
                   }}>
                     RANK #{index + 1}
                   </span>
                   <a href={report.url} target="_blank" rel="noreferrer" style={{ color: '#52c41a', fontWeight: 'bold', fontSize: '1.1rem' }}>
                     Source: {report.url.substring(0, 65)}...
                   </a>
                </div>
                <span className="result-pill" style={{ 
                  backgroundColor: index === 0 ? '#ff4d4f' : '#faad14', 
                  padding: '10px 20px', 
                  fontSize: '1.2rem', 
                  fontWeight: 'bold',
                  borderRadius: '5px'
                }}>
                  {report.overall_paraphrase_percentage}% Match
                </span>
              </div>
              
              <div style={{ marginTop: '15px', fontSize: '1rem', color: '#ccc', borderTop: '1px solid #333', paddingTop: '10px' }}>
                <p><strong>Analyzed:</strong> {report.total_sentences} sentences</p>
                <p><strong>Plagiarized Found:</strong> {report.plagiarized_count} sentences</p>
              </div>

              <details style={{ marginTop: '15px' }}>
                <summary style={{ cursor: 'pointer', color: '#1890ff', fontWeight: 'bold' }}>View Matching Sentences Breakdown</summary>
                <div style={{ padding: '15px', background: '#222', borderRadius: '8px', marginTop: '10px' }}>
                  {report.detailed_matches.map((m, i) => (
                    <div key={i} style={{ marginBottom: '15px', borderBottom: '1px solid #444', paddingBottom: '15px' }}>
                      <p style={{ color: '#ff7875', marginBottom: '5px' }}><strong>🔴 Student:</strong> {m.student_sentence}</p>
                      <p style={{ color: '#95de64', marginBottom: '8px' }}><strong>🟢 Source:</strong> {m.source_sentence}</p>
                      
                      <div style={{ display: 'flex', gap: '20px', marginTop: '10px', fontSize: '0.9rem', backgroundColor: '#333', padding: '8px', borderRadius: '5px' }}>
                        <span style={{ color: '#bae637' }}>🧠 <strong>Semantic:</strong> {m.semantic_score}%</span>
                        <span style={{ color: '#40a9ff' }}>⚙️ <strong>Lexical:</strong> {m.lexical_score}%</span>
                        <span style={{ color: '#fff', fontWeight: 'bold', marginLeft: 'auto' }}>🛡️ Final: {m.paraphrase_score}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </details>
            </div>
          ))}

          {/* 0% MATCH CASE */}
          {reports.length > 0 && !hasPlagiarism && (
            <div className="par-result" style={{ display: 'block', padding: '30px', textAlign: 'center', backgroundColor: '#1a1a1a', border: '1px solid #333' }}>
              <div style={{ fontSize: '3rem', marginBottom: '15px' }}>✅</div>
              <h2 style={{ color: '#52c41a' }}>0% Match Detected</h2>
              <p style={{ color: '#d1cfe0', fontSize: '1.1rem' }}>
                No paraphrased content exceeding the 50% threshold was found on the analyzed sites.
              </p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}