import React from 'react';

export function DebuggerPage({
  workspaceFiles,
  detectedIssues,
  isScanning,
  isOnline,
  repairResults,
  isRepairing,
  onScan,
  onRepair
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', padding: '24px', gap: '20px', position: 'relative', zIndex: 1 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Active Workspace Audit</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Proactively scans workspace files for syntax errors and executes automated code fixes.
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={onScan}
          disabled={isScanning || !isOnline}
        >
          {isScanning ? '⏳ Auditing...' : '🔍 Rescan Workspace'}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', flex: 1, overflow: 'hidden' }}>
        {/* Scan files list */}
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px', overflowY: 'auto' }}>
          <h4 style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>Scanned Files ({workspaceFiles.length})</h4>
          {workspaceFiles.length === 0 ? (
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No files found or scanner is offline.</span>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {workspaceFiles.map((file, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-elevated)', padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', fontSize: '0.82rem', fontFamily: 'var(--font-code)' }}>
                  <span style={{ color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{file}</span>
                  <span className="chip chip-green">Active</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Detected issues list */}
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px', overflowY: 'auto' }}>
          <h4 style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>Detected Issues ({detectedIssues.length})</h4>
          {detectedIssues.length === 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1, color: 'var(--success)', gap: '6px' }}>
              <span style={{ fontSize: '24px' }}>🛡️</span>
              <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Workspace Clean. No Syntax Errors Found!</span>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {detectedIssues.map((issue, i) => (
                <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '8px', background: 'var(--bg-elevated)', padding: '14px', borderRadius: 'var(--radius)', border: '1px solid var(--danger)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--danger)', fontFamily: 'var(--font-code)' }}>{issue.file_path}</span>
                    <span className="chip chip-red">{issue.issue_type}</span>
                  </div>
                  <pre style={{ background: 'var(--bg-base)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '8px 10px', fontSize: '0.78rem', color: '#fca5a5', overflowX: 'auto', fontFamily: 'var(--font-code)' }}>
                    <code>{issue.details}</code>
                  </pre>

                  {repairResults[issue.file_path] ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '6px' }}>
                      <div style={{ fontSize: '0.8rem', fontWeight: 500, color: repairResults[issue.file_path].status === 'success' ? 'var(--success)' : 'var(--danger)' }}>
                        Status: {repairResults[issue.file_path].status === 'success' ? '✓ Fix Applied Successfully' : '✗ Repair Failed'}
                      </div>
                      {repairResults[issue.file_path].sandbox_output && (
                        <pre style={{ background: 'var(--bg-base)', padding: '8px', borderRadius: '4px', fontSize: '0.75rem', fontFamily: 'var(--font-code)', overflowX: 'auto', color: 'var(--text-secondary)' }}>
                          <code>{repairResults[issue.file_path].sandbox_output}</code>
                        </pre>
                      )}
                    </div>
                  ) : (
                    <button
                      className="btn btn-secondary"
                      style={{ alignSelf: 'flex-start', marginTop: '4px' }}
                      onClick={() => onRepair(issue.file_path, issue.details)}
                      disabled={isRepairing[issue.file_path]}
                    >
                      {isRepairing[issue.file_path] ? '⏳ Repairing...' : '🔧 Fix Issue'}
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
