import { useState, useEffect } from 'react';
import * as api from '../services/api';

export function useMemory(addToast) {
  const [memories, setMemories] = useState([]);
  const [newMemoryText, setNewMemoryText] = useState('');
  const [newMemoryMeta, setNewMemoryMeta] = useState('{"type": "manual"}');
  const [isSavingMemory, setIsSavingMemory] = useState(false);
  const [memorySearch, setMemorySearch] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);

  const fetchMemories = async () => {
    try {
      const data = await api.fetchMemories();
      setMemories(data.memories || []);
    } catch (err) {
      console.error('Failed to fetch memories', err);
    }
  };

  const handleMemorySearch = async () => {
    if (!memorySearch.trim()) return;
    setIsSearching(true);
    try {
      const data = await api.searchMemory(memorySearch, 5);
      setSearchResults(data.results || []);
    } catch (err) {
      if (addToast) {
        addToast('Search failed: ' + err.message, 'error');
      }
    } finally {
      setIsSearching(false);
    }
  };

  const handleClearMemory = async () => {
    try {
      await api.clearMemory();
      setMemories([]);
      setSearchResults(null);
      if (addToast) {
        addToast('All memories cleared.', 'success');
      }
    } catch (err) {
      if (addToast) {
        addToast('Failed to clear memory: ' + err.message, 'error');
      }
    }
  };

  const handleSaveMemory = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!newMemoryText.trim()) return;

    setIsSavingMemory(true);
    try {
      let meta = {};
      try {
        meta = JSON.parse(newMemoryMeta);
      } catch (err) {
        meta = { type: 'manual', parse_error: true };
      }

      await api.addMemory(newMemoryText, meta);
      setNewMemoryText('');
      fetchMemories();
      if (addToast) {
        addToast('Memory recorded successfully!', 'success');
      }
    } catch (err) {
      if (addToast) {
        addToast('Failed to save memory: ' + err.message, 'error');
      }
    } finally {
      setIsSavingMemory(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, []);

  return {
    memories,
    setMemories,
    newMemoryText,
    setNewMemoryText,
    newMemoryMeta,
    setNewMemoryMeta,
    isSavingMemory,
    memorySearch,
    setMemorySearch,
    searchResults,
    setSearchResults,
    isSearching,
    fetchMemories,
    handleMemorySearch,
    handleClearMemory,
    handleSaveMemory
  };
}
