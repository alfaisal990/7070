/**
 * Phoenix AI Frontend API client service.
 * Standardizes fetch operations, error handling, and response processing.
 */

export async function fetchHealth() {
  const res = await fetch('/api/health');
  if (!res.ok) throw new Error(`Health check failed (status: ${res.status})`);
  return res.json();
}

export async function fetchMemories() {
  const res = await fetch('/api/memory');
  if (!res.ok) throw new Error(`Failed to fetch memories (status: ${res.status})`);
  return res.json();
}

export async function scanWorkspace() {
  const res = await fetch('/api/agent/debug/scan');
  if (!res.ok) throw new Error(`Workspace scan failed (status: ${res.status})`);
  return res.json();
}

export async function repairFile(filePath, errorMsg) {
  const res = await fetch('/api/agent/debug/repair', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_path: filePath, error_msg: errorMsg })
  });
  if (!res.ok) throw new Error(`File repair failed (status: ${res.status})`);
  return res.json();
}

export async function refactorCode(code, refactorType) {
  const res = await fetch('/api/agent/refactor', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, refactor_type: refactorType })
  });
  if (!res.ok) throw new Error(`Refactoring failed (status: ${res.status})`);
  return res.json();
}

export async function searchMemory(query, topN = 5) {
  const res = await fetch('/api/memory/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_n: topN })
  });
  if (!res.ok) throw new Error(`Memory search failed (status: ${res.status})`);
  return res.json();
}

export async function clearMemory() {
  const res = await fetch('/api/memory/clear', { method: 'DELETE' });
  if (!res.ok) throw new Error(`Failed to clear memory (status: ${res.status})`);
  return res.json();
}

export async function sendChatMessage(prompt, temperature = 0.2, maxTokens = 512) {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, temperature, max_tokens: maxTokens })
  });
  if (!res.ok) throw new Error(`Chat request failed (status: ${res.status})`);
  return res.json();
}

export async function runCodeInSandbox(code, timeout = 5.0) {
  const res = await fetch('/api/sandbox/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, timeout: parseFloat(timeout) })
  });
  if (!res.ok) throw new Error(`Sandbox execution failed (status: ${res.status})`);
  return res.json();
}

export async function addMemory(text, metadata = {}) {
  const res = await fetch('/api/memory/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, metadata })
  });
  if (!res.ok) throw new Error(`Failed to add memory (status: ${res.status})`);
  return res.json();
}

export async function triggerBackup() {
  const res = await fetch('/api/admin/backup', { method: 'POST' });
  if (!res.ok) throw new Error(`Backup failed (status: ${res.status})`);
  return res.json();
}

export async function searchAITypes(query = '', categoryId = '') {
  let url = `/api/ai_explorer/search?`;
  if (query) url += `query=${encodeURIComponent(query)}&`;
  if (categoryId) url += `category_id=${encodeURIComponent(categoryId)}&`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`AI Explorer search failed (status: ${res.status})`);
  return res.json();
}

export async function addAIModel(categoryId, name, developer, type, parameters, useCase) {
  const res = await fetch('/api/ai_explorer/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      category_id: categoryId,
      name,
      developer,
      type,
      parameters,
      use_case: useCase
    })
  });
  if (!res.ok) throw new Error(`Failed to add AI model (status: ${res.status})`);
  return res.json();
}
