import React, { useState } from 'react';
import NavBar from './NavBar';
import Sidebar from './Sidebar';
import './Pretrained.css';

export default function Pretrained() {
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

  const response = await fetch('/api/pretrained/check', {
    method: 'POST',
    body: formData,
    credentials: 'same-origin',
  });

  if (!response.ok) {
    throw new Error('Failed to check pretrained');
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

return ( <div className="pre-wrap"> <NavBar />


  <div className="pre-body">
    <Sidebar />

    <section className="pre-main">
      <h1 className="pre-title">Pretrained Detection</h1>

      <div className="pre-card">
        <label className="lbl-block">Upload Document:</label>

        <div className="pretrained-box" />

        <div className="pre-actions">
          <input
            type="file"
            className="file-input"
            onChange={handleFileChange}
            accept=".pdf,.txt,.doc,.docx"
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

      {result !== null && (
        <div className="pre-result">
          <div className="result-label">Pretrained Score</div>
          <div className="result-pill">{result}%</div>
        </div>
      )}
    </section>
  </div>
</div>


);
}
