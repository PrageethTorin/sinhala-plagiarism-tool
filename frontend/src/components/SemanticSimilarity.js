import React, { useState } from "react";
import NavBar from "./NavBar";
import Sidebar from "./Sidebar";
import "./SemanticSimilarity.css";

export default function SemanticSimilarity({ sidebarOpen, setSidebarOpen }) {
  // Tabs
  const [activeTab, setActiveTab] = useState("document");

  // Backend
  const BACKEND_URL = "http://127.0.0.1:8000";

  // -------------------------------
  // Document states (existing)
  // -------------------------------
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState("No file chosen");
  const [googleDocURL, setGoogleDocURL] = useState("");
  const [useWebSearch, setUseWebSearch] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // -------------------------------
  // Paragraph → Web (existing)
  // -------------------------------
  const [singlePara, setSinglePara] = useState("");
  const [paraLoading, setParaLoading] = useState(false);
  const [paraResult, setParaResult] = useState(null);

  // -------------------------------
  // ✅ NEW: Paragraph A vs B
  // -------------------------------
  const [paraA, setParaA] = useState("");
  const [paraB, setParaB] = useState("");
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareResult, setCompareResult] = useState(null);

  // -------------------------------
  // File upload
  // -------------------------------
  const handleFileChange = (e) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      setFileName(f.name);
      setResult(null);
      setError(null);
    }
  };

  const handleCheck = async () => {
    if (!file) return alert("Please choose a document");

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const form = new FormData();
      form.append("file", file);
      form.append("use_web_search", useWebSearch ? "1" : "0");
      if (googleDocURL) form.append("google_doc_url", googleDocURL);

      const res = await fetch(`${BACKEND_URL}/semantic/api/upload_file_compare`, {
        method: "POST",
        body: form,
      });

      const data = await res.json();
      setResult(data.result);
    } catch (err) {
      setError("Document check failed");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------------
  // Paragraph → Web
  // -------------------------------
  const handleParagraphCheck = async () => {
    if (!singlePara.trim()) return alert("Paste a paragraph");

    setParaLoading(true);
    setParaResult(null);

    try {
      const res = await fetch(`${BACKEND_URL}/semantic/api/paragraph_web_check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          paragraph: singlePara,
          use_web_search: useWebSearch,
          google_doc_url: googleDocURL || null,
        }),
      });

      setParaResult(await res.json());
    } catch {
      setError("Paragraph check failed");
    } finally {
      setParaLoading(false);
    }
  };

  // -------------------------------
  // ✅ Paragraph A vs B (NEW)
  // -------------------------------
  const handleCompareParagraphs = async () => {
    if (!paraA.trim() || !paraB.trim()) {
      return alert("Please enter both paragraphs");
    }

    setCompareLoading(true);
    setCompareResult(null);

    try {
      const res = await fetch(
        `${BACKEND_URL}/semantic/api/paragraph_similarity`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ p1: paraA, p2: paraB }),
        }
      );

      setCompareResult(await res.json());
    } catch {
      setError("Comparison failed");
    } finally {
      setCompareLoading(false);
    }
  };

  return (
    <div className="sem-wrap">
      <NavBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

      <div className="sem-body">
        <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <section className="sem-main">
          <h1 className="sem-title">Semantic Similarity Checker</h1>

          {/* Tabs */}
          <div className="tab-bar">
            <button className={`tab ${activeTab==="document"?"active":""}`} onClick={()=>setActiveTab("document")}>Document</button>
            <button className={`tab ${activeTab==="paragraph"?"active":""}`} onClick={()=>setActiveTab("paragraph")}>Paragraph</button>
            <button className={`tab ${activeTab==="compare"?"active":""}`} onClick={()=>setActiveTab("compare")}>Compare</button>
          </div>

          {/* ---------------- DOCUMENT ---------------- */}
          {activeTab === "document" && (
            <div className="sem-card">
              <label className="lbl-block">Upload Document</label>
              <div className="semantic-box" />

              <div className="sem-actions">
                <input type="file" onChange={handleFileChange} />
                <span className="file-name">{fileName}</span>
                <button className="sem-check" onClick={handleCheck}>
                  {loading ? "Checking..." : "Check"}
                </button>
              </div>
            </div>
          )}

          {/* ---------------- PARAGRAPH → WEB ---------------- */}
          {activeTab === "paragraph" && (
            <div className="sem-card">
              <textarea
                className="para-box"
                placeholder="Paste one paragraph..."
                value={singlePara}
                onChange={(e) => setSinglePara(e.target.value)}
              />
              <button className="sem-check" onClick={handleParagraphCheck}>
                {paraLoading ? "Checking..." : "Check Paragraph"}
              </button>

              {paraResult && (
                <div className="primary-result">
                  <div className="result-label-large">Combined Score</div>
                  <div className="result-pill-large">
                    {paraResult.paragraph_score}%
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ---------------- ✅ PARAGRAPH A vs B ---------------- */}
          {activeTab === "compare" && (
            <div className="sem-card">
              <label className="lbl-block">Paragraph A</label>
              <textarea
                className="para-box"
                value={paraA}
                onChange={(e) => setParaA(e.target.value)}
              />

              <label className="lbl-block">Paragraph B</label>
              <textarea
                className="para-box"
                value={paraB}
                onChange={(e) => setParaB(e.target.value)}
              />

              <button className="sem-check" onClick={handleCompareParagraphs}>
                {compareLoading ? "Comparing..." : "Compare"}
              </button>

              {compareResult && (
                <div className="primary-result">
                  <div className="result-label-large">
                    Semantic Similarity
                  </div>
                  <div className="result-pill-large">
                    {compareResult.percentage}%
                  </div>
                </div>
              )}
            </div>
          )}

          {error && <div className="error-box">{error}</div>}
        </section>
      </div>
    </div>
  );
}
