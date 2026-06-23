import React from 'react';

export function Sidebar({ activeTab, setActiveTab, healthData, isOnline, onScanWorkspace, onTriggerBackup, isBackingUp }) {
  const formatUptime = (seconds) => {
    if (!seconds) return '0s';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <span className="flame">🔥</span>
        <h1>Phoenix AI</h1>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1 }}>
        <div
          className={`nav-item ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          <span className="icon">💬</span>
          <span>AI Assistant</span>
        </div>

        <div
          className={`nav-item ${activeTab === 'sandbox' ? 'active' : ''}`}
          onClick={() => setActiveTab('sandbox')}
        >
          <span className="icon">💻</span>
          <span>Code Sandbox</span>
        </div>

        <div
          className={`nav-item ${activeTab === 'memory' ? 'active' : ''}`}
          onClick={() => setActiveTab('memory')}
        >
          <span className="icon">🧠</span>
          <span>Semantic Memory</span>
        </div>

        <div
          className={`nav-item ${activeTab === 'debug' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('debug');
            onScanWorkspace();
          }}
        >
          <span className="icon">🔧</span>
          <span>Auto Debugger</span>
        </div>

        <div
          className={`nav-item ${activeTab === 'refactor' ? 'active' : ''}`}
          onClick={() => setActiveTab('refactor')}
        >
          <span className="icon">⚡</span>
          <span>Code Refactorer</span>
        </div>

        <div
          className={`nav-item ${activeTab === 'ai_explorer' ? 'active' : ''}`}
          onClick={() => setActiveTab('ai_explorer')}
        >
          <span className="icon">🔍</span>
          <span>مستكشف الذكاء الاصطناعي</span>
        </div>
      </nav>

      {/* Backup Trigger */}
      <div style={{ padding: '0 12px 12px 12px' }}>
        <button 
          className="btn btn-secondary" 
          style={{ width: '100%', fontSize: '0.78rem', padding: '6px' }}
          onClick={onTriggerBackup}
          disabled={!isOnline || isBackingUp}
        >
          {isBackingUp ? '💾 Backing up...' : '💾 Backup DB'}
        </button>
      </div>

      {/* System Info Panel */}
      {healthData && (
        <div className="system-info">
          <div className="system-info-row">
            <span>Model</span>
            <span className="value">{healthData.model?.parameters_human || '—'}</span>
          </div>
          <div className="system-info-row">
            <span>Device</span>
            <span className="value">{healthData.model?.device || '—'}</span>
          </div>
          <div className="system-info-row">
            <span>Vocab</span>
            <span className="value">{healthData.tokenizer?.vocab_size?.toLocaleString() || '—'}</span>
          </div>
          <div className="system-info-row">
            <span>Memories</span>
            <span className="value">{healthData.memory?.count ?? '—'}</span>
          </div>
          <div className="system-info-row">
            <span>Uptime</span>
            <span className="value">{formatUptime(healthData.uptime_seconds)}</span>
          </div>
        </div>
      )}

      <div className="sidebar-footer">
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
          <span className="status-dot" style={{ backgroundColor: isOnline ? 'var(--success)' : 'var(--danger)' }} />
          <span>{isOnline ? 'Connected' : 'Disconnected'}</span>
        </div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
          v1.1.0 • {healthData?.model?.is_trained ? 'Trained' : 'Mock Mode'}
        </div>
      </div>
    </aside>
  );
}
