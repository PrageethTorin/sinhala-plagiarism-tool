import React, { useState } from 'react';
import NavBar from './NavBar';
import Sidebar from './Sidebar';
import './SemanticSimilarity.css';

export default function SemanticSimilarity({ sidebarOpen, setSidebarOpen }) {
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState('No file chosen');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setFileName(selectedFile.name);
    }
  };

  const handleCheck = async () => {
    if (!file) {
      alert('Please select a file');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/semantic/check', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
      });

      if (!response.ok) {
        throw new Error('Failed to check semantic similarity');
      }

      const data = await response.json();
      setResult(data.score || 0);
    } catch (error) {
      alert('Error: ' + error.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sem-wrap">
      <NavBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

      <div className="sem-body">
        <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <section className="sem-main">
          <h1 className="sem-title">Semantic Similarity</h1>

          <div className="sem-card">
            <label className="lbl-block">Upload Document:</label>

            <div className="semantic-box" />

            <div className="sem-actions">
              <input
                type="file"
                className="file-input"
                onChange={handleFileChange}
                accept=".pdf,.txt,.doc,.docx"
              />

              <span className="file-name">{fileName}</span>

              <button
                className="sem-check"
                onClick={handleCheck}
                disabled={loading}
              >
                {loading ? 'Checking...' : 'Check'}
              </button>
            </div>
          </div>

          {result !== null && (
            <div className="sem-result">
              <div className="result-label">Similarity Score</div>
              <div className="result-pill">{result}%</div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
