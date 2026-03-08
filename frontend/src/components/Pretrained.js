import React, { useMemo, useState } from 'react';
import NavBar from './NavBar';
import Sidebar from './Sidebar';
import './Pretrained.css';

export default function Pretrained({ sidebarOpen, setSidebarOpen }) {
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState('No file chosen');
  const [text, setText] = useState('');
  const [runInternetScan, setRunInternetScan] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const buildApiBases = () => {
    const envBase = process.env.REACT_APP_GATEWAY_URL;
    if (envBase) return [envBase.replace(/\/+$/, '')];
    return ['http://127.0.0.1:8000', 'http://localhost:8000'];
  };

  const safeJson = async (response) => {
    const ct = response.headers.get('content-type') || '';
    if (ct.includes('application/json')) return response.json();
    const txt = await response.text();
    try {
      return JSON.parse(txt);
    } catch {
      return { error: txt || `HTTP ${response.status}` };
    }
  };

  const postAnalyzeTextWithRetry = async (payloadObj) => {
    const bases = buildApiBases();
    let lastError = null;

    for (const base of bases) {
      try {
        const response = await fetch(`${base}/api/plagiarism/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json; charset=utf-8' },
          body: JSON.stringify(payloadObj),
        });

        if (!response.ok) {
          const errBody = await safeJson(response);
          throw new Error(errBody?.detail || errBody?.error || JSON.stringify(errBody));
        }
        return await safeJson(response);
      } catch (err) {
        lastError = err;
      }
    }

    throw lastError || new Error('Failed to fetch from gateway API (/analyze)');
  };

  const postAnalyzeFileWithRetry = async (formData) => {
    const bases = buildApiBases();
    let lastError = null;

    for (const base of bases) {
      try {
        const response = await fetch(`${base}/api/plagiarism/analyze-file`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const errBody = await safeJson(response);
          throw new Error(errBody?.detail || errBody?.error || JSON.stringify(errBody));
        }
        return await safeJson(response);
      } catch (err) {
        lastError = err;
      }
    }

    throw lastError || new Error('Failed to fetch from gateway API (/analyze-file)');
  };

  const fmtPct = (v) => Number(v || 0).toFixed(2);
  const clampPct = (v) => Math.min(Math.max(Number(v || 0), 0), 100);

  const getInternetUrls = (res) => {
    if (!res) return [];

    const url1 = res?.internet_result?.url ? [res.internet_result.url] : [];
    const url2 = Array.isArray(res?.internet_result)
      ? res.internet_result.map((x) => x?.url).filter(Boolean)
      : [];
    const url3 = Array.isArray(res?.internet_sources)
      ? res.internet_sources.map((x) => x?.url).filter(Boolean)
      : [];
    const url4 = Array.isArray(res?.web_sources)
      ? res.web_sources.map((x) => x?.url).filter(Boolean)
      : [];
    const url5 = Array.isArray(res?.wsa_result?.web_sources)
      ? res.wsa_result.web_sources.map((x) => x?.url).filter(Boolean)
      : [];
    const url6 =
      res?.wsa_result?.matched_url && res.wsa_result.matched_url !== 'No source found'
        ? [res.wsa_result.matched_url]
        : [];

    return Array.from(new Set([...url1, ...url2, ...url3, ...url4, ...url5, ...url6]));
  };

  const getDisplaySources = (res) => {
    if (!res) return [];

    const sources = [];

    if (Array.isArray(res?.internet_result)) {
      res.internet_result.forEach((item) => {
        if (!item?.url) return;
        sources.push({
          url: item.url,
          type: 'Internet Match',
          score: item.overall_paraphrase_percentage ?? null,
          preview: null,
          textLen: null,
        });
      });
    }

    if (Array.isArray(res?.wsa_result?.web_sources)) {
      res.wsa_result.web_sources.forEach((item) => {
        if (!item?.url) return;
        sources.push({
          url: item.url,
          type: 'Writing Style Source',
          score: null,
          preview: item.preview || null,
          textLen: item.text_len || null,
        });
      });
    }

    if (
      res?.wsa_result?.matched_url &&
      res.wsa_result.matched_url !== 'No source found' &&
      !sources.some((s) => s.url === res.wsa_result.matched_url)
    ) {
      sources.push({
        url: res.wsa_result.matched_url,
        type: 'Best Style Match',
        score: res?.wsa_result?.similarity_score ?? null,
        preview: null,
        textLen: null,
      });
    }

    const uniq = new Map();
    for (const s of sources) {
      if (!uniq.has(s.url)) uniq.set(s.url, s);
    }

    return Array.from(uniq.values());
  };

  const splitIntoSentences = (raw) => {
    if (!raw) return [];
    return raw
      .replace(/\s+/g, ' ')
      .split(/(?<=[.!?।])/g)
      .map((s) => s.trim())
      .filter(Boolean);
  };

  const buildSentenceHighlights = (res, sourceText) => {
    const sentences = splitIntoSentences(sourceText);
    if (!sentences.length) return [];

    const detailedMatches = [];
    if (Array.isArray(res?.internet_result)) {
      res.internet_result.forEach((item) => {
        if (Array.isArray(item?.detailed_matches)) {
          item.detailed_matches.forEach((m) => {
            detailedMatches.push({
              sentenceIndex: m?.sentenceIndex ?? m?.idx,
              score: m?.score ?? m?.similarity ?? item?.overall_paraphrase_percentage ?? 0,
              url: item?.url || null,
            });
          });
        }
      });
    }

    if (detailedMatches.length > 0) {
      const scores = sentences.map(() => ({ score: 0, url: null }));
      detailedMatches.forEach((m) => {
        const idx = Number(m.sentenceIndex);
        if (Number.isFinite(idx) && idx >= 0 && idx < scores.length) {
          const sc = Number(m.score || 0);
          if (sc > scores[idx].score) {
            scores[idx] = { score: sc, url: m.url };
          }
        }
      });

      return sentences.map((sentence, idx) => ({
        text: sentence,
        score: scores[idx].score,
        sourceUrl: scores[idx].url,
      }));
    }

    const fallbackScore = Math.max(
      Number(res?.paraphrase || 0),
      Number(res?.semantic || 0),
      Number(res?.features?.wsa_similarity || 0)
    );

    return sentences.map((sentence) => ({
      text: sentence,
      score: fallbackScore,
      sourceUrl:
        res?.wsa_result?.matched_url && res.wsa_result.matched_url !== 'No source found'
          ? res.wsa_result.matched_url
          : null,
    }));
  };

  const highlightStyle = (score) => {
    const s = clampPct(score);

    if (s >= 70) {
      return {
        background: 'rgba(220, 38, 38, 0.28)',
        borderLeft: '4px solid #dc2626',
        borderRadius: 8,
        padding: '4px 8px',
      };
    }

    if (s >= 40) {
      return {
        background: 'rgba(245, 158, 11, 0.22)',
        borderLeft: '4px solid #f59e0b',
        borderRadius: 8,
        padding: '4px 8px',
      };
    }

    if (s > 0) {
      return {
        background: 'rgba(234, 179, 8, 0.16)',
        borderLeft: '4px solid #eab308',
        borderRadius: 8,
        padding: '4px 8px',
      };
    }

    return {
      background: 'transparent',
      padding: '4px 8px',
    };
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setFileName(selectedFile.name);
      setText('');
    }
  };

  const handleCheck = async () => {
    if (!file && !text.trim()) {
      alert('Please upload a file or paste text');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      let data;

      if (file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('runInternetScan', String(runInternetScan));
        data = await postAnalyzeFileWithRetry(formData);
      } else {
        const payload = {
          studentText: text,
          sourceText: '',
          runInternetScan,
        };
        data = await postAnalyzeTextWithRetry(payload);
      }

      setResult(data);
    } catch (error) {
      alert(
        `Error: ${error.message || error}\n\nCheck that:\n- Gateway: 8000\n- WSA: 8001\n- Paraphrase: 5000\n- Semantic: 8002\nare running.`
      );
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const internetUrls = useMemo(() => getInternetUrls(result), [result]);
  const displaySources = useMemo(() => getDisplaySources(result), [result]);
  const highlightedSentences = useMemo(() => {
    const shownText = file ? result?.extracted_text || text : text;
    return buildSentenceHighlights(result, shownText);
  }, [result, text, file]);

  const decision = String(result?.decision || '').toUpperCase();
  const overallScore = clampPct(result?.overall || 0);

  const verdictMeta = (() => {
    if (decision === 'PLAGIARIZED') {
      return { icon: '⚠️', title: 'Significant Plagiarism Detected' };
    }
    if (decision === 'SUSPICIOUS') {
      return { icon: '⚡', title: 'Moderate Similarity Found' };
    }
    return { icon: '✓', title: 'No Significant Plagiarism' };
  })();

  return (
    <div className="pre-wrap">
      <NavBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

      <div className="pre-body">
        <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <section className="pre-main">
          <div className="pre-modern-container">
            <div className="pre-header">
              <h1 className="pre-title">Plagiarism Detection</h1>
              <p className="pre-subtitle">
                Upload or paste your text to check for plagiarism, paraphrasing, and content similarity
              </p>
            </div>

            <div className="pre-layout-grid">
              <div className="pre-input-column">
                <div className="pre-card-modern">
                  <label className="lbl-block">Your Document</label>

                  <textarea
                    className="pretrained-box-modern"
                    placeholder="Paste your text here or upload a file..."
                    value={text}
                    onChange={(e) => {
                      setText(e.target.value);
                      setFile(null);
                      setFileName('No file chosen');
                    }}
                  />

                  <div className="file-upload-wrapper">
                    <input
                      type="file"
                      id="file-input-pretrained"
                      className="file-input"
                      onChange={handleFileChange}
                      accept=".txt,.pdf,.doc,.docx"
                    />
                    <label htmlFor="file-input-pretrained" className="file-upload-label">
                      📎 {fileName === 'No file chosen' ? 'Upload File' : fileName}
                    </label>
                  </div>

                  <div className="checkbox-wrapper">
                    <input
                      type="checkbox"
                      id="searchWebPretrained"
                      checked={runInternetScan}
                      onChange={(e) => setRunInternetScan(e.target.checked)}
                    />
                    <label htmlFor="searchWebPretrained">Search web for similar content</label>
                  </div>

                  <button
                    className={`pre-check-modern ${loading ? 'loading' : ''}`}
                    onClick={handleCheck}
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <span className="spinner"></span> Analyzing...
                      </>
                    ) : (
                      'Check Plagiarism'
                    )}
                  </button>
                </div>

                {!result && !loading && (
                  <div className="pre-empty-state">
                    <div className="empty-icon">📝</div>
                    <p>Paste or upload text to begin analysis</p>
                  </div>
                )}
              </div>

              <div className="pre-results-column">
                {!result && !loading && (
                  <div className="pre-card-modern results-placeholder">
                    <div className="placeholder-content">
                      <div className="placeholder-icon">✨</div>
                      <p className="placeholder-text">Results will appear here</p>
                    </div>
                  </div>
                )}

                {result && (
                  <div className="pre-results-container">
                    <div className="pre-card-modern verdict-card plagiarism-summary-card">
                      <div className="verdict-header">
                        <span className="verdict-icon">{verdictMeta.icon}</span>
                        <div className="verdict-text">
                          <h3 className="verdict-title">{verdictMeta.title}</h3>
                          <p className="verdict-subtitle">
                            Overall Score: <strong>{fmtPct(overallScore)}%</strong>
                          </p>
                          {result.decision && (
                            <p className="verdict-subtitle">
                              Decision: <strong>{String(result.decision)}</strong>
                            </p>
                          )}
                          {result.internet_sources_count ? (
                            <p className="verdict-subtitle">
                              Sources Used: <strong>{displaySources.length}</strong>
                            </p>
                          ) : null}
                        </div>
                      </div>
                    </div>

                    <div className="pre-scores-grid">
                      {/* Only showing Overall Score as requested */}
                      <div className="score-card">
                        <div className="score-label">Overall Score</div>
                        <div className="score-value">{fmtPct(overallScore)}%</div>
                        <div className="score-bar">
                          <div className="score-fill" style={{ width: `${overallScore}%` }}></div>
                        </div>
                      </div>
                    </div>

                    <div className="pre-card-modern">
                      <h4 className="gauge-title" style={{ marginBottom: 10 }}>
                        Highlighted Document
                      </h4>

                      {highlightedSentences.length > 0 ? (
                        <div style={{ lineHeight: 2 }}>
                          {highlightedSentences.map((item, idx) => (
                            <span key={idx} style={{ marginRight: 6 }}>
                              <span
                                style={highlightStyle(item.score)}
                                title={`Match: ${fmtPct(item.score)}%`}
                              >
                                {item.text}
                              </span>
                              {item.sourceUrl ? (
                                <a
                                  href={item.sourceUrl}
                                  target="_blank"
                                  rel="noreferrer"
                                  style={{ marginLeft: 6, fontSize: 12 }}
                                >
                                  source
                                </a>
                              ) : null}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <p style={{ margin: 0 }}>No highlighted content available.</p>
                      )}
                    </div>

                    <div className="pre-card-modern">
                      <h4 className="gauge-title" style={{ marginBottom: 10 }}>
                        Web Sources
                      </h4>

                      {runInternetScan ? (
                        displaySources.length > 0 ? (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                            {displaySources.map((src, idx) => (
                              <div
                                key={src.url || idx}
                                style={{
                                  padding: 12,
                                  border: '1px solid rgba(255,255,255,0.08)',
                                  borderRadius: 10,
                                  wordBreak: 'break-word',
                                }}
                              >
                                <div style={{ marginBottom: 6 }}>
                                  <a href={src.url} target="_blank" rel="noreferrer">
                                    {src.url}
                                  </a>
                                </div>

                                <div style={{ fontSize: 13, opacity: 0.85, marginBottom: 6 }}>
                                  <strong>Type:</strong> {src.type}
                                  {src.score !== null && src.score !== undefined ? (
                                    <>
                                      {' '}
                                      | <strong>Score:</strong> {fmtPct(src.score)}%
                                    </>
                                  ) : null}
                                  {src.textLen ? (
                                    <>
                                      {' '}
                                      | <strong>Extracted Length:</strong> {src.textLen}
                                    </>
                                  ) : null}
                                </div>

                                {src.preview ? (
                                  <div
                                    style={{
                                      fontSize: 13,
                                      lineHeight: 1.6,
                                      opacity: 0.9,
                                      background: 'rgba(255,255,255,0.03)',
                                      padding: 10,
                                      borderRadius: 8,
                                    }}
                                  >
                                    {src.preview}
                                  </div>
                                ) : null}
                              </div>
                            ))}
                          </div>
                        ) : internetUrls.length > 0 ? (
                          <ul style={{ margin: 0, paddingLeft: 18 }}>
                            {internetUrls.map((u) => (
                              <li key={u} style={{ marginBottom: 6, wordBreak: 'break-all' }}>
                                <a href={u} target="_blank" rel="noreferrer">
                                  {u}
                                </a>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p style={{ margin: 0 }}>
                            No web source link returned.
                            {result?.internet_result?.error ? (
                              <>
                                {' '}
                                <strong>Reason:</strong> {String(result.internet_result.error)}
                              </>
                            ) : null}
                          </p>
                        )
                      ) : (
                        <p style={{ margin: 0 }}>Web scan is turned off.</p>
                      )}
                    </div>

                    {result.used_fallback && (
                      <div className="pre-card-modern fallback-notice">
                        <p style={{ margin: 0 }}>
                          ℹ️ Used fallback scoring because one or more backend components didn’t return usable results.
                          {result?.message ? (
                            <>
                              <br />
                              <strong>Details:</strong> {String(result.message)}
                            </>
                          ) : null}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}