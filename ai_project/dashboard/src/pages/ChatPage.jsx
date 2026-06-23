import React from 'react';
import { MessageRenderer } from '../components/MessageRenderer';

export function ChatPage({
  messages,
  isTyping,
  inputText,
  setInputText,
  streamMode,
  setStreamMode,
  isOnline,
  onSubmit,
  messagesEndRef
}) {
  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className="message">
            <div className={`avatar ${msg.sender === 'user' ? 'user' : 'ai'}`}>
              {msg.sender === 'user' ? 'U' : 'PX'}
            </div>
            <div className={`bubble ${msg.sender === 'user' ? 'user' : 'ai'}`}>
              <MessageRenderer text={msg.text} />
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

      <form onSubmit={onSubmit} className="input-bar">
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', width: '100%' }}>
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Ask a coding question or request file operations..."
            disabled={!isOnline}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                onSubmit(e);
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
  );
}
