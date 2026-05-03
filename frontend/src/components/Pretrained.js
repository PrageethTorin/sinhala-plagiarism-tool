import React, { useMemo, useRef, useState } from 'react';
import NavBar from './NavBar';
import Sidebar from './Sidebar';
import './Pretrained.css';

export default function Pretrained({ sidebarOpen, setSidebarOpen }) {
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState('No file chosen');
  const [text, setText] = useState('');
  const [runInternetScan, setRunInternetScan] = useState(true);
  const [loading, setLoading] = useState(false);
  const [extractingFile, setExtractingFile] = useState(false);
  const [result, setResult] = useState(null);
  const [toast, setToast] = useState(null);
  const toastTimerRef = useRef(null);
  const fileInputRef = useRef(null);

  const showToast = (message, type = 'info') => {
    if (toastTimerRef.current) {
      clearTimeout(toastTimerRef.current);
    }
    setToast({ message, type });
    toastTimerRef.current = setTimeout(() => setToast(null), 3500);
  };

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

  const buildOcrBases = () => {
    const envBase = process.env.REACT_APP_OCR_URL || process.env.REACT_APP_OLD_BACKEND_URL;
    if (envBase) return [envBase.replace(/\/+$/, '')];
    return ['http://127.0.0.1:5000', 'http://localhost:5000'];
  };

  const postOcrImageWithRetry = async (imageFile) => {
    const bases = buildOcrBases();
    const formData = new FormData();
    formData.append('image', imageFile);
    let lastError = null;

    for (const base of bases) {
      try {
        const response = await fetch(`${base}/api/ocr-extract`, {
          method: 'POST',
          body: formData,
        });
        const data = await safeJson(response);
        if (!response.ok) {
          throw new Error(data?.detail || data?.error || 'OCR extraction failed');
        }
        return data;
      } catch (err) {
        lastError = err;
      }
    }

    throw lastError || new Error('Failed to fetch from OCR API (/api/ocr-extract)');
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

    const isWikipedia = (url) =>
      String(url || '').toLowerCase().includes('wikipedia.org');

    const sources = [];
    const matchType =
      res?.features?.web_match_type || res?.web_match_type || res?.evidence?.web_match_type;

    if (Array.isArray(res?.internet_result)) {
      res.internet_result.forEach((item) => {
        if (!item?.url) return;
        const sourceType =
          matchType === 'direct_copy'
            ? 'Copied Web Source'
            : matchType === 'paraphrase'
              ? 'Possible Paraphrased Source'
              : 'Related Web Source';
        sources.push({
          url: item.url,
          type: sourceType,
          score: item.overall_paraphrase_percentage ?? null,
          reliable: Boolean(item.content_extracted),
          preview: null,
          textLen: item.text_len ?? null,
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
          reliable: Boolean((item.text_len || 0) >= 120),
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
        reliable: true,
        preview: null,
        textLen: null,
      });
    }

    const uniq = new Map();
    for (const s of sources) {
      if (!uniq.has(s.url)) uniq.set(s.url, s);
    }

    return Array.from(uniq.values()).sort((a, b) => {
      const aWiki = isWikipedia(a.url) ? 1 : 0;
      const bWiki = isWikipedia(b.url) ? 1 : 0;
      if (aWiki !== bWiki) return bWiki - aWiki;

      const ar = a.reliable ? 1 : 0;
      const br = b.reliable ? 1 : 0;
      if (ar !== br) return br - ar;

      const as = Number(a.score ?? -1);
      const bs = Number(b.score ?? -1);
      return bs - as;
    });
  };

  const splitIntoSentences = (raw) => {
    if (!raw) return [];
    return raw
      .replace(/\s+/g, ' ')
      .split(/(?<=[.!?।])/g)
      .map((s) => s.trim())
      .filter(Boolean);
  };

  const normalizeSentence = (s) =>
    String(s || '')
      .replace(/\s+/g, ' ')
      .replace(/[.?!à¥¤]+$/g, '')
      .trim()
      .toLowerCase();

  const normalizeToken = (token) =>
    String(token || '')
      .replace(/^[^\w\u0D80-\u0DFF]+|[^\w\u0D80-\u0DFF]+$/g, '')
      .trim()
      .toLowerCase();

  const tokenizePreserveSpaces = (sentence) => {
    if (!sentence) return [];
    const matches = sentence.match(/\S+\s*/g);
    return matches && matches.length ? matches : [sentence];
  };

  const buildNgrams = (word, n = 3) => {
    if (!word || word.length < n) return [];
    const grams = [];
    for (let i = 0; i <= word.length - n; i += 1) {
      grams.push(word.slice(i, i + n));
    }
    return grams;
  };

  const tokenSimilarity = (token, sourceToken) => {
    if (!token || !sourceToken) return 0;
    if (token === sourceToken) return 1;
    const a = buildNgrams(token);
    const b = buildNgrams(sourceToken);
    if (!a.length || !b.length) return 0;
    const setA = new Set(a);
    const setB = new Set(b);
    let inter = 0;
    setA.forEach((g) => {
      if (setB.has(g)) inter += 1;
    });
    const union = setA.size + setB.size - inter;
    return union ? inter / union : 0;
  };

  const buildTokenHighlights = (sentence, sourceSentence, alignedWords) => {
    const tokens = tokenizePreserveSpaces(sentence);
    const sourceTokens = (sourceSentence || '')
      .split(/\s+/)
      .map(normalizeToken)
      .filter(Boolean);

    if (Array.isArray(alignedWords) && alignedWords.length > 0) {
      const indexMap = new Map(
        alignedWords.map((entry) => [
          Number(entry?.token_index),
          String(entry?.match_type || '').toLowerCase(),
        ])
      );
      return tokens.map((text, idx) => {
        const matchType = indexMap.get(idx) || 'none';
        if (matchType === 'exact') return { text, score: 90 };
        if (matchType === 'synonym') return { text, score: 50 };

        // 'none' from backend — try n-gram to catch morphological variants DB missed
        if (sourceTokens.length) {
          const norm = normalizeToken(text);
          if (norm) {
            let best = 0;
            for (let i = 0; i < sourceTokens.length; i += 1) {
              const sim = tokenSimilarity(norm, sourceTokens[i]);
              if (sim > best) best = sim;
              if (best >= 0.9) break;
            }
            if (best >= 0.8) return { text, score: 50 };
            if (best >= 0.65) return { text, score: 35 };
          }
        }
        return { text, score: 0 };
      });
    }

    if (!sourceTokens.length) {
      return tokens.map((text) => ({ text, score: 0 }));
    }

    const sourceSet = new Set(sourceTokens);
    return tokens.map((text) => {
      const norm = normalizeToken(text);
      if (!norm) {
        return { text, score: 0 };
      }
      if (sourceSet.has(norm)) {
        return { text, score: 90 };
      }

      let best = 0;
      for (let i = 0; i < sourceTokens.length; i += 1) {
        const sim = tokenSimilarity(norm, sourceTokens[i]);
        if (sim > best) best = sim;
        if (best >= 0.9) break;
      }

      if (best >= 0.8) return { text, score: 50 };
      if (best >= 0.65) return { text, score: 35 };
      return { text, score: 0 };
    });
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
              studentSentence: m?.student_sentence ?? m?.input_sentence ?? m?.matched_text ?? null,
              sourceSentence: m?.source_sentence ?? m?.matched_text ?? null,
              alignedWords: Array.isArray(m?.aligned_words) ? m.aligned_words : null,
              score: Math.max(
                Number(m?.score ?? 0),
                Number(m?.similarity ?? 0),
                Number(m?.paraphrase_score ?? 0),
                Number(m?.semantic_score ?? 0),
                Number(m?.lexical_score ?? 0),
                Number(item?.overall_paraphrase_percentage ?? 0)
              ),
              url: item?.url || null,
            });
          });
        }
      });
    }

    // DB mode: use paraphrase detailed matches when available.
    if (Array.isArray(res?.paraphrase_result?.detailed_matches)) {
      res.paraphrase_result.detailed_matches.forEach((m) => {
        detailedMatches.push({
          sentenceIndex: m?.sentenceIndex ?? m?.idx,
          studentSentence: m?.student_sentence ?? null,
          sourceSentence: m?.source_sentence ?? null,
          alignedWords: Array.isArray(m?.aligned_words) ? m.aligned_words : null,
          score: m?.paraphrase_score ?? m?.score ?? 0,
          url: null,
        });
      });
    }

    // DB mode fallback: map WSA sentence_map entries using overall WSA similarity.
    // Only apply when similarity is reasonably strong to avoid noisy highlights.
    if (
      detailedMatches.length === 0 &&
      Array.isArray(res?.wsa_result?.sentence_map) &&
      Number(res?.features?.wsa_similarity ?? res?.wsa_result?.similarity_score ?? 0) >= 60
    ) {
      const wsaScore = Number(
        res?.features?.wsa_similarity ?? res?.wsa_result?.similarity_score ?? 0
      );
      res.wsa_result.sentence_map.forEach((s) => {
        detailedMatches.push({
          sentenceIndex: s?.id ? Number(s.id) - 1 : undefined,
          studentSentence: s?.text ?? null,
          score: wsaScore,
          url: null,
        });
      });
    }

    if (detailedMatches.length > 0) {
      const scores = sentences.map(() => ({
        score: 0,
        url: null,
        sourceSentence: null,
        alignedWords: null,
      }));
      const normSentences = sentences.map((s) => normalizeSentence(s));
      detailedMatches.forEach((m) => {
        let idx = Number(m.sentenceIndex);
        if (!Number.isFinite(idx) || idx < 0 || idx >= scores.length) {
          const normStudent = normalizeSentence(m.studentSentence);
          if (normStudent) {
            idx = normSentences.findIndex((s) => s === normStudent);
            if (idx < 0) {
              idx = normSentences.findIndex(
                (s) => s.includes(normStudent) || normStudent.includes(s)
              );
            }
          }
        }
        if (Number.isFinite(idx) && idx >= 0 && idx < scores.length) {
          const sc = Number(m.score || 0);
          if (sc > scores[idx].score) {
            scores[idx] = {
              score: sc,
              url: m.url,
              sourceSentence: m.sourceSentence,
              alignedWords: m.alignedWords,
            };
          }
        }
      });

      return sentences.map((sentence, idx) => ({
        text: sentence,
        score: scores[idx].score,
        sourceUrl: scores[idx].url,
        sourceSentence: scores[idx].sourceSentence,
        alignedWords: scores[idx].alignedWords,
      }));
    }

    // Do not apply fallback sentence highlighting when there are no real detailed matches.
    // This avoids showing "fake" highlighted plagiarism in DB mode and weak-match cases.
    return sentences.map((sentence) => ({
      text: sentence,
      score: 0,
      sourceUrl: null,
    }));
  };

  const highlightStyle = (score, strong = false) => {
    const s = clampPct(score);

    if (s >= 70) {
      return {
        background: strong ? 'rgba(220, 38, 38, 0.6)' : 'rgba(220, 38, 38, 0.28)',
        borderLeft: strong ? '4px solid #b91c1c' : '4px solid #dc2626',
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

  const highlightWordStyle = (score, strong = false) => {
    const s = clampPct(score);
    if (s >= 70) {
      return {
        background: strong ? 'rgba(220, 38, 38, 0.6)' : 'rgba(220, 38, 38, 0.42)',
        borderRadius: 6,
        padding: '2px 4px',
      };
    }
    if (s >= 40) {
      return {
        background: 'rgba(245, 158, 11, 0.45)',
        borderRadius: 6,
        padding: '2px 4px',
      };
    }
    return {
      background: 'transparent',
      padding: '2px 4px',
    };
  };

  const readTextFile = (selectedFile) =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ''));
      reader.onerror = () => reject(new Error('Unable to read text file.'));
      reader.readAsText(selectedFile, 'utf-8');
    });

  const handleFileChange = async (e) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    const allowedExtensions = ['.txt', '.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tif', '.tiff'];
    const lowerName = selectedFile.name.toLowerCase();
    const isImageFile = selectedFile.type.startsWith('image/');
    const isTextFile = lowerName.endsWith('.txt') || selectedFile.type === 'text/plain';
    const hasValidExtension = allowedExtensions.some((ext) => lowerName.endsWith(ext)) || isImageFile;
    if (!hasValidExtension) {
      showToast('Only .txt, .pdf, .doc, .docx, or image files are allowed.', 'error');
      e.target.value = '';
      return;
    }

    const maxSizeBytes = 10 * 1024 * 1024;
    if (selectedFile.size > maxSizeBytes) {
      showToast('File is too large. Maximum allowed size is 10MB.', 'error');
      e.target.value = '';
      return;
    }

    setResult(null);

    if (isImageFile) {
      setExtractingFile(true);
      setFile(null);
      setFileName(`OCR: ${selectedFile.name}`);
      try {
        const data = await postOcrImageWithRetry(selectedFile);
        const extractedText = String(data?.extractedText || '').trim();
        if (!extractedText) {
          throw new Error('No readable Sinhala text found in image.');
        }
        setText(extractedText);
        showToast('Sinhala text extracted from image.', 'success');
      } catch (error) {
        showToast(`OCR failed: ${error.message || error}`, 'error');
        setFileName('No file chosen');
      } finally {
        setExtractingFile(false);
        e.target.value = '';
      }
      return;
    }

    if (isTextFile) {
      setExtractingFile(true);
      setFile(null);
      setFileName(selectedFile.name);
      try {
        const fileText = String(await readTextFile(selectedFile)).trim();
        if (!fileText) {
          throw new Error('No text found in the file.');
        }
        setText(fileText);
        showToast('Text file loaded.', 'success');
      } catch (error) {
        showToast(`File read failed: ${error.message || error}`, 'error');
        setFileName('No file chosen');
      } finally {
        setExtractingFile(false);
        e.target.value = '';
      }
      return;
    }

    setFile(selectedFile);
    setFileName(selectedFile.name);
    setText('');
    showToast('File selected successfully.', 'success');
  };

  const handleCheck = async () => {
    if (!file && !text.trim()) {
      showToast('Please upload a file or paste text before analyzing.', 'warning');
      return;
    }

    if (!file && text.trim().length < 20) {
      showToast('Please enter at least 20 characters for analysis.', 'warning');
      return;
    }

    if (extractingFile) {
      showToast('Please wait until text extraction finishes.', 'warning');
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
      showToast('Analysis completed successfully.', 'success');
    } catch (error) {
      showToast(
        `Analysis failed: ${error.message || error}. Check services on ports 8000, 8001, 5000, 8002.`,
        'error'
      );
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    if (extractingFile) {
      showToast('Please wait until file extraction finishes.', 'warning');
      return;
    }
    if (loading) {
      showToast('Please wait until analysis finishes.', 'warning');
      return;
    }

    setText('');
    setFile(null);
    setFileName('No file chosen');
    setResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    showToast('Cleared text and file selection.', 'info');
  };

  const internetUrls = useMemo(() => getInternetUrls(result), [result]);
  const displaySources = useMemo(() => getDisplaySources(result), [result]);
  const highlightedSentences = useMemo(() => {
    const shownText = file ? result?.extracted_text || text : text;
    return buildSentenceHighlights(result, shownText);
  }, [result, text, file]);

  const decision = String(result?.decision || '').toUpperCase();
  const overallScore = clampPct(result?.overall || 0);
  const webDirectScore = clampPct(
    result?.features?.web_direct_match ?? result?.web_direct_match ?? result?.evidence?.best_direct ?? 0
  );
  const webMatchType =
    result?.features?.web_match_type || result?.web_match_type || result?.evidence?.web_match_type;
  const hasDirectWebCopy = webMatchType === 'direct_copy' || webDirectScore >= 70;
  const hasWebEvidence = Boolean(webMatchType && webMatchType !== 'none') || displaySources.length > 0;
  const displayHasDirectWebCopy = hasDirectWebCopy;
  const displayDecision = displayHasDirectWebCopy ? 'PLAGIARIZED' : decision;
  const displayOverallScore = overallScore;
  const webEvidenceLabel =
    webMatchType === 'direct_copy'
      ? 'Copied from web'
      : webMatchType === 'paraphrase'
        ? 'Possible paraphrased web match'
        : 'Related web source found';

  const verdictMeta = (() => {
    if (displayHasDirectWebCopy) {
      return { icon: '!', title: 'Direct Web Copy Detected' };
    }
    if (displayDecision === 'PLAGIARIZED') {
      return { icon: '⚠️', title: 'Significant Plagiarism Detected' };
    }
    if (displayDecision === 'SUSPICIOUS') {
      return { icon: '⚡', title: 'Moderate Similarity Found' };
    }
    return { icon: '✓', title: 'No Significant Plagiarism' };
  })();

  const isClean = !displayHasDirectWebCopy &&
    !['PLAGIARIZED', 'SUSPICIOUS'].includes(displayDecision);

  const isDbBaseline =
    Boolean(result?.db_mode) &&
    (Boolean(result?.evidence?.flags?.includes?.('db_baseline_created')) ||
      result?.matched_submission_id == null);

  return (
    <div className="pre-wrap">
      <NavBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      {toast && (
        <div className={`pre-toast pre-toast-${toast.type}`} role="status" aria-live="polite">
          {toast.message}
        </div>
      )}

      <div className="pre-body">
        <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <section className="pre-main">
          <div className="pre-modern-container">
            <div className="pre-header">
              <h1 className="pre-title">Plagiarism Detection</h1>
              <p className="pre-subtitle">
                Upload or paste your text to check copied or similar web content
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
                      ref={fileInputRef}
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

                  <div className="pre-action-row">
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
                    <button
                      className="pre-clear-btn"
                      type="button"
                      onClick={handleClear}
                      aria-label="Clear text and uploaded file"
                    >
                      <svg
                        className="pre-clear-icon"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        aria-hidden="true"
                      >
                        <path d="M3 6h18" />
                        <path d="M8 6V4h8v2" />
                        <path d="M8 10v8" />
                        <path d="M12 10v8" />
                        <path d="M16 10v8" />
                      </svg>
                      Clear
                    </button>
                  </div>
                </div>
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
                          <h3
                            className="verdict-title"
                            style={displayHasDirectWebCopy ? { color: '#dc2626' } : undefined}
                          >
                            {verdictMeta.title}
                          </h3>
                          <p className="verdict-subtitle">
                            Overall Score: <strong>{fmtPct(displayOverallScore)}%</strong>
                          </p>
                          {displayDecision && (
                            <p className="verdict-subtitle">
                              Decision: <strong>{displayDecision}</strong>
                            </p>
                          )}
                          {result.internet_sources_count ? (
                            <p className="verdict-subtitle">
                              Sources Used: <strong>{displaySources.length}</strong>
                            </p>
                          ) : null}
                          {webMatchType && webMatchType !== 'none' ? (
                            <p className="verdict-subtitle">
                              Web Evidence: <strong>{webEvidenceLabel}</strong>
                            </p>
                          ) : null}
                        </div>
                      </div>
                    </div>

                    <div className="pre-scores-grid pre-scores-grid-single">
                      <div className="score-card">
                        <div className="score-label">Overall Score</div>
                        <div className="score-value">{fmtPct(displayOverallScore)}%</div>
                        <div className="score-bar">
                          <div className="score-fill" style={{ width: `${displayOverallScore}%` }}></div>
                        </div>
                        {hasWebEvidence && (
                          <div className="score-helper">
                            {webEvidenceLabel}
                          </div>
                        )}
                      </div>
                    </div>

                    {!isDbBaseline && (
                      <div className="pre-card-modern">
                        <h4 className="gauge-title" style={{ marginBottom: 10 }}>
                          Highlighted Document
                        </h4>

                        {highlightedSentences.length > 0 ? (
                          <>
                            {!isClean && (
                              <div style={{ display: 'flex', gap: 16, marginBottom: 12, flexWrap: 'wrap' }}>
                                <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
                                  <span style={{ display: 'inline-block', width: 14, height: 14, borderRadius: 4, background: 'rgba(220, 38, 38, 0.6)', border: '2px solid #b91c1c' }}></span>
                                  Direct copy
                                </span>
                                <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
                                  <span style={{ display: 'inline-block', width: 14, height: 14, borderRadius: 4, background: 'rgba(220, 38, 38, 0.42)', border: '2px solid #dc2626' }}></span>
                                  Plagiarized
                                </span>
                                <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
                                  <span style={{ display: 'inline-block', width: 14, height: 14, borderRadius: 4, background: 'rgba(245, 158, 11, 0.45)', border: '2px solid #f59e0b' }}></span>
                                  Suspicious
                                </span>
                                <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
                                  <span style={{ display: 'inline-block', width: 14, height: 14, borderRadius: 4, background: 'rgba(234, 179, 8, 0.16)', border: '2px solid #eab308' }}></span>
                                  Low similarity
                                </span>
                              </div>
                            )}
                            <div style={{ lineHeight: 2 }}>
                              {highlightedSentences.map((item, idx) => (
                                <span key={idx} style={{ marginRight: 6 }}>
                                  {!isClean && item.sourceSentence ? (
                                    <span title={`Match: ${fmtPct(item.score)}%`}>
                                      {buildTokenHighlights(
                                        item.text,
                                        item.sourceSentence,
                                        item.alignedWords
                                      ).map(
                                        (tok, tIdx) => (
                                          <span key={tIdx} style={highlightWordStyle(tok.score, displayHasDirectWebCopy)}>
                                            {tok.text}
                                          </span>
                                        )
                                      )}
                                    </span>
                                  ) : (
                                    <span
                                      style={highlightStyle(isClean ? 0 : item.score, displayHasDirectWebCopy)}
                                      title={isClean ? undefined : `Match: ${fmtPct(item.score)}%`}
                                    >
                                      {item.text}
                                    </span>
                                  )}
                                </span>
                              ))}
                            </div>
                          </>
                        ) : (
                          <p style={{ margin: 0 }}>No highlighted content available.</p>
                        )}
                      </div>
                    )}

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
                                  {' '}
                                  | <strong>Reliability:</strong> {src.reliable ? 'High' : 'Low'}
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
