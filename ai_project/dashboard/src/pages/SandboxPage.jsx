import React from 'react';

export function SandboxPage({
  sandboxCode,
  setSandboxCode,
  sandboxTimeout,
  setSandboxTimeout,
  isRunning,
  isOnline,
  sandboxOutput,
  onRun
}) {
  return (
    <div className="sandbox-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Timeout (s):
            <input
              type="number"
              value={sandboxTimeout}
              onChange={(e) => setSandboxTimeout(e.target.value)}
              style={{
                width: '60px',
                marginLeft: '8px',
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                color: 'var(--text-primary)',
                padding: '2px 6px',
                outline: 'none'
              }}
            />
          </label>
        </div>
        <button
          className="btn btn-primary"
          onClick={onRun}
          disabled={isRunning || !isOnline}
        >
          {isRunning ? '⏳ Running...' : '▶ Run Code'}
        </button>
      </div>

      <div className="code-editor">
        <div className="code-editor-header">
          <span>sandbox_run.py</span>
          <span>Python 3.10+</span>
        </div>
        <textarea
          value={sandboxCode}
          onChange={(e) => setSandboxCode(e.target.value)}
          placeholder="# Enter Python code here..."
        />
      </div>

      {sandboxOutput && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <h3 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 500 }}>Output</h3>
          <div
            className={`output-block ${
              sandboxOutput.exit_code === 0 && sandboxOutput.status === 'success' ? 'success' : 'error'
            }`}
          >
            {sandboxOutput.status === 'timeout' && (
              <div style={{ color: 'var(--danger)', fontWeight: 'bold' }}>[Process Timeout Expired]</div>
            )}
            {sandboxOutput.status === 'blocked' && (
              <div style={{ color: 'var(--danger)', fontWeight: 'bold' }}>[Security Access Violation Detected]</div>
            )}
            
            {sandboxOutput.stdout && (
              <div>
                <strong style={{ fontSize: '0.8rem', opacity: 0.8 }}>stdout:</strong>
                <pre style={{ margin: '4px 0 12px 0' }}><code>{sandboxOutput.stdout}</code></pre>
              </div>
            )}
            {sandboxOutput.stderr && (
              <div>
                <strong style={{ fontSize: '0.8rem', opacity: 0.8 }}>stderr:</strong>
                <pre style={{ margin: '4px 0 0 0', color: sandboxOutput.status === 'success' ? 'var(--warning)' : 'inherit' }}>
                  <code>{sandboxOutput.stderr}</code>
                </pre>
              </div>
            )}
            {!sandboxOutput.stdout && !sandboxOutput.stderr && (
              <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>[No output produced]</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
