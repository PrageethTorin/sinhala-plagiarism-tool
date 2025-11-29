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
              Our advanced plagiarism checker verifies against internet sources, academic databases and AI-generated content to give you the most comprehensive plagiarism detection.
            </p>

            <a href="#/paraphrase" className="btn-check-now">Check Now</a>
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
            <div className="stat-number">82M+</div>
            <div className="stat-label">Scholarly Articles</div>
          </div>

          <div className="stat-card">
            <div className="stat-number">91B+</div>
            <div className="stat-label">Web Pages Indexed</div>
          </div>

          <div className="stat-card">
            <div className="stat-number">153M+</div>
            <div className="stat-label">Open Access Articles</div>
          </div>

          <div className="stat-card">
            <div className="stat-number">102M+</div>
            <div className="stat-label">Pages Updated Daily</div>
          </div>
        </div>

        <div className="features-section">
          <h2 className="features-title">Our Features</h2>
          
          <div className="features-grid">
            <a href="#/paraphrase" className="feature-card paraphrase-card">
              <div className="card-icon">📄</div>
              <h3>Paraphrase Detection</h3>
              <p>Detect paraphrased content and rewritten text</p>
            </a>

            <a href="#/writing-style-1" className="feature-card writing-card">
              <div className="card-icon">✍️</div>
              <h3>Writing Style</h3>
              <p>Analyze and identify writing patterns</p>
            </a>

            <a href="#/writing-style-2" className="feature-card similarity-card">
              <div className="card-icon">🔍</div>
              <h3>Semantic Similarity</h3>
              <p>Find semantically similar content</p>
            </a>

            <a href="#/pretrained" className="feature-card pretrained-card">
              <div className="card-icon">🤖</div>
              <h3>Pretrained Models</h3>
              <p>AI-powered plagiarism detection</p>
            </a>
          </div>
        </div>
      </main>
    </div>
  );
}
