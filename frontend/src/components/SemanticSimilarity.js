// frontend/src/components/SemanticSimilarity.js
import React, { useState } from "react";
import NavBar from "./NavBar";
import Sidebar from "./Sidebar";
import "./SemanticSimilarity.css";

export default function SemanticSimilarity({ sidebarOpen, setSidebarOpen }) {
  // File upload states
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState("No file chosen");
  const [googleDocURL, setGoogleDocURL] = useState("");
  const [useWebSearch, setUseWebSearch] = useState(true);

  // Generic
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Single-paragraph states
  const [singlePara, setSinglePara] = useState("");
  const [paraLoading, setParaLoading] = useState(false);
  const [paraResult, setParaResult] = useState(null);

  // change if your backend is hosted somewhere else
  const BACKEND_URL = "http://127.0.0.1:8000";

  // File handling
  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (f) {
      setFile(f);
      setFileName(f.name);
      setError(null);
      setResult(null);
    }
  };

  // Upload file -> backend extraction + compare
  const handleCheck = async () => {
    if (!file) {
      alert("Please choose a document");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const form = new FormData();
      form.append("file", file);
      if (googleDocURL) form.append("google_doc_url", googleDocURL);
      form.append("use_web_search", useWebSearch ? "1" : "0");

      // NOTE: updated path to include /semantic prefix
      const res = await fetch(`${BACKEND_URL}/semantic/api/upload_file_compare`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`Server error ${res.status}: ${txt}`);
      }

      const data = await res.json();
      // backend returns { source_count, result } (or just result)
      setResult(data.result ?? data);
    } catch (err) {
      console.error(err);
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  // Single paragraph web/doc check
  const handleParagraphCheck = async () => {
    if (!singlePara || !singlePara.trim()) {
      alert("Please paste a paragraph to check");
      return;
    }

    setParaLoading(true);
    setParaResult(null);
    setError(null);

    try {
      const payload = {
        paragraph: singlePara,
        top_k: 3,
        google_doc_url: googleDocURL || null,
        use_web_search: useWebSearch,
      };

      // NOTE: updated path to include /semantic prefix
      const res = await fetch(`${BACKEND_URL}/semantic/api/paragraph_web_check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`Server error ${res.status}: ${txt}`);
      }

      const data = await res.json();
      setParaResult(data);
    } catch (err) {
      console.error(err);
      setError(err.message || "Paragraph check failed");
    } finally {
      setParaLoading(false);
    }
  };

  return (
    <div className="sem-wrap">
      <NavBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

      <div className="sem-body">
        <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <section className="sem-main">
          <h1 className="sem-title">Semantic Similarity Checker</h1>

          {/* Upload card */}
          <div className="sem-card">
            <label className="lbl-block">Upload Document (.pdf / .txt / .docx)</label>
            <div className="semantic-box" />

            <div className="sem-actions">
              <input
                type="file"
                className="file-input"
                accept=".pdf,.txt,.docx"
                onChange={handleFileChange}
              />
              <span className="file-name">{fileName}</span>

              <button className="sem-check" disabled={loading} onClick={handleCheck}>
                {loading ? "Checking..." : "Check"}
              </button>
            </div>

            {/* Web search toggle */}
            <div className="web-toggle" style={{ marginTop: 12 }}>
              <label className="toggle-label">
                <input
                  type="checkbox"
                  checked={useWebSearch}
                  onChange={(e) => setUseWebSearch(e.target.checked)}
                />
                &nbsp;Enable Web Search (Google)
              </label>
            </div>

            {/* Google Doc URL Field */}
            <div className="google-doc-box" style={{ marginTop: 12 }}>
              <label className="lbl-block">Google Doc URL (optional)</label>
              <input
                type="text"
                className="google-input"
                placeholder="https://docs.google.com/document/d/..."
                value={googleDocURL}
                onChange={(e) => setGoogleDocURL(e.target.value)}
              />
            </div>
          </div>

          {/* Error message */}
          {error && <div className="error-box">⚠️ {error}</div>}

          {/* Results from document upload */}
          {result && (
            <div className="result-section">
              <div className="sem-result">
                <div className="result-label">Overall Document Score</div>
                <div className="result-pill">{result.document_score}%</div>
              </div>

              <h3 className="paragraph-title">Paragraph Matches</h3>

              {result.paragraphs.map((p) => (
                <div key={p.index} className="paragraph-card">
                  <strong>
                    Paragraph {p.index + 1} — Score: {p.paragraph_score}%
                  </strong>

                  <div className="paragraph-text">{p.text}</div>

                  <div className="match-list">
                    <strong>Top Matches:</strong>
                    {p.matches.map((m, idx) => (
                      <div key={idx} className="match-box">
                        <div><strong>Match #{idx + 1}</strong></div>
                        <div className="scores">
                          Semantic: {m.semantic.toFixed(3)} | Lexical: {m.lexical.toFixed(3)}
                        </div>
                        <div className="match-text">{m.corpus_text}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ---------------- Single paragraph check ---------------- */}
          <div className="section-title" style={{ marginTop: 28 }}>
            Check a Single Paragraph (Web / Google Doc)
          </div>

          <div className="sem-card" style={{ marginTop: 10 }}>
            <textarea
              className="para-box"
              placeholder="Paste one paragraph here (one idea / one paragraph)..."
              value={singlePara}
              onChange={(e) => setSinglePara(e.target.value)}
            />

            <div style={{ display: "flex", gap: 12, alignItems: "center", marginTop: 8 }}>
              <button className="sem-check" onClick={handleParagraphCheck} disabled={paraLoading}>
                {paraLoading ? "Checking..." : "Check Paragraph"}
              </button>

              <div style={{ color: "#c7c7c7", fontSize: 14 }}>
                Optional: uses same Google Doc URL and web toggle above
              </div>
            </div>

            {/* Show paragraph result */}
            {paraResult && (
              <div style={{ marginTop: 16 }}>
                <div className="primary-result">
                  <div className="result-label-large">Paragraph Combined Score</div>
                  <div className="result-pill-large">{paraResult.paragraph_score}%</div>
                </div>

                <h4 style={{ marginTop: 12 }}>Top Matches</h4>
                {paraResult.matches && paraResult.matches.length ? (
                  paraResult.matches.map((m, i) => (
                    <div key={i} className="match-box" style={{ marginTop: 10 }}>
                      <div style={{ fontWeight: 700 }}>Match #{i + 1} — Combined {(m.combined * 100).toFixed(2)}%</div>
                      <div style={{ color: "#9ee7e2", marginTop: 6 }}>
                        Semantic: {(m.semantic * 100).toFixed(2)}% • Lexical: {(m.lexical * 100).toFixed(2)}% • Stylometric: {(m.stylometric * 100).toFixed(2)}%
                      </div>
                      <div style={{ marginTop: 8, background: "#fff", color: "#222", padding: 8, borderRadius: 6, whiteSpace: "pre-wrap" }}>
                        {m.corpus_text}
                      </div>
                    </div>
                  ))
                ) : (
                  <div style={{ color: "#999", marginTop: 8 }}>No matches found in web/docs.</div>
                )}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
