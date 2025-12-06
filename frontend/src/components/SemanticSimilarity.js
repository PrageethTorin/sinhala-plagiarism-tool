import React, { useState } from "react";
import NavBar from "./NavBar";
import Sidebar from "./Sidebar";
import "./SemanticSimilarity.css";

export default function SemanticSimilarity({ sidebarOpen, setSidebarOpen }) {
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState("No file chosen");
  const [googleDocURL, setGoogleDocURL] = useState("");
  const [useWebSearch, setUseWebSearch] = useState(true);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const BACKEND_URL = "http://127.0.0.1:8000";

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (f) {
      setFile(f);
      setFileName(f.name);
      setError(null);
      setResult(null);
    }
  };

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
      form.append("google_doc_url", googleDocURL || "");
      form.append("use_web_search", useWebSearch ? "1" : "0");

      const res = await fetch(`${BACKEND_URL}/api/upload_file_compare`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`Server error ${res.status}: ${txt}`);
      }

      const data = await res.json();
      setResult(data.result);
    } catch (err) {
      console.error(err);
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
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
            <div className="web-toggle">
              <label className="toggle-label">
                <input
                  type="checkbox"
                  checked={useWebSearch}
                  onChange={(e) => setUseWebSearch(e.target.checked)}
                />
                Enable Web Search (Google)
              </label>
            </div>

            {/* Google Doc URL Field */}
            <div className="google-doc-box">
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

          {/* Results */}
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
        </section>
      </div>
    </div>
  );
}
