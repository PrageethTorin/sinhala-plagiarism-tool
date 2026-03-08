import React, { useState } from 'react';
import NavBar from './NavBar';
import Sidebar from './Sidebar';
import './Pretrained.css';
import CircularGauge from './CircularGauge';

export default function Pretrained() {
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState('No file chosen');
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setFileName(selectedFile.name);
      setText(''); // clear text if file is chosen
    }
  };

  const handleCheck = async () => {
    if (!file && !text.trim()) {
      alert('Please upload a file or paste text');
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();

      if (file) {
        formData.append('file', file);
      } else {
        formData.append('text', text);
      }

      const response = await fetch(
        'http://127.0.0.1:8000/api/plagiarism/check',
        {
          method: 'POST',
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error('Failed to check plagiarism');
      }

      const data = await response.json();
      setResult(data);

    } catch (error) {
      alert('Error: ' + error.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pre-wrap">
      <NavBar />

      <div className="pre-body">
        <Sidebar />

        <section className="pre-main">
          <h1 className="pre-title">Plagiarism Check</h1>

          <div className="pre-card">
            <label className="lbl-block">
              Upload Document or Paste Text:
            </label>

            {/* SAME BOX – NOW TEXTAREA */}
            <textarea
              className="pretrained-box"
              placeholder="Paste text here..."
              value={text}
              onChange={(e) => {
                setText(e.target.value);
                setFile(null);
                setFileName('No file chosen');
              }}
            />

            <div className="pre-actions">
              <input
                type="file"
                className="file-input"
                onChange={handleFileChange}
                accept=".txt,.pdf,.doc,.docx"
              />

              <span className="file-name">{fileName}</span>

              <button
                className="pre-check"
                onClick={handleCheck}
                disabled={loading}
              >
                {loading ? 'Checking...' : 'Check'}
              </button>
            </div>
          </div>

          {result && (
            <div className="pre-result">
              <CircularGauge value={result.overall} />

              <div className="score-breakdown">
                <p>
                  Overall Plagiarism:{' '}
                  <b>{result.overall.toFixed(2)}%</b>
                </p>
                <p>
                  Semantic Similarity:{' '}
                  {result.semantic.toFixed(2)}%
                </p>
                <p>
                  Paraphrase Similarity:{' '}
                  {result.paraphrase.toFixed(2)}%
                </p>
                <p>
                  Stylometric Similarity:{' '}
                  {result.style.toFixed(2)}%
                </p>
                <p>
                  Status: <b>{result.decision}</b>
                </p>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
