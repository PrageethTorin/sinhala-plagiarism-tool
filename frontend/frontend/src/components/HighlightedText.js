/**
 * HighlightedText Component
 * =========================
 * Displays text with semantically similar words highlighted.
 * Uses color coding based on similarity scores:
 * - Red: High similarity (>= 80%)
 * - Orange: Medium similarity (60-80%)
 * - Yellow: Low similarity (40-60%)
 *
 * Author: S N S Dahanayake (IT22920522)
 * Created: January 10, 2026
 */

import React, { useState } from 'react';
import './HighlightedText.css';

/**
 * Renders text with highlighted words based on semantic similarity
 */
const HighlightedText = ({ text, highlights, showTooltips = true }) => {
  const [activeHighlight, setActiveHighlight] = useState(null);

  if (!text || !highlights || highlights.length === 0) {
    return <div className="highlighted-text-container">{text}</div>;
  }

  // Sort highlights by start position
  const sortedHighlights = [...highlights].sort((a, b) => a.start - b.start);

  // Build the highlighted text
  const renderHighlightedText = () => {
    const elements = [];
    let lastEnd = 0;

    sortedHighlights.forEach((highlight, index) => {
      // Add text before this highlight
      if (highlight.start > lastEnd) {
        elements.push(
          <span key={`text-${index}`} className="normal-text">
            {text.substring(lastEnd, highlight.start)}
          </span>
        );
      }

      // Add the highlighted word
      const similarityPercent = (highlight.similarity * 100).toFixed(1);
      const highlightClass = getHighlightClass(highlight.similarity);

      elements.push(
        <span
          key={`highlight-${index}`}
          className={`semantic-highlight ${highlightClass}`}
          style={{ backgroundColor: highlight.highlight_color }}
          onMouseEnter={() => setActiveHighlight(highlight)}
          onMouseLeave={() => setActiveHighlight(null)}
        >
          {text.substring(highlight.start, highlight.end)}
          {showTooltips && activeHighlight === highlight && (
            <span className="highlight-tooltip">
              <strong>Matched:</strong> {highlight.original_word}
              <br />
              <strong>Similarity:</strong> {similarityPercent}%
            </span>
          )}
        </span>
      );

      lastEnd = highlight.end;
    });

    // Add remaining text after last highlight
    if (lastEnd < text.length) {
      elements.push(
        <span key="text-end" className="normal-text">
          {text.substring(lastEnd)}
        </span>
      );
    }

    return elements;
  };

  return (
    <div className="highlighted-text-container">
      <div className="highlighted-text">{renderHighlightedText()}</div>
    </div>
  );
};

/**
 * Get CSS class based on similarity score
 */
const getHighlightClass = (similarity) => {
  if (similarity >= 0.8) return 'high-similarity';
  if (similarity >= 0.6) return 'medium-similarity';
  return 'low-similarity';
};

/**
 * Statistics display for highlighting results
 */
export const HighlightStats = ({ statistics }) => {
  if (!statistics) return null;

  const {
    total_suspicious_words,
    total_original_words,
    matched_words,
    average_similarity,
    high_similarity_count,
    medium_similarity_count,
    low_similarity_count
  } = statistics;

  const matchPercentage = total_suspicious_words > 0
    ? ((matched_words / total_suspicious_words) * 100).toFixed(1)
    : 0;

  return (
    <div className="highlight-stats">
      <h4>Highlight Statistics</h4>
      <div className="stats-grid">
        <div className="stat-item">
          <span className="stat-label">Words Analyzed</span>
          <span className="stat-value">{total_suspicious_words}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Words Matched</span>
          <span className="stat-value">{matched_words} ({matchPercentage}%)</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Avg Similarity</span>
          <span className="stat-value">{(average_similarity * 100).toFixed(1)}%</span>
        </div>
      </div>

      <div className="similarity-breakdown">
        <h5>Similarity Breakdown</h5>
        <div className="breakdown-bars">
          <div className="breakdown-item">
            <span className="breakdown-color high-color"></span>
            <span className="breakdown-label">High (&ge;80%)</span>
            <span className="breakdown-value">{high_similarity_count}</span>
          </div>
          <div className="breakdown-item">
            <span className="breakdown-color medium-color"></span>
            <span className="breakdown-label">Medium (60-80%)</span>
            <span className="breakdown-value">{medium_similarity_count}</span>
          </div>
          <div className="breakdown-item">
            <span className="breakdown-color low-color"></span>
            <span className="breakdown-label">Low (40-60%)</span>
            <span className="breakdown-value">{low_similarity_count}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Legend component showing color meanings
 */
export const HighlightLegend = () => (
  <div className="highlight-legend">
    <span className="legend-title">Legend:</span>
    <div className="legend-items">
      <span className="legend-item">
        <span className="legend-color" style={{ backgroundColor: '#ff6b6b' }}></span>
        High (&ge;80%)
      </span>
      <span className="legend-item">
        <span className="legend-color" style={{ backgroundColor: '#ffa94d' }}></span>
        Medium (60-80%)
      </span>
      <span className="legend-item">
        <span className="legend-color" style={{ backgroundColor: '#ffd43b' }}></span>
        Low (40-60%)
      </span>
    </div>
  </div>
);

export default HighlightedText;
