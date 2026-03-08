import React, { useState } from 'react';

export function HighlightLegend() {
  return (
    <div className="highlight-legend">
      <div className="legend-item">
        <span className="legend-color high"></span>
        <span className="legend-label">High Similarity (80-100%)</span>
      </div>
      <div className="legend-item">
        <span className="legend-color medium"></span>
        <span className="legend-label">Medium Similarity (50-79%)</span>
      </div>
      <div className="legend-item">
        <span className="legend-color low"></span>
        <span className="legend-label">Low Similarity (40-49%)</span>
      </div>
    </div>
  );
}

export default function HighlightedText({ text = '', highlights = [], showTooltips = true }) {
  const [hoveredIndex, setHoveredIndex] = useState(null);

  if (!highlights || highlights.length === 0) {
    return <span>{text}</span>;
  }

  // Sort highlights by start position to build the text correctly
  const sortedHighlights = [...highlights].sort((a, b) => a.start - b.start);

  // Build array of text segments with their highlight data
  const segments = [];
  let lastEnd = 0;

  sortedHighlights.forEach((highlight, index) => {
    // Add non-highlighted text before this highlight
    if (highlight.start > lastEnd) {
      segments.push({
        type: 'text',
        content: text.substring(lastEnd, highlight.start),
      });
    }

    // Add highlighted text
    segments.push({
      type: 'highlight',
      content: text.substring(highlight.start, highlight.end),
      similarity: highlight.similarity || 0,
      originalWord: highlight.original_word || '',
      suspiciousWord: highlight.suspicious_word || '',
      index: index,
    });

    lastEnd = highlight.end;
  });

  // Add remaining non-highlighted text
  if (lastEnd < text.length) {
    segments.push({
      type: 'text',
      content: text.substring(lastEnd),
    });
  }

  // Determine highlight color based on similarity score
  const getHighlightClass = (similarity) => {
    if (similarity >= 0.8) return 'highlight-high';
    if (similarity >= 0.5) return 'highlight-medium';
    return 'highlight-low';
  };

  return (
    <span className="highlighted-text-container">
      {segments.map((segment, idx) => {
        if (segment.type === 'text') {
          return <span key={idx}>{segment.content}</span>;
        }

        return (
          <span
            key={idx}
            className={`highlighted-word ${getHighlightClass(segment.similarity)}`}
            onMouseEnter={() => showTooltips && setHoveredIndex(segment.index)}
            onMouseLeave={() => setHoveredIndex(null)}
            title={showTooltips ? `Similarity: ${(segment.similarity * 100).toFixed(1)}%` : ''}
          >
            {segment.content}
            {showTooltips && hoveredIndex === segment.index && (
              <div className="highlight-tooltip">
                <div className="tooltip-content">
                  <div className="tooltip-label">Similar to:</div>
                  <div className="tooltip-word">{segment.originalWord}</div>
                  <div className="tooltip-label">Similarity:</div>
                  <div className="tooltip-score">
                    {(segment.similarity * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            )}
          </span>
        );
      })}
    </span>
  );
}
