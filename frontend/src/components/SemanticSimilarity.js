import React, { useState, useRef, useCallback } from 'react';
import NavBar from './NavBar';
import Sidebar from './Sidebar';
import './SemanticSimilarity.css';
import axios from 'axios';
import HighlightedText, { HighlightLegend } from './HighlightedText';
import './HighlightedText.css';

export default function SemanticSimilarity({ sidebarOpen, setSidebarOpen }) {
  // Tab state
  const [activeTab, setActiveTab] = useState('paragraph');

  // Paragraph comparison state
  const [originalText, setOriginalText] = useState('');
  const [suspiciousText, setSuspiciousText] = useState('');
  const [threshold] = useState(0.7);
  const [mainLoading, setMainLoading] = useState(false);
  const [result, setResult] = useState(null);

  // Semantic word highlighting state (NEW)
  const [highlightData, setHighlightData] = useState(null);
  const [highlightLoading, setHighlightLoading] = useState(false);
  const [showHighlights, setShowHighlights] = useState(true);

  // Enhanced web search state (DuckDuckGo + Playwright - FREE, no API limits)
  const [enhancedText, setEnhancedText] = useState('');
  const [enhancedLoading, setEnhancedLoading] = useState(false);
  const [enhancedResult, setEnhancedResult] = useState(null);

  // Turnitin-style report state
  const [activeSourceIndex, setActiveSourceIndex] = useState(null);
  const [showWebHighlights, setShowWebHighlights] = useState(true);
  const highlightRefs = useRef({});
  const sourceRefs = useRef({});

  // File upload state
  const [fileUploading, setFileUploading] = useState({ original: false, suspicious: false, enhanced: false });

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
      // Use approved hybrid endpoint (correct methodology)
      const response = await axios.post(`${API_BASE_URL}/api/supervisor-hybrid`, {
        text_pair: {
          original: originalText,
          suspicious: suspiciousText
        },
        threshold: threshold
      });

      setResult(response.data);

      // Automatically fetch word-level highlights after similarity check
      fetchHighlights(originalText, suspiciousText);

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

  // ==================== SEMANTIC WORD HIGHLIGHTING (NEW) ====================
  const fetchHighlights = async (original, suspicious) => {
    if (!original.trim() || !suspicious.trim()) return;

    setHighlightLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/highlight-matches`, {
        original: original,
        suspicious: suspicious,
        threshold: 0.4  // Lower threshold to show more word matches
      });

      setHighlightData(response.data);
    } catch (error) {
      console.error('Highlight API Error:', error);
      // Don't show error for highlights - they're optional
      setHighlightData(null);
    } finally {
      setHighlightLoading(false);
    }
  };

  // ==================== ENHANCED WEB SEARCH (FREE) ====================
  const handleEnhancedSearch = async () => {
    if (!enhancedText.trim()) {
      setError("Please enter text for web search");
      return;
    }

    setEnhancedLoading(true);
    setError("");
    setEnhancedResult(null);
    setActiveSourceIndex(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/enhanced-web-check`, {
        text_pair: {
          original: enhancedText,
          suspicious: ""
        },
        threshold: 0.3  // Lower threshold to show more matches
      });

      setEnhancedResult(response.data);
    } catch (err) {
      console.error(err);
      if (err.response) {
        // Server responded with error
        setError(`Server error: ${err.response.data?.detail || err.response.data?.error || JSON.stringify(err.response.data)}`);
      } else if (err.request) {
        // No response received
        setError("Cannot connect to server. Make sure backend is running on port 8000.");
      } else {
        setError(`Error: ${err.message}`);
      }
    } finally {
      setEnhancedLoading(false);
    }
  };

  // ==================== TURNITIN-STYLE REPORT HELPERS ====================
  const SOURCE_COLORS = [
    { bg: 'rgba(255, 107, 107, 0.3)', border: '#ff6b6b', text: '#ff6b6b' },
    { bg: 'rgba(102, 126, 234, 0.3)', border: '#667eea', text: '#667eea' },
    { bg: 'rgba(255, 169, 77, 0.3)',  border: '#ffa94d', text: '#ffa94d' },
    { bg: 'rgba(81, 207, 102, 0.3)',  border: '#51cf66', text: '#51cf66' },
    { bg: 'rgba(204, 93, 232, 0.3)',  border: '#cc5de8', text: '#cc5de8' },
    { bg: 'rgba(34, 184, 207, 0.3)',  border: '#22b8cf', text: '#22b8cf' },
    { bg: 'rgba(255, 212, 59, 0.3)',  border: '#ffd43b', text: '#ffd43b' },
    { bg: 'rgba(255, 135, 154, 0.3)', border: '#ff879a', text: '#ff879a' },
    { bg: 'rgba(116, 184, 22, 0.3)',  border: '#74b816', text: '#74b816' },
    { bg: 'rgba(166, 140, 255, 0.3)', border: '#a68cff', text: '#a68cff' },
  ];

  // Find words that differ between user text and web source text
  const findChangedWords = useCallback((userText, webText) => {
    if (!userText || !webText) return new Set();
    const userWords = userText.split(/\s+/).filter(Boolean);
    const webWords = new Set(webText.split(/\s+/).filter(Boolean));
    const changed = new Set();
    userWords.forEach((word) => {
      // Word is "changed" if it doesn't appear in the web source (paraphrased)
      if (!webWords.has(word)) {
        changed.add(word);
      }
    });
    return changed;
  }, []);

  const buildHighlightedDocument = useCallback((text, matches) => {
    if (!text || !matches || matches.length === 0) return [{ type: 'text', content: text }];

    // Build regions from matches
    const regions = [];
    matches.forEach((match, sourceIndex) => {
      const userText = match.user_matched_text || '';
      if (!userText) return;

      // Try exact match first
      let pos = text.indexOf(userText);
      if (pos !== -1) {
        regions.push({
          start: pos,
          end: pos + userText.length,
          sourceIndex,
          match,
        });
        return;
      }

      // Fuzzy match: try to find a substantial substring
      // For long texts, try matching by sentences/lines
      const lines = userText.split(/\n+/).filter(l => l.trim().length > 20);
      for (const line of lines) {
        const linePos = text.indexOf(line.trim());
        if (linePos !== -1) {
          regions.push({
            start: linePos,
            end: linePos + line.trim().length,
            sourceIndex,
            match,
          });
        }
      }
    });

    // Sort by start position
    regions.sort((a, b) => a.start - b.start);

    // Merge overlapping regions from the same source, keep higher score for different sources
    const filtered = [];
    for (const region of regions) {
      const last = filtered[filtered.length - 1];
      if (last && region.start <= last.end) {
        if (region.sourceIndex === last.sourceIndex) {
          // Same source: merge (extend)
          last.end = Math.max(last.end, region.end);
        } else if ((region.match.similarity_score || 0) > (last.match.similarity_score || 0)) {
          filtered[filtered.length - 1] = region;
        }
      } else {
        filtered.push(region);
      }
    }

    // Build segments with word-level change detection
    const segments = [];
    let cursor = 0;
    for (const region of filtered) {
      if (region.start > cursor) {
        segments.push({ type: 'text', content: text.slice(cursor, region.start) });
      }

      // Find words that differ between user text and web source
      const highlightContent = text.slice(region.start, region.end);
      const changedWords = findChangedWords(highlightContent, region.match.matched_text || '');

      segments.push({
        type: 'highlight',
        content: highlightContent,
        sourceIndex: region.sourceIndex,
        match: region.match,
        changedWords,
      });
      cursor = region.end;
    }
    if (cursor < text.length) {
      segments.push({ type: 'text', content: text.slice(cursor) });
    }

    return segments;
  }, [findChangedWords]);

  const scrollToSource = useCallback((index) => {
    setActiveSourceIndex(index);
    const el = sourceRefs.current[index];
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, []);

  const scrollToHighlight = useCallback((index) => {
    setActiveSourceIndex(index);
    const el = highlightRefs.current[index];
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.classList.add('pulse-highlight');
      setTimeout(() => el.classList.remove('pulse-highlight'), 1500);
    }
  }, []);

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
    setEnhancedText("");
    setResult(null);
    setEnhancedResult(null);
    setHighlightData(null);
    setActiveSourceIndex(null);
    setError("");
  };

  const handleFileUpload = async (e, textType) => {
    const file = e.target.files[0];
    if (!file) return;

    // Reset input so the same file can be re-selected
    e.target.value = '';

    const fileExt = file.name.split('.').pop().toLowerCase();
    const allowedTypes = ['txt', 'pdf', 'docx'];

    if (!allowedTypes.includes(fileExt)) {
      setError(`Unsupported file type: .${fileExt}. Please upload .txt, .pdf, or .docx files.`);
      return;
    }

    // Client-side file size check (10 MB)
    if (file.size > 10 * 1024 * 1024) {
      setError(`File too large (${(file.size / (1024 * 1024)).toFixed(1)} MB). Maximum is 10 MB.`);
      return;
    }

    const setText = (text) => {
      if (textType === 'original') setOriginalText(text);
      else if (textType === 'suspicious') setSuspiciousText(text);
      else if (textType === 'enhanced') setEnhancedText(text);
    };

    setError('');

    // All files: send to backend for extraction (handles encoding detection for Sinhala)
    // PDF/DOCX/TXT files: send to backend for extraction
    setFileUploading((prev) => ({ ...prev, [textType]: true }));

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_BASE_URL}/api/extract-text`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 30000,
      });

      if (response.data.success && response.data.text) {
        setText(response.data.text);
      } else {
        setError('No text could be extracted from the file.');
      }
    } catch (err) {
      console.error('File extraction error:', err);
      if (err.response) {
        setError(err.response.data?.detail || 'Failed to extract text from file.');
      } else if (err.code === 'ECONNABORTED') {
        setError('File extraction timed out. Please try a smaller file.');
      } else {
        setError('Cannot connect to server. Make sure backend is running on port 8000.');
      }
    } finally {
      setFileUploading((prev) => ({ ...prev, [textType]: false }));
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
              <span className="tab-text">Semantic Similarity (Comparison)</span>
            </button>
            <button
              className={`tab-btn ${activeTab === 'enhanced' ? 'active' : ''}`}
              onClick={() => setActiveTab('enhanced')}
            >
              <span className="tab-icon">🌐</span>
              <span className="tab-text">Semantic Similarity (Web Search)</span>
          
            </button>
          </div>

          {/* ==================== TAB CONTENT ==================== */}
          <div className="tab-content">

            {/* ========== PARAGRAPH COMPARISON TAB ========== */}
            {activeTab === 'paragraph' && (
              <div className="tab-panel">
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
                          accept=".txt,.pdf,.docx"
                          id="original-file"
                          disabled={fileUploading.original}
                        />
                        <label htmlFor="original-file" className={`upload-btn ${fileUploading.original ? 'uploading' : ''}`}>
                          {fileUploading.original ? (<><span className="loading-spinner"></span>Extracting...</>) : 'Upload'}
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
                          accept=".txt,.pdf,.docx"
                          id="suspicious-file"
                          disabled={fileUploading.suspicious}
                        />
                        <label htmlFor="suspicious-file" className={`upload-btn ${fileUploading.suspicious ? 'uploading' : ''}`}>
                          {fileUploading.suspicious ? (<><span className="loading-spinner"></span>Extracting...</>) : 'Upload'}
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
                        'Detect'
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

                    {/* Case Type Badge */}
                    {result.metadata?.case_type && (
                      <div className="case-type-section">
                        <span className={`case-badge ${result.metadata.case_type}`}>
                          {result.metadata.case_type === 'easy_negative' && '✓ Easy Negative'}
                          {result.metadata.case_type === 'easy_positive' && '⚠ Easy Positive'}
                          {result.metadata.case_type === 'difficult' && '🔍 Difficult Case (ML Used)'}
                        </span>
                        <span className="method-badge">
                          {result.metadata.method === 'custom_only' ? 'Custom Algorithm' : 'Hybrid + Fine-tuned Model'}
                        </span>
                      </div>
                    )}

                    {/* Component Scores */}
                    {result.components && (
                      <div className="components-section">
                        <h3 className="section-title">Score Breakdown</h3>
                        <div className="components-grid">
                          <div className="component-item">
                            <div className="component-name">Custom Score</div>
                            <div className="component-desc">(Jaccard + N-grams + Word Order)</div>
                            <div className="component-value">{(result.components.custom_score * 100).toFixed(1)}%</div>
                          </div>
                          {result.components.embedding_score !== undefined && result.components.embedding_score !== null && (
                            <div className="component-item">
                              <div className="component-name">Embedding Score</div>
                              <div className="component-desc">(Fine-tuned MiniLM Model)</div>
                              <div className="component-value">{(result.components.embedding_score * 100).toFixed(1)}%</div>
                            </div>
                          )}
                          <div className="component-item highlight">
                            <div className="component-name">Final Score</div>
                            <div className="component-desc">
                              {result.metadata?.case_type === 'difficult'
                                ? '(Custom + Embedding) / 2'
                                : '(Custom Score Only)'}
                            </div>
                            <div className="component-value">{(result.components.final_score * 100).toFixed(1)}%</div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Text Comparison with Inline Highlights */}
                    <div className="text-comparison-section">
                      <div className="section-header">
                        <h3 className="section-title">Text Comparison</h3>
                        {highlightData && highlightData.highlights && highlightData.highlights.length > 0 && (
                          <label className="toggle-label">
                            <input
                              type="checkbox"
                              checked={showHighlights}
                              onChange={(e) => setShowHighlights(e.target.checked)}
                            />
                            Word Highlights
                          </label>
                        )}
                      </div>

                      {showHighlights && highlightData && highlightData.highlights && highlightData.highlights.length > 0 && (
                        <HighlightLegend />
                      )}

                      <div className="comparison-panels">
                        {/* Original Text Panel */}
                        <div className="comparison-panel">
                          <div className="panel-label">Original Text</div>
                          <div className="panel-text-content">
                            {originalText}
                          </div>
                        </div>

                        {/* Suspicious Text Panel - with inline highlights */}
                        <div className="comparison-panel suspicious-panel">
                          <div className="panel-label">Suspicious Text</div>
                          <div className="panel-text-content">
                            {highlightLoading ? (
                              <div className="highlight-loading-inline">
                                <span className="loading-spinner"></span>
                                Analyzing words...
                              </div>
                            ) : showHighlights && highlightData && highlightData.highlights && highlightData.highlights.length > 0 ? (
                              <HighlightedText
                                text={highlightData.suspicious_text}
                                highlights={highlightData.highlights}
                                showTooltips={true}
                              />
                            ) : (
                              suspiciousText
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Compact highlight stats inline */}
                      {showHighlights && highlightData && highlightData.statistics && (
                        <div className="inline-highlight-stats">
                          <span className="inline-stat">
                            <strong>{highlightData.statistics.matched_words}</strong> of {highlightData.statistics.total_suspicious_words} words matched
                          </span>
                          <span className="inline-stat-sep">|</span>
                          <span className="inline-stat">
                            Avg: <strong>{(highlightData.statistics.average_similarity * 100).toFixed(1)}%</strong>
                          </span>
                          <span className="inline-stat-sep">|</span>
                          <span className="inline-stat high-stat">
                            {highlightData.statistics.high_similarity_count} high
                          </span>
                          <span className="inline-stat medium-stat">
                            {highlightData.statistics.medium_similarity_count} med
                          </span>
                          <span className="inline-stat low-stat">
                            {highlightData.statistics.low_similarity_count} low
                          </span>
                        </div>
                      )}
                    </div>

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

            {/* ========== ENHANCED WEB SEARCH TAB ========== */}
            {activeTab === 'enhanced' && (
              <div className="tab-panel">
                <div className="text-card single-input">
                  <div className="card-header">
                    <span className="card-title">Suspicious Text to Check</span>
                    <div className="file-upload-wrapper">
                      <input
                        type="file"
                        className="file-input-hidden"
                        onChange={(e) => handleFileUpload(e, 'enhanced')}
                        accept=".txt,.pdf,.docx"
                        id="enhanced-file"
                        disabled={fileUploading.enhanced}
                      />
                      <label htmlFor="enhanced-file" className={`upload-btn ${fileUploading.enhanced ? 'uploading' : ''}`}>
                        {fileUploading.enhanced ? (<><span className="loading-spinner"></span>Extracting...</>) : 'Upload'}
                      </label>
                    </div>
                  </div>
                  <textarea
                    className="text-input"
                    rows={8}
                    value={enhancedText}
                    onChange={(e) => setEnhancedText(e.target.value)}
                    placeholder="Enter only the suspicious text - we'll find the original source from the web..."
                  />
                  <div className="char-counter">
                    {enhancedText.length} characters
                  </div>
                </div>

                <div className="action-buttons centered">
                  <button
                    className="primary-action-btn"
                    onClick={handleEnhancedSearch}
                    disabled={enhancedLoading}
                  >
                    {enhancedLoading ? (
                      <>
                        <span className="loading-spinner"></span>
                        Searching...
                      </>
                    ) : (
                      'Detect'
                    )}
                  </button>
                  <button
                    className="secondary-action-btn"
                    onClick={() => { setEnhancedText(''); setEnhancedResult(null); }}
                  >
                    Clear
                  </button>
                </div>

                {/* Enhanced Search Results */}
                {enhancedResult && (
                  <div className="results-container">
                    {enhancedResult.success === false ? (
                      <div className="error-container">
                        <h3 className="section-title">Setup Required</h3>
                        <p>{enhancedResult.error}</p>
                        {enhancedResult.install_instructions && (
                          <div className="install-instructions">
                            <h4>Install dependencies:</h4>
                            <ol>
                              {Object.entries(enhancedResult.install_instructions).map(([step, cmd]) => (
                                <li key={step}><code>{cmd}</code></li>
                              ))}
                            </ol>
                          </div>
                        )}
                      </div>
                    ) : (
                      <>
                        <h3 className="section-title">Web Search Results</h3>

                        {/* Verdict and Summary */}
                        <div className="overall-score-section">
                          <div className="score-circle-container">
                            <div
                              className="score-circle"
                              style={{
                                background: `conic-gradient(
                                  ${getScoreColor(enhancedResult.max_similarity || 0)} ${(enhancedResult.max_similarity || 0) * 360}deg,
                                  #3a3546 ${(enhancedResult.max_similarity || 0) * 360}deg
                                )`
                              }}
                            >
                              <div className="score-inner">
                                <span className="score-percent">
                                  {((enhancedResult.max_similarity || 0) * 100).toFixed(1)}%
                                </span>
                                <span className="score-label">Max Similarity</span>
                              </div>
                            </div>
                          </div>

                          <div className="verdict-section">
                            {enhancedResult.verdict && (
                              <div className={`verdict-badge ${enhancedResult.verdict.includes('Original') ? 'original' : 'plagiarized'}`}>
                                {enhancedResult.verdict}
                              </div>
                            )}
                            <div className="stats-grid">
                              <div className="stat-item">
                                <span className="stat-value">{enhancedResult.statistics?.sources_scraped || 0}</span>
                                <span className="stat-label">Pages Scraped</span>
                              </div>
                              <div className="stat-item">
                                <span className="stat-value">{enhancedResult.statistics?.paragraphs_checked || 0}</span>
                                <span className="stat-label">Paragraphs</span>
                              </div>
                              <div className="stat-item">
                                <span className="stat-value">{enhancedResult.statistics?.matches_found || 0}</span>
                                <span className="stat-label">Matches</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* ===== TURNITIN-STYLE REPORT ===== */}
                        {enhancedResult.matches && enhancedResult.matches.length > 0 && (
                          <div className="turnitin-report-section">
                            <div className="section-header">
                              <h3 className="section-title">Similarity Report</h3>
                              <label className="toggle-label">
                                <input
                                  type="checkbox"
                                  checked={showWebHighlights}
                                  onChange={(e) => setShowWebHighlights(e.target.checked)}
                                />
                                Show Highlights
                              </label>
                            </div>

                            <div className="turnitin-report">
                              {/* Left: Document with highlights */}
                              <div className="report-document">
                                <div className="report-document-header">Your Document</div>
                                <div className="report-document-body">
                                  {showWebHighlights ? (
                                    buildHighlightedDocument(enhancedText, enhancedResult.matches).map((seg, i) =>
                                      seg.type === 'text' ? (
                                        <span key={i}>{seg.content}</span>
                                      ) : (
                                        <span
                                          key={i}
                                          ref={(el) => { highlightRefs.current[seg.sourceIndex] = el; }}
                                          className={`report-highlight ${activeSourceIndex === seg.sourceIndex ? 'active' : ''}`}
                                          style={{
                                            backgroundColor: SOURCE_COLORS[seg.sourceIndex % SOURCE_COLORS.length].bg,
                                            borderBottomColor: SOURCE_COLORS[seg.sourceIndex % SOURCE_COLORS.length].border,
                                          }}
                                          onClick={() => scrollToSource(seg.sourceIndex)}
                                          title={`Source ${seg.sourceIndex + 1}: ${seg.match.source_title || seg.match.source_url || ''} — ${((seg.match.similarity_score || 0) * 100).toFixed(1)}%`}
                                        >
                                          <span
                                            className="source-marker"
                                            style={{
                                              backgroundColor: SOURCE_COLORS[seg.sourceIndex % SOURCE_COLORS.length].border,
                                            }}
                                          >
                                            {seg.sourceIndex + 1}
                                          </span>
                                          {/* Render words with changed-word highlighting */}
                                          {seg.changedWords && seg.changedWords.size > 0 ? (
                                            seg.content.split(/(\s+)/).map((word, wi) => {
                                              if (/^\s+$/.test(word)) return <span key={wi}>{word}</span>;
                                              return seg.changedWords.has(word) ? (
                                                <span
                                                  key={wi}
                                                  className="changed-word"
                                                  style={{
                                                    backgroundColor: 'rgba(255, 193, 7, 0.5)',
                                                    borderBottom: '2px solid #ffc107',
                                                    borderRadius: '2px',
                                                    padding: '0 1px',
                                                  }}
                                                  title="Semantically changed word"
                                                >
                                                  {word}
                                                </span>
                                              ) : (
                                                <span key={wi}>{word}</span>
                                              );
                                            })
                                          ) : (
                                            seg.content
                                          )}
                                        </span>
                                      )
                                    )
                                  ) : (
                                    enhancedText
                                  )}
                                </div>
                              </div>

                              {/* Right: Source list */}
                              <div className="report-sources">
                                <div className="report-sources-header">
                                  Sources ({enhancedResult.matches.length})
                                </div>
                                <div className="report-sources-list">
                                  {enhancedResult.matches.map((match, index) => {
                                    const color = SOURCE_COLORS[index % SOURCE_COLORS.length];
                                    const hostname = (() => {
                                      try { return new URL(match.source_url).hostname; } catch { return match.source_url || 'Unknown'; }
                                    })();

                                    return (
                                      <div
                                        key={index}
                                        ref={(el) => { sourceRefs.current[index] = el; }}
                                        className={`source-card ${activeSourceIndex === index ? 'active' : ''}`}
                                        style={{ borderLeftColor: color.border }}
                                        onClick={() => scrollToHighlight(index)}
                                      >
                                        <div className="source-card-top">
                                          <span className="source-number" style={{ backgroundColor: color.border }}>
                                            {index + 1}
                                          </span>
                                          <span className="source-score" style={{ color: getScoreColor(match.similarity_score || 0) }}>
                                            {((match.similarity_score || 0) * 100).toFixed(1)}%
                                          </span>
                                        </div>
                                        <div className="source-hostname">{hostname}</div>
                                        {match.source_title && (
                                          <div className="source-title-text">{match.source_title}</div>
                                        )}
                                        <div className="source-card-meta">
                                          <span className={`case-badge small ${match.case_type}`}>
                                            {match.case_type === 'easy_negative' && 'Easy Negative'}
                                            {match.case_type === 'easy_positive' && 'Easy Positive'}
                                            {match.case_type === 'difficult' && 'Difficult (ML)'}
                                            {match.case_type === 'paraphrase_detected' && 'Paraphrase'}
                                          </span>
                                        </div>
                                        <div className="source-score-breakdown">
                                          <span className="mini-pill">Custom {((match.custom_score || 0) * 100).toFixed(0)}%</span>
                                          {match.embedding_score != null && (
                                            <span className="mini-pill">Embed {(match.embedding_score * 100).toFixed(0)}%</span>
                                          )}
                                        </div>
                                        {match.source_url && (
                                          <a
                                            href={match.source_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="source-link"
                                            onClick={(e) => e.stopPropagation()}
                                          >
                                            Open source
                                          </a>
                                        )}
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Metadata */}
                        <div className="metadata-section">
                          <div className="metadata-item">
                            <span className="metadata-label">Processing Time:</span>
                            <span className="metadata-value">
                              {enhancedResult.processing_time?.toFixed(2) || enhancedResult.statistics?.processing_time_seconds?.toFixed(2) || '0.00'}s
                            </span>
                          </div>
                          {enhancedResult.metadata && (
                            <>
                              <div className="metadata-item">
                                <span className="metadata-label">Search Engine:</span>
                                <span className="metadata-value">{enhancedResult.metadata.search_engine}</span>
                              </div>
                              <div className="metadata-item">
                                <span className="metadata-label">Scraper:</span>
                                <span className="metadata-value">{enhancedResult.metadata.scraper}</span>
                              </div>
                            </>
                          )}
                        </div>

                        {/* No matches */}
                        {(!enhancedResult.matches || enhancedResult.matches.length === 0) && (
                          <div className="no-matches-message">
                            No similar content found on the web. The text appears to be original.
                          </div>
                        )}
                      </>
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
