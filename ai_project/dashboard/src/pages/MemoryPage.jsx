import React, { useState } from 'react';

export function MemoryPage({
  newMemoryText,
  setNewMemoryText,
  newMemoryMeta,
  setNewMemoryMeta,
  isSavingMemory,
  onSaveMemory,
  memorySearch,
  setMemorySearch,
  isSearching,
  onMemorySearch,
  searchResults,
  setSearchResults,
  memories,
  onClearMemory,
  isOnline,
  addToast
}) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setUploadFile(e.target.files[0]);
    }
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    // Check 5MB limit
    if (uploadFile.size > 5 * 1024 * 1024) {
      addToast('File exceeds 5MB size limit.', 'error');
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', uploadFile);

    try {
      const res = await fetch('/api/memory/upload', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        addToast(`Successfully ingested ${uploadFile.name}!`, 'success');
        setUploadFile(null);
        // Reset file input element
        const fileInput = document.getElementById('rag-file-input');
        if (fileInput) fileInput.value = '';
      } else {
        const data = await res.json();
        addToast(data.detail || 'Upload failed.', 'error');
      }
    } catch (err) {
      addToast('Ingestion error: ' + err.message, 'error');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', position: 'relative', zIndex: 1 }}>
      
      {/* Form to add memory manually */}
      <div style={{ padding: '24px 24px 0', borderBottom: '1px solid var(--border)' }}>
        <form onSubmit={onSaveMemory} style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: 600 }}>Record Semantic Memory</h3>
          <div style={{ display: 'flex', gap: '10px' }}>
            <input
              type="text"
              value={newMemoryText}
              onChange={(e) => setNewMemoryText(e.target.value)}
              placeholder="Enter factual data, previous learning, or preference to record..."
              style={{
                flex: 1,
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
                padding: '10px 14px',
                fontSize: '0.9rem',
                outline: 'none'
              }}
              disabled={!isOnline}
            />
            <input
              type="text"
              value={newMemoryMeta}
              onChange={(e) => setNewMemoryMeta(e.target.value)}
              placeholder='Metadata JSON (e.g. {"category": "coding"})'
              style={{
                width: '260px',
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
                padding: '10px 14px',
                fontSize: '0.9rem',
                outline: 'none',
                fontFamily: 'var(--font-code)'
              }}
              disabled={!isOnline}
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!isOnline || !newMemoryText.trim() || isSavingMemory}
            >
              Save
            </button>
          </div>
        </form>

        {/* Upload File to RAG memory store */}
        <form onSubmit={handleUploadSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '16px', padding: '12px 14px', background: 'var(--bg-surface)', border: '1px dashed var(--border)', borderRadius: 'var(--radius)' }}>
          <h3 style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 500 }}>Ingest Document via RAG Pipeline (.txt, .md, .py, .csv, .json)</h3>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <input
              id="rag-file-input"
              type="file"
              accept=".txt,.md,.py,.csv,.json"
              onChange={handleFileChange}
              style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}
              disabled={!isOnline || isUploading}
            />
            <button
              type="submit"
              className="btn btn-secondary"
              disabled={!isOnline || !uploadFile || isUploading}
              style={{ padding: '6px 12px', fontSize: '0.8rem' }}
            >
              {isUploading ? '⏳ Ingesting...' : '📤 Upload & Ingest'}
            </button>
          </div>
        </form>

        {/* Memory search + clear */}
        <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', alignItems: 'center' }}>
          <div className="search-bar" style={{ flex: 1 }}>
            <input
              type="text"
              value={memorySearch}
              onChange={(e) => setMemorySearch(e.target.value)}
              placeholder="🔍 Search memories by semantic similarity..."
              onKeyDown={(e) => { if (e.key === 'Enter') onMemorySearch(); }}
              disabled={!isOnline}
            />
            <button className="btn btn-secondary" onClick={onMemorySearch} disabled={!isOnline || isSearching || !memorySearch.trim()}>
              {isSearching ? '...' : 'Search'}
            </button>
          </div>
          {memories.length > 0 && (
            <button className="btn btn-danger" onClick={onClearMemory} disabled={!isOnline} style={{ fontSize: '0.78rem' }}>
              Clear All
            </button>
          )}
        </div>
      </div>

      {/* Search results or memory list */}
      <div className="memory-container" style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
        {searchResults !== null ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                Search Results ({searchResults.length})
              </h3>
              <button className="btn btn-secondary" onClick={() => setSearchResults(null)} style={{ fontSize: '0.78rem', padding: '5px 12px' }}>
                ← Back to All
              </button>
            </div>
            {searchResults.map((res, index) => (
              <div key={index} className="memory-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ whiteSpace: 'pre-wrap', flex: 1 }}>{res.text}</div>
                  <span className="chip chip-cyan" style={{ marginLeft: '12px', flexShrink: 0 }}>
                    {(res.similarity * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="memory-meta">
                  Metadata: {JSON.stringify(res.metadata || {})}
                </div>
              </div>
            ))}
          </div>
        ) : memories.length === 0 ? (
          <div className="empty-state">
            <span className="big-icon">🧠</span>
            <h3>Memory is Empty</h3>
            <p>Memories are captured during user interactions or can be added manually above.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <h3 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
              Stored Vectors ({memories.length})
            </h3>
            {memories.map((mem, index) => (
              <div key={index} className="memory-card">
                <div style={{ whiteSpace: 'pre-wrap' }}>{mem.text}</div>
                <div className="memory-meta">
                  Metadata: {JSON.stringify(mem.metadata || {})}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
