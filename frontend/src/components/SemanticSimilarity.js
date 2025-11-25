// frontend/src/components/SemanticSimilarity.js
import React, { useState } from "react";
import NavBar from "./NavBar";
import Sidebar from "./Sidebar";
import "./SemanticSimilarity.css";

export default function SemanticSimilarity({ sidebarOpen, setSidebarOpen }) {
  const [original, setOriginal] = useState("");
  const [comparison, setComparison] = useState(""); // text loaded from file or typed
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null); // { score, label }
  const [error, setError] = useState(null);

  // change if your backend uses a different host/port
  const BACKEND_URL = "http://127.0.0.1:8000";

  // File input -> read text content and set as comparison text
  const handleFileChange = (e) => {
    setError(null);
    const file = e.target.files && e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target.result;
      setComparison(text);
    };
    reader.onerror = () => {
      setError("Failed to read file. Make sure it's a text file (.txt).");
    };
    reader.readAsText(file, "UTF-8");
  };

  async function onCheck() {
    setError(null);
    setResult(null);

    // basic validation
    if (!original?.trim()) {
      setError("Please enter the Original text.");
      return;
    }
    if (!comparison?.trim()) {
      setError("Please enter or upload the Comparison text (file or paste).");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/similarity`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ a: original, b: comparison }),
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`Server error ${res.status}: ${txt}`);
      }
      const data = await res.json();
      // data expected: { score: 0.87, label: "High" }
      setResult(data);
    } catch (err) {
      console.error(err);
      setError(err.message || "Unknown error calling API");
    } finally {
      setLoading(false);
    }
  }

  const percent = result ? `${(result.score * 100).toFixed(1)}%` : "—";

  return (
    <div className="semantic-wrap">
      <NavBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      <div className="semantic-body">
        <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <section className="semantic-main">
          <h1 className="semantic-title">Semantic Similarity</h1>

          <div className="semantic-card">
            <label className="lbl-block">Original:</label>
            <textarea
              className="text-box"
              value={original}
              onChange={(e) => setOriginal(e.target.value)}
              placeholder="Paste the original text here..."
              rows={8}
            />

            <label className="lbl-block" style={{ marginTop: 12 }}>
              Comparison (paste text or upload a .txt file):
            </label>
            <textarea
              className="text-box"
              value={comparison}
              onChange={(e) => setComparison(e.target.value)}
              placeholder="Paste the text to compare or choose a file..."
              rows={6}
            />

            <div className="semantic-actions" style={{ marginTop: 10 }}>
              <input
                type="file"
                className="file-input"
                accept=".txt"
                onChange={handleFileChange}
              />
              <button
                className="semantic-check"
                onClick={onCheck}
                disabled={loading}
              >
                {loading ? "Checking..." : "Check"}
              </button>
            </div>
          </div>

          <div className="semantic-result" style={{ marginTop: 18 }}>
            <div className="result-label">Similarity Score</div>
            <div className="result-pill" style={{ minWidth: 80 }}>
              {result ? percent : "—"}
            </div>

            <div style={{ marginTop: 8 }}>
              {result && (
                <div>
                  <strong>Label:</strong> {result.label}
                </div>
              )}
              {error && (
                <div style={{ color: "crimson", marginTop: 8 }}>{error}</div>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
