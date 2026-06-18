import React, { useState, useEffect, useRef } from 'react';

function App() {
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'sandbox' | 'memory'
  const [isOnline, setIsOnline] = useState(false);
  const [modelName, setModelName] = useState('Phoenix-54M');

  // Chat state
  const [messages, setMessages] = useState([
    {
      sender: 'ai',
      text: 'Hello! I am Phoenix AI, your local Python coding assistant. How can I help you write, explain, or debug Python code today?'
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [streamMode, setStreamMode] = useState(true);
  const messagesEndRef = useRef(null);

  // Sandbox state
  const [sandboxCode, setSandboxCode] = useState(
    `# Write your Python code here\ndef greet(name):\n    return f"Hello, {name}!"\n\nprint(greet("Phoenix AI"))\n`
  );
  const [sandboxOutput, setSandboxOutput] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [sandboxTimeout, setSandboxTimeout] = useState(5.0);

  // Memory state
  const [memories, setMemories] = useState([]);
  const [newMemoryText, setNewMemoryText] = useState('');
  const [newMemoryMeta, setNewMemoryMeta] = useState('{"type": "manual"}');
  const [isSavingMemory, setIsSavingMemory] = useState(false);

  // Auto-scroll chat to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Check backend health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('/api/memory');
        if (res.ok) {
          setIsOnline(true);
          // Fetch memories when we are online
          const data = await res.json();
          setMemories(data.memories || []);
        } else {
          setIsOnline(false);
        }
      } catch (err) {
        setIsOnline(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  // Fetch memories helper
  const fetchMemories = async () => {
    try {
      const res = await fetch('/api/memory');
      if (res.ok) {
        const data = await res.json();
        setMemories(data.memories || []);
      }
    } catch (err) {
      console.error('Failed to fetch memories', err);
    }
  };

  // Chat message submit
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const userPrompt = inputText;
    setInputText('');
    setMessages((prev) => [...prev, { sender: 'user', text: userPrompt }]);
    setIsTyping(true);

    if (streamMode) {
      // Streaming Response
      try {
        setMessages((prev) => [...prev, { sender: 'ai', text: '', isStreaming: true }]);
        
        const response = await fetch(`/api/chat/stream?prompt=${encodeURIComponent(userPrompt)}&temperature=0.7`);
        if (!response.ok) {
          throw new Error('Streaming failed or backend is busy.');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let accumulatedText = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          accumulatedText += chunk;

          setMessages((prev) => {
            const updated = [...prev];
            const lastMsg = updated[updated.length - 1];
            if (lastMsg && lastMsg.sender === 'ai' && lastMsg.isStreaming) {
              lastMsg.text = accumulatedText;
            }
            return updated;
          });
        }

        // Finalize message
        setMessages((prev) => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg && lastMsg.sender === 'ai') {
            lastMsg.isStreaming = false;
          }
          return updated;
        });
        
        // Refresh memories in background in case the agent stored something
        fetchMemories();
      } catch (error) {
        setMessages((prev) => [
          ...prev.slice(0, -1),
          { sender: 'ai', text: `Error: ${error.message || 'Connection failed.'}` }
        ]);
      } finally {
        setIsTyping(false);
      }
    } else {
      // Non-Streaming Agent Loop (Runs tools like code execution)
      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: userPrompt, temperature: 0.2, max_tokens: 512 })
        });
        
        if (!res.ok) {
          throw new Error('Failed to get a response from the agent.');
        }

        const data = await res.json();
        setMessages((prev) => [...prev, { sender: 'ai', text: data.response }]);
        fetchMemories();
      } catch (error) {
        setMessages((prev) => [
          ...prev,
          { sender: 'ai', text: `Error: ${error.message || 'Connection failed.'}` }
        ]);
      } finally {
        setIsTyping(false);
      }
    }
  };

  // Run code in sandbox
  const handleRunSandbox = async () => {
    setIsRunning(true);
    setSandboxOutput(null);
    try {
      const res = await fetch('/api/sandbox/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: sandboxCode, timeout: parseFloat(sandboxTimeout) })
      });
      if (res.ok) {
        const data = await res.json();
        setSandboxOutput(data);
      } else {
        setSandboxOutput({ status: 'error', stderr: 'HTTP Error ' + res.status, stdout: '', exit_code: -1 });
      }
    } catch (err) {
      setSandboxOutput({ status: 'error', stderr: err.message, stdout: '', exit_code: -1 });
    } finally {
      setIsRunning(false);
    }
  };

  // Save memory manually
  const handleSaveMemory = async (e) => {
    e.preventDefault();
    if (!newMemoryText.trim()) return;

    setIsSavingMemory(true);
    try {
      let meta = {};
      try {
        meta = JSON.parse(newMemoryMeta);
      } catch (e) {
        meta = { type: 'manual', parse_error: true };
      }

      const res = await fetch('/api/memory/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: newMemoryText, metadata: meta })
      });

      if (res.ok) {
        setNewMemoryText('');
        fetchMemories();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsSavingMemory(false);
    }
  };

  // Helper to parse Agent text and style tool calls, markdown code blocks, etc.
  const renderMessageContent = (text) => {
    if (!text) return null;

    // Regex to split by markdown code blocks (```python ... ```) or tool tags
    // Let's do a simple line-based parse or match-based parse for nice visual rendering.
    const parts = [];
    let remaining = text;
    
    // Patterns to scan for
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
        // Push preceding plain text
        if (earliestIndex > 0) {
          parts.push({
            id: index++,
            type: 'text',
            content: remaining.substring(0, earliestIndex)
          });
        }

        // Push matched block
        parts.push({
          id: index++,
          type: patternInfo.name,
          content: earliestMatch[1],
          fullMatch: earliestMatch[0],
          // extra metadata if needed
          filePath: patternInfo.name === 'write_file' ? earliestMatch[1] : null
        });

        remaining = remaining.substring(earliestIndex + earliestMatch[0].length);
      }
    }

    if (remaining) {
      parts.push({
        id: index++,
        type: 'text',
        content: remaining
      });
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
                  <pre>
                    <code>{part.content.trim()}</code>
                  </pre>
                </div>
              );
            case 'execute_code':
              return (
                <div key={part.id} className="tool-block tool-call">
                  <div className="tool-header">
                    <span className="chip chip-purple">💻 Execute Code</span>
                  </div>
                  <pre><code>{part.content.trim()}</code></pre>
                </div>
              );
            case 'execution_result':
              return (
                <div key={part.id} className="tool-block tool-response">
                  <div className="tool-header">
                    <span className="chip chip-green">🖥️ Execution Output</span>
                  </div>
                  <pre><code>{part.content.trim()}</code></pre>
                </div>
              );
            case 'read_file':
              return (
                <div key={part.id} className="tool-block tool-call">
                  <div className="tool-header">
                    <span className="chip chip-cyan">📂 Read File</span>
                  </div>
                  <div className="tool-path-indicator">Path: <code>{part.content.trim()}</code></div>
                </div>
              );
            case 'file_content':
              return (
                <div key={part.id} className="tool-block tool-response">
                  <div className="tool-header">
                    <span className="chip chip-green">📄 File Contents</span>
                  </div>
                  <pre><code>{part.content.trim()}</code></pre>
                </div>
              );
            case 'write_file':
              return (
                <div key={part.id} className="tool-block tool-call">
                  <div className="tool-header">
                    <span className="chip chip-purple">✍️ Write File</span>
                  </div>
                  <pre><code>{part.content.trim()}</code></pre>
                </div>
              );
            case 'file_status':
              return (
                <div key={part.id} className="tool-block tool-response">
                  <div className="tool-header">
                    <span className="chip chip-green">💾 File Operation Status</span>
                  </div>
                  <pre><code>{part.content.trim()}</code></pre>
                </div>
              );
            default:
              return <p key={part.id}>{part.content}</p>;
          }
        })}
      </div>
    );
  };

  return (
    <div className="layout">
      {/* Sidebar Panel */}
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
        </nav>

        <div className="sidebar-footer">
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
            <span className={`status-dot`} style={{ backgroundColor: isOnline ? 'var(--success)' : 'var(--danger)' }} />
            <span>{isOnline ? 'Connected' : 'Disconnected'}</span>
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
            Model: {modelName}
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-panel">
        <header className="panel-header">
          <h2>
            {activeTab === 'chat' && 'AI Assistant Chat'}
            {activeTab === 'sandbox' && 'Secure Code Execution Sandbox'}
            {activeTab === 'memory' && 'Long-Term Semantic Memory Store'}
          </h2>
        </header>

        {/* Tab 1: Chat Assistant */}
        {activeTab === 'chat' && (
          <div className="chat-container">
            <div className="messages">
              {messages.map((msg, index) => (
                <div key={index} className="message">
                  <div className={`avatar ${msg.sender === 'user' ? 'user' : 'ai'}`}>
                    {msg.sender === 'user' ? 'U' : 'PX'}
                  </div>
                  <div className={`bubble ${msg.sender === 'user' ? 'user' : 'ai'}`}>
                    {renderMessageContent(msg.text)}
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="message">
                  <div className="avatar ai">PX</div>
                  <div className="bubble ai">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSendMessage} className="input-bar">
              <div style={{ display: 'flex', gap: '10px', alignItems: 'center', width: '100%' }}>
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="Ask a coding question or request file operations..."
                  disabled={!isOnline}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage(e);
                    }
                  }}
                />
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={!isOnline || !inputText.trim() || isTyping}
                >
                  Send
                </button>
              </div>
              <div style={{ display: 'flex', gap: '15px', marginTop: '6px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={streamMode}
                    onChange={(e) => setStreamMode(e.target.checked)}
                  />
                  Stream Output
                </label>
                <span>Press Enter to send (Shift+Enter for new line)</span>
              </div>
            </form>
          </div>
        )}

        {/* Tab 2: Code Sandbox */}
        {activeTab === 'sandbox' && (
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
                onClick={handleRunSandbox}
                disabled={isRunning || !isOnline}
              >
                {isRunning ? 'Running...' : 'Run Code'}
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
                  {sandboxOutput.stdout && (
                    <div>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '4px' }}>stdout:</div>
                      {sandboxOutput.stdout}
                    </div>
                  )}
                  {sandboxOutput.stderr && (
                    <div style={{ marginTop: sandboxOutput.stdout ? '10px' : '0' }}>
                      <div style={{ color: 'var(--danger)', fontSize: '0.75rem', marginBottom: '4px' }}>stderr:</div>
                      {sandboxOutput.stderr}
                    </div>
                  )}
                  {!sandboxOutput.stdout && !sandboxOutput.stderr && (
                    <span style={{ color: 'var(--text-muted)' }}>[Process exited with code {sandboxOutput.exit_code} and produced no output]</span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Vector Memory */}
        {activeTab === 'memory' && (
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
            {/* Form to add memory manually */}
            <div style={{ padding: '24px 24px 0', borderBottom: '1px solid var(--border)' }}>
              <form onSubmit={handleSaveMemory} style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
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
            </div>

            {/* List memories */}
            <div className="memory-container" style={{ flex: 1 }}>
              {memories.length === 0 ? (
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
        )}
      </main>
    </div>
  );
}

export default App;
