import React from 'react';
import './Home.css';
import NavBar from './NavBar';

export default function Home() {
  return (
    <div className="home-container">
      <NavBar />

      <main className="hero">
        <h1 className="hero-title">සිංහල භාෂාව</h1>

        <div className="cards">
          <div className="card cyan">Paraphrase Detection</div>
          <div className="card green">Writing Style</div>
          <div className="card blue">Writing Style</div>
          <div className="card pink">Writing Style</div>
        </div>
      </main>
    </div>
  );
}
