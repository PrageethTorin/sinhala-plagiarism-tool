import React, { useState } from 'react';
import NavBar from './NavBar';
import Sidebar from './Sidebar';
import './Pretrained.css';
<<<<<<< HEAD
=======
import CircularGauge from './CircularGauge';

>>>>>>> 5673241b182fadae9c0cb3ec5af5138f234b4b13

export default function Pretrained({ sidebarOpen, setSidebarOpen }) {
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

<<<<<<< HEAD
  const response = await fetch('/api/pretrained/check', {
=======
 const response = await fetch('http://127.0.0.1:5000/api/plagiarism/check', {

>>>>>>> 5673241b182fadae9c0cb3ec5af5138f234b4b13
    method: 'POST',
    body: formData,
    credentials: 'same-origin',
  });

  if (!response.ok) {
    throw new Error('Failed to check pretrained');
  }

  const data = await response.json();
<<<<<<< HEAD
  setResult(data.score || 0);
=======
  setResult(data);
;
>>>>>>> 5673241b182fadae9c0cb3ec5af5138f234b4b13
} catch (error) {
  alert('Error: ' + error.message);
  setResult(null);
} finally {
  setLoading(false);
}


};

return ( <div className="pre-wrap"> <NavBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />


  <div className="pre-body">
    <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

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

<<<<<<< HEAD
      {result !== null && (
        <div className="pre-result">
          <div className="result-label">Pretrained Score</div>
          <div className="result-pill">{result}%</div>
        </div>
      )}
=======
  
{result && (
  <div className="pre-result">
    <CircularGauge value={result.overall} />

    <div className="score-breakdown">
      <p>Overall Plagiarism: <b>{result.overall.toFixed(2)}%</b></p>
      <p>Semantic Similarity: {result.semantic.toFixed(2)}%</p>
      <p>Paraphrase Similarity: {result.paraphrase.toFixed(2)}%</p>
      <p>Stylometric Similarity: {result.style.toFixed(2)}%</p>
      <p>Status: <b>{result.decision}</b></p>
    </div>
  </div>
)}


>>>>>>> 5673241b182fadae9c0cb3ec5af5138f234b4b13
    </section>
  </div>
</div>


);
}
