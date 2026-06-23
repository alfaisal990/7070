import { useState, useRef, useEffect } from 'react';
import * as api from '../services/api';

export function useChat(fetchMemories) {
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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSendMessage = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!inputText.trim()) return;

    const userPrompt = inputText;
    setInputText('');
    setMessages((prev) => [...prev, { sender: 'user', text: userPrompt }]);
    setIsTyping(true);

    if (streamMode) {
      try {
        setMessages((prev) => [...prev, { sender: 'ai', text: '', isStreaming: true }]);

        const response = await fetch(`/api/chat/stream?prompt=${encodeURIComponent(userPrompt)}&temperature=0.7`);
        if (!response.ok) {
          if (response.status === 400) {
            throw new Error('Potential prompt injection or instruction override detected.');
          }
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

        setMessages((prev) => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg && lastMsg.sender === 'ai') {
            lastMsg.isStreaming = false;
          }
          return updated;
        });

        if (fetchMemories) fetchMemories();
      } catch (error) {
        setMessages((prev) => [
          ...prev.slice(0, -1),
          { sender: 'ai', text: `Error: ${error.message || 'Connection failed.'}` }
        ]);
      } finally {
        setIsTyping(false);
      }
    } else {
      try {
        const data = await api.sendChatMessage(userPrompt, 0.2, 512);
        setMessages((prev) => [...prev, { sender: 'ai', text: data.response }]);
        if (fetchMemories) fetchMemories();
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

  return {
    messages,
    setMessages,
    inputText,
    setInputText,
    isTyping,
    streamMode,
    setStreamMode,
    messagesEndRef,
    handleSendMessage,
    scrollToBottom
  };
}
