import React from 'react';
import './Home.css';
import NavBar from './NavBar';

export default function Home({ sidebarOpen, setSidebarOpen }) {
  return (
    <div className="home-container">
      <NavBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

      <main className="hero-section">
        <div className="hero-content">
          <div className="hero-left">
            <h1 className="hero-title">
              <span className="highlight">Sinhala</span> Plagiarism Checker now
              <br />
              Enhanced with <span className="ai-highlight">AI Content Detector</span>
            </h1>

            <p className="hero-description">
              Our advanced plagiarism checker uses semantic similarity modeling to detect plagiarism in Sinhala text — even when content is paraphrased with different words but the same meaning.
            </p>

            <a href="#/writing-style-2" className="btn-check-now">Check Now</a>
          </div>

          <div className="hero-right">
            <img
              src="https://imgur.com/4eOuzSJ.png"
              alt="Plagiarism Detection Illustration"
              className="hero-image"
            />
          </div>
        </div>

        <div className="stats-section">
          <div className="stat-card">
            <div className="stat-number">2,494</div>
            <div className="stat-label">Training Pairs</div>
          </div>

          <div className="stat-card">
            <div className="stat-number">0.9997</div>
            <div className="stat-label">ROC-AUC Score</div>
          </div>

          <div className="stat-card">
            <div className="stat-number">2,807</div>
            <div className="stat-label">Corpus Paragraphs</div>
          </div>

          <div className="stat-card">
            <div className="stat-number">97.17%</div>
            <div className="stat-label">Paraphrase Detection</div>
          </div>
        </div>

        <div className="features-section">
          <h2 className="features-title">Our Features</h2>

          <div className="features-grid">
            <a href="#/writing-style-2" className="feature-card similarity-card">
              <div className="card-icon">🔍</div>
              <h3>Semantic Similarity (Comparison)</h3>
              <p>Compare two texts and detect plagiarism with hybrid ML approach</p>
            </a>

            <a href="#/writing-style-2" className="feature-card similarity-card">
              <div className="card-icon">🌐</div>
              <h3>Semantic Similarity (Web Search)</h3>
              <p>Search the web to find original sources using embedding-first detection</p>
            </a>
          </div>
        </div>
      </main>
    </div>
  );
}
