import React from 'react';

export function MessageRenderer({ text }) {
  if (!text) return null;

  const parts = [];
  let remaining = text;

  const patterns = [
    { name: 'execute_code', regex: /<execute_code>([\s\S]*?)<\/execute_code>/ },
    { name: 'execution_result', regex: /<execution_result>([\s\S]*?)<\/execution_result>/ },
    { name: 'read_file', regex: /<read_file>([\s\S]*?)<\/read_file>/ },
    { name: 'file_content', regex: /<file_content path=".*?">([\s\S]*?)<\/file_content>/ },
    { name: 'write_file', regex: /<write_file path="(.*?)">([\s\S]*?)<\/write_file>/ },
    { name: 'file_status', regex: /<file_status path=".*?">([\s\S]*?)<\/file_status>/ },
    { name: 'markdown_code', regex: /```[a-zA-Z]*\n([\s\S]*?)```/ }
  ];

  let found = true;
  let index = 0;

  while (found) {
    found = false;
    let earliestMatch = null;
    let earliestIndex = -1;
    let patternInfo = null;

    for (const p of patterns) {
      const match = remaining.match(p.regex);
      if (match && match.index !== undefined) {
        if (earliestIndex === -1 || match.index < earliestIndex) {
          earliestIndex = match.index;
          earliestMatch = match;
          patternInfo = p;
        }
      }
    }

    if (earliestMatch && patternInfo) {
      found = true;
      if (earliestIndex > 0) {
        parts.push({ id: index++, type: 'text', content: remaining.substring(0, earliestIndex) });
      }
      parts.push({
        id: index++,
        type: patternInfo.name,
        content: earliestMatch[1],
        fullMatch: earliestMatch[0],
        filePath: patternInfo.name === 'write_file' ? earliestMatch[1] : null
      });
      remaining = remaining.substring(earliestIndex + earliestMatch[0].length);
    }
  }

  if (remaining) {
    parts.push({ id: index++, type: 'text', content: remaining });
  }

  return (
    <div className="rendered-message">
      {parts.map((part) => {
        switch (part.type) {
          case 'text':
            return <p key={part.id} style={{ whiteSpace: 'pre-wrap', marginBottom: '8px' }}>{part.content}</p>;
          case 'markdown_code':
            return (
              <div key={part.id} className="code-block-wrapper">
                <pre><code>{part.content.trim()}</code></pre>
              </div>
            );
          case 'execute_code':
            return (
              <div key={part.id} className="tool-block tool-call">
                <div className="tool-header"><span className="chip chip-purple">💻 Execute Code</span></div>
                <pre><code>{part.content.trim()}</code></pre>
              </div>
            );
          case 'execution_result':
            return (
              <div key={part.id} className="tool-block tool-response">
                <div className="tool-header"><span className="chip chip-green">🖥️ Execution Output</span></div>
                <pre><code>{part.content.trim()}</code></pre>
              </div>
            );
          case 'read_file':
            return (
              <div key={part.id} className="tool-block tool-call">
                <div className="tool-header"><span className="chip chip-cyan">📂 Read File</span></div>
                <div className="tool-path-indicator">Path: <code>{part.content.trim()}</code></div>
              </div>
            );
          case 'file_content':
            return (
              <div key={part.id} className="tool-block tool-response">
                <div className="tool-header"><span className="chip chip-green">📄 File Contents</span></div>
                <pre><code>{part.content.trim()}</code></pre>
              </div>
            );
          case 'write_file':
            return (
              <div key={part.id} className="tool-block tool-call">
                <div className="tool-header"><span className="chip chip-purple">✍️ Write File</span></div>
                <pre><code>{part.content.trim()}</code></pre>
              </div>
            );
          case 'file_status':
            return (
              <div key={part.id} className="tool-block tool-response">
                <div className="tool-header"><span className="chip chip-green">💾 File Operation Status</span></div>
                <pre><code>{part.content.trim()}</code></pre>
              </div>
            );
          default:
            return <p key={part.id}>{part.content}</p>;
        }
      })}
    </div>
  );
}
