import React from 'react';
import './Home.css';
import NavBar from './NavBar';

export default function Home({ sidebarOpen, setSidebarOpen }) {
  return (
    <div className="home-container">
      <NavBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

      <main className="hero">
        <h1 className="hero-title">සිංහල භාෂාව</h1>

        <div className="cards">
          <a className="card-link" href="#/paraphrase">
            <div className="card cyan">Paraphrase Detection</div>
          </a>

          <a className="card-link" href="#/writing-style-1">
            <div className="card green">Writing Style</div>
          </a>

          <a className="card-link" href="#/writing-style-2">
            <div className="card blue">Semantic Similarity</div>
          </a>

          <a className="card-link pink-link" href="#/writing-style-3">
            <div className="card pink">Pretrained Models</div>
          </a>
        </div>
      </main>
    </div>
  );
}
