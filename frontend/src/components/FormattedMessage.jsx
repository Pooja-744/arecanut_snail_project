import React from 'react';

/**
 * FormattedMessage component.
 * Parses markdown-like patterns and renders clean, structured HTML
 * eliminating raw asterisks (*, **), stray dashes (-), or formatting clutter.
 */
export default function FormattedMessage({ content }) {
  if (!content) return null;

  // Split lines
  const lines = content.split('\n');
  const elements = [];
  let currentList = [];
  let listKey = 0;

  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`ul-${listKey++}`} style={{ margin: '8px 0', paddingLeft: '20px', listStyleType: 'none' }}>
          {currentList.map((item, idx) => (
            <li key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '6px', lineHeight: '1.5' }}>
              <span style={{ color: '#16a34a', fontSize: '1rem', lineHeight: '1.2' }}>•</span>
              <div>{renderInline(item)}</div>
            </li>
          ))}
        </ul>
      );
      currentList = [];
    }
  };

  const renderInline = (text) => {
    // Replace **bold** with <strong>
    const parts = [];
    const boldRegex = /\*\*(.*?)\*\*/g;
    let lastIndex = 0;
    let match;

    while ((match = boldRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(cleanText(text.substring(lastIndex, match.index)));
      }
      parts.push(
        <strong key={match.index} style={{ fontWeight: 700, color: 'inherit' }}>
          {cleanText(match[1])}
        </strong>
      );
      lastIndex = boldRegex.lastIndex;
    }

    if (lastIndex < text.length) {
      parts.push(cleanText(text.substring(lastIndex)));
    }

    return parts.length > 0 ? parts : cleanText(text);
  };

  // Strip remaining unwanted raw markdown asterisks or symbols
  const cleanText = (str) => {
    return str.replace(/^\*+\s*/, '').replace(/\*+$/, '');
  };

  lines.forEach((line, i) => {
    const trimmed = line.trim();

    if (!trimmed) {
      flushList();
      return;
    }

    // Check for headers (### or ##)
    if (trimmed.startsWith('### ') || trimmed.startsWith('## ')) {
      flushList();
      const headerText = trimmed.replace(/^#+\s*/, '');
      elements.push(
        <h4 key={`h-${i}`} style={{ fontSize: '0.95rem', fontWeight: 800, margin: '10px 0 4px', color: '#14532d' }}>
          {renderInline(headerText)}
        </h4>
      );
      return;
    }

    // Check for bullet points: starts with * , - , • 
    if (/^[\*\-•]\s+/.test(trimmed)) {
      const itemText = trimmed.replace(/^[\*\-•]\s+/, '');
      currentList.push(itemText);
      return;
    }

    // Check for numbered list: 1. , 2. 
    if (/^\d+\.\s+/.test(trimmed)) {
      flushList();
      const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
      if (numMatch) {
        elements.push(
          <div key={`num-${i}`} style={{ display: 'flex', gap: '8px', margin: '6px 0', alignItems: 'flex-start' }}>
            <span style={{
              background: '#dcfce7',
              color: '#15803d',
              fontWeight: 700,
              fontSize: '0.75rem',
              borderRadius: '50%',
              width: '20px',
              height: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              marginTop: '2px'
            }}>
              {numMatch[1]}
            </span>
            <div style={{ flex: 1, lineHeight: '1.5' }}>
              {renderInline(numMatch[2])}
            </div>
          </div>
        );
        return;
      }
    }

    // Normal paragraph line
    flushList();
    elements.push(
      <p key={`p-${i}`} style={{ margin: '4px 0', lineHeight: '1.5' }}>
        {renderInline(trimmed)}
      </p>
    );
  });

  flushList();

  return <div style={{ fontSize: '0.9rem' }}>{elements}</div>;
}
