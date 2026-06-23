import React from 'react';

export function RefactorPage({
  refactorCode,
  setRefactorCode,
  refactorType,
  setRefactorType,
  isRefactoring,
  isOnline,
  refactoredResult,
  onRefactor,
  addToast
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', padding: '24px', gap: '20px', position: 'relative', zIndex: 1 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Automated Code Optimizer</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Paste Python code, select a refactoring scheme, and verify it in the secure Sandbox.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <select
            value={refactorType}
            onChange={(e) => setRefactorType(e.target.value)}
            style={{
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border)',
              borderRadius: '4px',
              color: 'var(--text-primary)',
              padding: '8px 12px',
              fontSize: '0.85rem',
              outline: 'none'
            }}
          >
            <option value="optimize_imports">Optimize Imports</option>
            <option value="add_docstrings">Generate Docstrings</option>
            <option value="ai_optimization">AI Code Clean</option>
          </select>
          <button
            className="btn btn-primary"
            onClick={onRefactor}
            disabled={isRefactoring || !isOnline}
          >
            {isRefactoring ? '⏳ Refactoring...' : '⚡ Refactor Code'}
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', flex: 1, overflow: 'hidden' }}>
        {/* Original Code */}
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)', background: 'var(--bg-elevated)', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
            Original Code
          </div>
          <textarea
            value={refactorCode}
            onChange={(e) => setRefactorCode(e.target.value)}
            placeholder="# Enter code to refactor..."
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: '#a5f3fc',
              fontFamily: 'var(--font-code)',
              fontSize: '0.85rem',
              padding: '14px',
              resize: 'none',
              lineHeight: '1.6'
            }}
          />
        </div>

        {/* Refactored Code */}
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)', background: 'var(--bg-elevated)', fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Refactored Output</span>
            {refactoredResult && refactoredResult.status === 'success' && (
              <button
                onClick={() => {
                  navigator.clipboard.writeText(refactoredResult.refactored);
                  addToast('Code copied to clipboard!', 'success');
                }}
                style={{ background: 'transparent', border: 'none', color: 'var(--accent-2)', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600 }}
              >
                📋 Copy Code
              </button>
            )}
          </div>

          {refactoredResult ? (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <pre style={{ flex: 1, margin: 0, padding: '14px', overflowY: 'auto', background: 'var(--bg-base)', color: '#6ee7b7', fontFamily: 'var(--font-code)', fontSize: '0.85rem', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
                <code>{refactoredResult.refactored}</code>
              </pre>
              <div style={{ padding: '12px 14px', borderTop: '1px solid var(--border)', background: 'var(--bg-elevated)', fontSize: '0.78rem', color: refactoredResult.status === 'success' ? 'var(--success)' : 'var(--danger)' }}>
                {refactoredResult.status === 'success' ? (
                  <span>✓ Sandbox Verification Passed successfully.</span>
                ) : (
                  <span>✗ Validation Failed: {refactoredResult.reason}</span>
                )}
              </div>
            </div>
          ) : (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.88rem' }}>
              Click "Refactor Code" to view optimized output.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
