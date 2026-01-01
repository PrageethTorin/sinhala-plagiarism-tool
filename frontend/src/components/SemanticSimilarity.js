import React, { useState } from 'react';
import NavBar from './NavBar';
import Sidebar from './Sidebar';
import './SemanticSimilarity.css';
import axios from 'axios';

export default function SemanticSimilarity({ sidebarOpen, setSidebarOpen }) {
  // Tab state
  const [activeTab, setActiveTab] = useState('paragraph');

  // Paragraph comparison state
  const [originalText, setOriginalText] = useState('');
  const [suspiciousText, setSuspiciousText] = useState('');
  const [threshold, setThreshold] = useState(0.7);
  const [algorithm, setAlgorithm] = useState('hybrid');
  const [checkParaphrase, setCheckParaphrase] = useState(false);
  const [mainLoading, setMainLoading] = useState(false);
  const [result, setResult] = useState(null);

  // Web corpus state
  const [webText, setWebText] = useState('');
  const [webLoading, setWebLoading] = useState(false);
  const [webResult, setWebResult] = useState(null);

  // Google search state
  const [googleText, setGoogleText] = useState('');
  const [googleLoading, setGoogleLoading] = useState(false);
  const [googleResult, setGoogleResult] = useState(null);

  // Shared state
  const [error, setError] = useState('');

  const API_BASE_URL = 'http://localhost:8000';

  // ==================== PARAGRAPH COMPARISON ====================
  const handleCheck = async () => {
    if (!originalText.trim() || !suspiciousText.trim()) {
      setError('Please enter both texts');
      return;
    }

    setMainLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/check-plagiarism`, {
        text_pair: {
          original: originalText,
          suspicious: suspiciousText
        },
        threshold: threshold,
        algorithm: algorithm,
        check_paraphrase: checkParaphrase
      });

      setResult(response.data);
    } catch (error) {
      console.error('API Error:', error);
      if (error.response) {
        setError(error.response.data?.error || error.response.data?.detail || 'API Error');
      } else if (error.request) {
        setError('Cannot connect to server. Make sure backend is running on port 8000.');
      } else {
        setError('Failed to check similarity');
      }
    } finally {
      setMainLoading(false);
    }
  };

  // ==================== WEB CORPUS CHECK ====================
  const handleWebCheck = async () => {
    if (!webText.trim()) {
      setError("Please enter text for web corpus check");
      return;
    }

    setWebLoading(true);
    setError("");
    setWebResult(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/web-corpus-check`, {
        text_pair: {
          original: webText,
          suspicious: ""
        }
      });

      setWebResult(response.data);
    } catch (err) {
      console.error(err);
      setError("Web corpus similarity check failed");
    } finally {
      setWebLoading(false);
    }
  };

  // ==================== GOOGLE WEB SEARCH ====================
  const handleGoogleSearch = async () => {
    if (!googleText.trim()) {
      setError("Please enter text for Google search");
      return;
    }

    setGoogleLoading(true);
    setError("");
    setGoogleResult(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/web-search-check`, {
        text_pair: {
          original: googleText,
          suspicious: ""
        }
      });

      setGoogleResult(response.data);
    } catch (err) {
      console.error(err);
      setError("Google web search failed. Please check API configuration.");
    } finally {
      setGoogleLoading(false);
    }
  };

  // ==================== UTILITY FUNCTIONS ====================
  const handleExample = () => {
    const exampleOriginal = "ශ්‍රී ලංකාවේ අධ්‍යාපන පද්ධතිය නවීකරණය කිරීමේ අවශ්‍යතාවය දැන් වැදගත් වේ. ගුණාත්මක අධ්‍යාපනයක් සහතික කිරීම සඳහා යාවත්කාලීන උපකරණ හා උපදේශන ක්‍රම අවශ්‍ය වේ.";
    const exampleSuspicious = "ශ්‍රී ලංකාවේ අධ්‍යාපන ක්ෂේත්‍රය නවීන ලෙස සංවර්ධනය කිරීමේ අවශ්‍යතාවය පවතී. උසස් තත්ත්වයේ අධ්‍යාපනයක් සහතික කර ගැනීම සඳහා නවීන උපකරණ හා උපදේශන ක්‍රම අත්‍යවශ්‍ය වේ.";

    setOriginalText(exampleOriginal);
    setSuspiciousText(exampleSuspicious);
    setResult(null);
    setError("");
  };

  const handleClear = () => {
    setOriginalText("");
    setSuspiciousText("");
    setWebText("");
    setGoogleText("");
    setResult(null);
    setWebResult(null);
    setGoogleResult(null);
    setError("");
    setThreshold(0.7);
    setAlgorithm('hybrid');
    setCheckParaphrase(false);
  };

  const handleFileUpload = async (e, textType) => {
    const file = e.target.files[0];
    if (!file) return;

    const fileType = file.name.split('.').pop().toLowerCase();
    const allowedTypes = ['txt', 'pdf', 'doc', 'docx'];

    if (!allowedTypes.includes(fileType)) {
      setError(`Unsupported file type: .${fileType}. Please upload .txt, .pdf, .doc, or .docx files.`);
      return;
    }

    if (fileType === 'txt') {
      const reader = new FileReader();
      reader.onload = (event) => {
        const content = event.target.result;
        if (textType === 'original') {
          setOriginalText(content);
        } else {
          setSuspiciousText(content);
        }
      };
      reader.readAsText(file);
    } else {
      setError(`For ${fileType.toUpperCase()} files, please use the File Upload feature in the API or convert to text first.`);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 0.8) return '#ff4757';
    if (score >= 0.5) return '#ffa502';
    return '#1fb6a0';
  };

  // ==================== RENDER ====================
  return (
    <div className="sem-wrap">
      <NavBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

      <div className="sem-body">
        <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <section className="sem-main">
          <h1 className="sem-title">Sinhala Plagiarism Detection</h1>

          {error && (
            <div className="sem-error">
              {error}
            </div>
          )}

          {/* ==================== TAB NAVIGATION ==================== */}
          <div className="tab-navigation">
            <button
              className={`tab-btn ${activeTab === 'paragraph' ? 'active' : ''}`}
              onClick={() => setActiveTab('paragraph')}
            >
              <span className="tab-icon">📝</span>
              <span className="tab-text">Paragraph Comparison</span>
            </button>
            <button
              className={`tab-btn ${activeTab === 'corpus' ? 'active' : ''}`}
              onClick={() => setActiveTab('corpus')}
            >
              <span className="tab-icon">📚</span>
              <span className="tab-text">Web Corpus Search</span>
            </button>
            <button
              className={`tab-btn ${activeTab === 'google' ? 'active' : ''}`}
              onClick={() => setActiveTab('google')}
            >
              <span className="tab-icon">🌐</span>
              <span className="tab-text">Google Web Search</span>
            </button>
          </div>

          {/* ==================== TAB CONTENT ==================== */}
          <div className="tab-content">

            {/* ========== PARAGRAPH COMPARISON TAB ========== */}
            {activeTab === 'paragraph' && (
              <div className="tab-panel">
                <p className="tab-description">
                  Compare two Sinhala texts directly to detect plagiarism or paraphrasing.
                </p>

                {/* Dual Text Input Section */}
                <div className="dual-input-section">
                  {/* Original Text Card */}
                  <div className="text-card">
                    <div className="card-header">
                      <span className="card-title">Original Text</span>
                      <div className="file-upload-wrapper">
                        <input
                          type="file"
                          className="file-input-hidden"
                          onChange={(e) => handleFileUpload(e, 'original')}
                          accept=".txt,.pdf,.doc,.docx"
                          id="original-file"
                        />
                        <label htmlFor="original-file" className="upload-btn">
                          Upload
                        </label>
                      </div>
                    </div>
                    <textarea
                      className="text-input"
                      value={originalText}
                      onChange={(e) => setOriginalText(e.target.value)}
                      placeholder="Enter original Sinhala text here..."
                      rows={8}
                    />
                    <div className="char-counter">
                      {originalText.length} characters
                    </div>
                  </div>

                  {/* VS Separator */}
                  <div className="vs-separator">
                    <div className="vs-circle">VS</div>
                  </div>

                  {/* Suspicious Text Card */}
                  <div className="text-card">
                    <div className="card-header">
                      <span className="card-title">Suspicious Text</span>
                      <div className="file-upload-wrapper">
                        <input
                          type="file"
                          className="file-input-hidden"
                          onChange={(e) => handleFileUpload(e, 'suspicious')}
                          accept=".txt,.pdf,.doc,.docx"
                          id="suspicious-file"
                        />
                        <label htmlFor="suspicious-file" className="upload-btn">
                          Upload
                        </label>
                      </div>
                    </div>
                    <textarea
                      className="text-input"
                      value={suspiciousText}
                      onChange={(e) => setSuspiciousText(e.target.value)}
                      placeholder="Enter suspicious Sinhala text here..."
                      rows={8}
                    />
                    <div className="char-counter">
                      {suspiciousText.length} characters
                    </div>
                  </div>
                </div>

                {/* Controls Card */}
                <div className="controls-card">
                  <div className="controls-grid">
                    <div className="control-group">
                      <label className="control-label">Algorithm:</label>
                      <select
                        className="control-select"
                        value={algorithm}
                        onChange={(e) => setAlgorithm(e.target.value)}
                      >
                        <option value="hybrid">Hybrid (Recommended)</option>
                        <option value="semantic">Semantic Only</option>
                        <option value="lexical">Lexical Only</option>
                      </select>
                    </div>

                    <div className="control-group">
                      <label className="control-label">
                        Threshold: <span className="threshold-value">{threshold.toFixed(2)}</span>
                      </label>
                      <input
                        type="range"
                        className="threshold-slider"
                        min="0.1"
                        max="0.95"
                        step="0.05"
                        value={threshold}
                        onChange={(e) => setThreshold(parseFloat(e.target.value))}
                      />
                      <div className="slider-labels">
                        <span>0.1</span>
                        <span>0.5</span>
                        <span>0.95</span>
                      </div>
                    </div>

                    <div className="control-group">
                      <label className="control-label">Options:</label>
                      <div className="checkbox-group">
                        <label className="checkbox-label">
                          <input
                            type="checkbox"
                            checked={checkParaphrase}
                            onChange={(e) => setCheckParaphrase(e.target.checked)}
                            className="checkbox-input"
                          />
                          <span className="checkbox-custom"></span>
                          Detect Paraphrasing
                        </label>
                      </div>
                    </div>
                  </div>

                  <div className="action-buttons">
                    <button
                      className="primary-action-btn"
                      onClick={handleCheck}
                      disabled={mainLoading}
                    >
                      {mainLoading ? (
                        <>
                          <span className="loading-spinner"></span>
                          Analyzing...
                        </>
                      ) : (
                        'Check Plagiarism'
                      )}
                    </button>
                    <button className="secondary-action-btn" onClick={handleExample}>
                      Load Example
                    </button>
                    <button className="secondary-action-btn" onClick={handleClear}>
                      Clear All
                    </button>
                  </div>
                </div>

                {/* Paragraph Results */}
                {result && (
                  <div className="results-container">
                    <div className="overall-score-section">
                      <div className="score-circle-container">
                        <div
                          className="score-circle"
                          style={{
                            background: `conic-gradient(
                              ${getScoreColor(result.similarity_score)} ${result.similarity_score * 360}deg,
                              #3a3546 ${result.similarity_score * 360}deg
                            )`
                          }}
                        >
                          <div className="score-inner">
                            <span className="score-percent">
                              {(result.similarity_score * 100).toFixed(1)}%
                            </span>
                            <span className="score-label">Similarity Score</span>
                          </div>
                        </div>
                      </div>

                    </div>

                    {/* Progress Bar */}
                    <div className="progress-section">
                      <div
                        className="progress-fill"
                        style={{ width: `${result.similarity_score * 100}%` }}
                      ></div>
                    </div>

                    {/* Component Scores */}
                    {result.components && (
                      <div className="components-section">
                        <h3 className="section-title">Component Analysis</h3>
                        <div className="components-grid">
                          {Object.entries(result.components).map(([key, value]) => (
                            <div key={key} className="component-item">
                              <div className="component-name">{key}</div>
                              <div className="component-value">{(value * 100).toFixed(1)}%</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Matched Sections */}
                    {result.matches && result.matches.length > 0 && (
                      <div className="matches-section">
                        <h3 className="section-title">Matched Segments</h3>
                        <div className="matches-list">
                          {result.matches.map((match, index) => (
                            <div key={index} className="match-item">
                              <div className="match-pair">
                                <div className="match-original">
                                  <span className="match-label">Original:</span>
                                  <span className="match-text">{match.original_segment}</span>
                                </div>
                                <div className="match-suspicious">
                                  <span className="match-label">Suspicious:</span>
                                  <span className="match-text">{match.suspicious_segment}</span>
                                </div>
                              </div>
                              <div
                                className="match-score"
                                style={{
                                  color: getScoreColor(match.similarity_score),
                                  borderColor: getScoreColor(match.similarity_score)
                                }}
                              >
                                {(match.similarity_score * 100).toFixed(1)}%
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Metadata */}
                    <div className="metadata-section">
                      {result.metadata && (
                        <div className="metadata-item">
                          <span className="metadata-label">Algorithm:</span>
                          <span className="metadata-value">{result.metadata.algorithm_used}</span>
                        </div>
                      )}
                      <div className="metadata-item">
                        <span className="metadata-label">Processing Time:</span>
                        <span className="metadata-value">
                          {result.processing_time?.toFixed(3) || '0.000'}s
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ========== WEB CORPUS TAB ========== */}
            {activeTab === 'corpus' && (
              <div className="tab-panel">
                <p className="tab-description">
                  Check your text against our indexed Sinhala Wikipedia corpus (2,807 documents).
                  Uses FAISS vector search + hybrid similarity scoring.
                </p>

                <div className="text-card single-input">
                  <div className="card-header">
                    <span className="card-title">Text to Check</span>
                  </div>
                  <textarea
                    className="text-input"
                    rows={8}
                    value={webText}
                    onChange={(e) => setWebText(e.target.value)}
                    placeholder="Enter Sinhala paragraph to check against web corpus..."
                  />
                  <div className="char-counter">
                    {webText.length} characters
                  </div>
                </div>

                <div className="action-buttons centered">
                  <button
                    className="primary-action-btn"
                    onClick={handleWebCheck}
                    disabled={webLoading}
                  >
                    {webLoading ? (
                      <>
                        <span className="loading-spinner"></span>
                        Searching Corpus...
                      </>
                    ) : (
                      'Search Web Corpus'
                    )}
                  </button>
                  <button
                    className="secondary-action-btn"
                    onClick={() => { setWebText(''); setWebResult(null); }}
                  >
                    Clear
                  </button>
                </div>

                {/* Web Corpus Results */}
                {webResult && (
                  <div className="results-container">
                    <h3 className="section-title">Corpus Search Results</h3>

                    {/* Summary */}
                    {webResult.summary && (
                      <div className="overall-score-section">
                        <div className="score-circle-container">
                          <div
                            className="score-circle"
                            style={{
                              background: `conic-gradient(
                                ${getScoreColor(webResult.summary.average_similarity)} ${webResult.summary.average_similarity * 360}deg,
                                #3a3546 ${webResult.summary.average_similarity * 360}deg
                              )`
                            }}
                          >
                            <div className="score-inner">
                              <span className="score-percent">
                                {(webResult.summary.average_similarity * 100).toFixed(1)}%
                              </span>
                              <span className="score-label">Avg. Similarity</span>
                            </div>
                          </div>
                        </div>

                        <div className="verdict-section">
                          <div className="stats-grid">
                            <div className="stat-item">
                              <span className="stat-value">{webResult.summary.sources_checked}</span>
                              <span className="stat-label">Sources Checked</span>
                            </div>
                            <div className="stat-item">
                              <span className="stat-value">{webResult.summary.matches_found}</span>
                              <span className="stat-label">Matches Found</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Matches */}
                    {webResult.matches && webResult.matches.length > 0 && (
                      <div className="matches-section">
                        <h4 className="section-subtitle">Top Matches</h4>
                        <div className="matches-list">
                          {webResult.matches.map((match, index) => (
                            <div key={index} className="match-item corpus-match">
                              <div className="match-content">
                                <div className="match-text-preview">
                                  {match.matched_text && match.matched_text.length > 300
                                    ? match.matched_text.substring(0, 300) + '...'
                                    : match.matched_text || 'N/A'}
                                </div>
                                <div className="match-meta">
                                  <span className={`case-badge ${match.case_type}`}>
                                    {match.case_type || 'unknown'}
                                  </span>
                                  {match.custom_score && (
                                    <span className="score-detail">
                                      Custom: {(match.custom_score * 100).toFixed(1)}%
                                    </span>
                                  )}
                                  {match.embedding_score && (
                                    <span className="score-detail">
                                      Embedding: {(match.embedding_score * 100).toFixed(1)}%
                                    </span>
                                  )}
                                </div>
                              </div>
                              <div
                                className="match-score"
                                style={{
                                  color: getScoreColor(match.final_score || 0),
                                  borderColor: getScoreColor(match.final_score || 0)
                                }}
                              >
                                {((match.final_score || 0) * 100).toFixed(1)}%
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* No matches */}
                    {webResult.summary && webResult.summary.matches_found === 0 && (
                      <div className="no-matches-message">
                        No significant matches found in the corpus.
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ========== GOOGLE SEARCH TAB ========== */}
            {activeTab === 'google' && (
              <div className="tab-panel">
                <p className="tab-description">
                  Search the live web using Google Custom Search API.
                  Finds similar content from across the internet.
                </p>

                <div className="text-card single-input">
                  <div className="card-header">
                    <span className="card-title">Text to Search</span>
                  </div>
                  <textarea
                    className="text-input"
                    rows={8}
                    value={googleText}
                    onChange={(e) => setGoogleText(e.target.value)}
                    placeholder="Enter Sinhala paragraph to search on the web..."
                  />
                  <div className="char-counter">
                    {googleText.length} characters
                  </div>
                </div>

                <div className="action-buttons centered">
                  <button
                    className="primary-action-btn google-btn"
                    onClick={handleGoogleSearch}
                    disabled={googleLoading}
                  >
                    {googleLoading ? (
                      <>
                        <span className="loading-spinner"></span>
                        Searching Web...
                      </>
                    ) : (
                      'Search Google'
                    )}
                  </button>
                  <button
                    className="secondary-action-btn"
                    onClick={() => { setGoogleText(''); setGoogleResult(null); }}
                  >
                    Clear
                  </button>
                </div>

                {/* Google Search Results */}
                {googleResult && (
                  <div className="results-container">
                    <h3 className="section-title">Google Search Results</h3>

                    {/* Verdict and Summary */}
                    <div className="overall-score-section">
                      <div className="score-circle-container">
                        <div
                          className="score-circle"
                          style={{
                            background: `conic-gradient(
                              ${getScoreColor(googleResult.max_similarity || 0)} ${(googleResult.max_similarity || 0) * 360}deg,
                              #3a3546 ${(googleResult.max_similarity || 0) * 360}deg
                            )`
                          }}
                        >
                          <div className="score-inner">
                            <span className="score-percent">
                              {((googleResult.max_similarity || 0) * 100).toFixed(1)}%
                            </span>
                            <span className="score-label">Max Similarity</span>
                          </div>
                        </div>
                      </div>

                      <div className="verdict-section">
                        {googleResult.verdict && (
                          <div className={`verdict-badge ${googleResult.verdict === 'Original' ? 'original' : 'plagiarized'}`}>
                            {googleResult.verdict}
                          </div>
                        )}
                        <div className="stats-grid">
                          <div className="stat-item">
                            <span className="stat-value">{googleResult.statistics?.sources_checked || 0}</span>
                            <span className="stat-label">Sources</span>
                          </div>
                          <div className="stat-item">
                            <span className="stat-value">{googleResult.statistics?.paragraphs_checked || 0}</span>
                            <span className="stat-label">Paragraphs</span>
                          </div>
                          <div className="stat-item">
                            <span className="stat-value">{googleResult.statistics?.sentences_checked || 0}</span>
                            <span className="stat-label">Sentences</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Sentence-Level Matches (ENHANCED) */}
                    {googleResult.sentence_matches && googleResult.sentence_matches.length > 0 && (
                      <div className="matches-section sentence-matches-section">
                        <h4 className="section-subtitle">
                          Matched Sentences
                          <span className="match-count-badge">
                            {googleResult.sentence_matches.length}
                          </span>
                        </h4>
                        <div className="sentence-matches-list">
                          {googleResult.sentence_matches.map((match, index) => (
                            <div key={index} className="sentence-match-item">
                              <div className="sentence-pair">
                                <div className="sentence-input">
                                  <span className="sentence-label">Your Text:</span>
                                  <span className="sentence-text">{match.input_sentence}</span>
                                </div>
                                <div className="sentence-arrow">→</div>
                                <div className="sentence-source">
                                  <span className="sentence-label">Source:</span>
                                  <span className="sentence-text">{match.source_sentence}</span>
                                </div>
                              </div>
                              <div className="sentence-meta">
                                <span
                                  className="sentence-score"
                                  style={{ color: getScoreColor(match.similarity_score) }}
                                >
                                  {(match.similarity_score * 100).toFixed(1)}%
                                </span>
                                <span className={`case-badge ${match.case_type}`}>
                                  {match.case_type}
                                </span>
                                {match.source_title && (
                                  <span className="source-title">{match.source_title}</span>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Web Results */}
                    {googleResult.matches && googleResult.matches.length > 0 && (
                      <div className="matches-section">
                        <h4 className="section-subtitle">Source Pages</h4>
                        <div className="matches-list">
                          {googleResult.matches.map((match, index) => (
                            <div key={index} className="match-item web-match">
                              <div className="match-content">
                                <div className="match-title">
                                  {match.source_title || match.title || 'Untitled'}
                                </div>
                                <div className="match-text-preview">
                                  {match.matched_text || match.snippet || 'No preview available'}
                                </div>
                                {(match.source_url || match.url) && (
                                  <a
                                    href={match.source_url || match.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="match-url"
                                  >
                                    {match.source_url || match.url}
                                  </a>
                                )}
                                <div className="match-meta">
                                  <span className={`case-badge ${match.case_type}`}>
                                    {match.case_type}
                                  </span>
                                  {match.custom_score && (
                                    <span className="score-detail">
                                      Custom: {(match.custom_score * 100).toFixed(1)}%
                                    </span>
                                  )}
                                  {match.embedding_score && (
                                    <span className="score-detail">
                                      Embedding: {(match.embedding_score * 100).toFixed(1)}%
                                    </span>
                                  )}
                                </div>
                              </div>
                              <div
                                className="match-score"
                                style={{
                                  color: getScoreColor(match.similarity_score || 0),
                                  borderColor: getScoreColor(match.similarity_score || 0)
                                }}
                              >
                                {((match.similarity_score || 0) * 100).toFixed(1)}%
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Processing Info */}
                    {googleResult.statistics && (
                      <div className="metadata-section">
                        <div className="metadata-item">
                          <span className="metadata-label">Processing Time:</span>
                          <span className="metadata-value">
                            {googleResult.statistics.processing_time?.toFixed(2) || '0.00'}s
                          </span>
                        </div>
                        {googleResult.metadata?.enhancement && (
                          <div className="metadata-item">
                            <span className="metadata-label">Enhancement:</span>
                            <span className="metadata-value enhancement-badge">
                              {googleResult.metadata.enhancement}
                            </span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* No results */}
                    {(!googleResult.matches || googleResult.matches.length === 0) &&
                     (!googleResult.sentence_matches || googleResult.sentence_matches.length === 0) && (
                      <div className="no-matches-message">
                        No matches found on the web.
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
