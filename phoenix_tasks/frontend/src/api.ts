const API_URL = 'http://localhost:8000';

export function getHeaders() {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export const api = {
  auth: {
    register: (body: any) =>
      fetch(`${API_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }).then((r) => {
        if (!r.ok) throw new Error('Registration failed');
        return r.json();
      }),
    login: (formData: URLSearchParams) =>
      fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      }).then(async (r) => {
        if (!r.ok) {
          const err = await r.json();
          throw new Error(err.detail || 'Login failed');
        }
        return r.json();
      }),
    getMe: () =>
      fetch(`${API_URL}/api/auth/me`, {
        method: 'GET',
        headers: getHeaders(),
      }).then((r) => {
        if (!r.ok) throw new Error('Failed to load user session');
        return r.json();
      }),
  },
  projects: {
    list: () =>
      fetch(`${API_URL}/api/projects`, {
        method: 'GET',
        headers: getHeaders(),
      }).then((r) => r.json()),
    create: (body: any) =>
      fetch(`${API_URL}/api/projects`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(body),
      }).then((r) => {
        if (!r.ok) throw new Error('Unauthorized or invalid data');
        return r.json();
      }),
    update: (id: number, body: any) =>
      fetch(`${API_URL}/api/projects/${id}`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify(body),
      }).then((r) => r.json()),
    delete: (id: number) =>
      fetch(`${API_URL}/api/projects/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
      }).then((r) => {
        if (!r.ok) throw new Error('Failed to delete project');
      }),
  },
  tasks: {
    list: (projectId: number) =>
      fetch(`${API_URL}/api/projects/${projectId}/tasks`, {
        method: 'GET',
        headers: getHeaders(),
      }).then((r) => r.json()),
    create: (projectId: number, body: any) =>
      fetch(`${API_URL}/api/projects/${projectId}/tasks`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(body),
      }).then((r) => {
        if (!r.ok) throw new Error('Failed to create task');
        return r.json();
      }),
    update: (id: number, body: any) =>
      fetch(`${API_URL}/api/tasks/${id}`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify(body),
      }).then((r) => r.json()),
    delete: (id: number) =>
      fetch(`${API_URL}/api/tasks/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
      }).then((r) => {
        if (!r.ok) throw new Error('Failed to delete task');
      }),
    getComments: (id: number) =>
      fetch(`${API_URL}/api/tasks/${id}/comments`, {
        method: 'GET',
        headers: getHeaders(),
      }).then((r) => r.json()),
    addComment: (id: number, body: any) =>
      fetch(`${API_URL}/api/tasks/${id}/comments`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(body),
      }).then((r) => {
        if (!r.ok) throw new Error('Failed to create comment');
        return r.json();
      }),
  },
  dashboard: {
    getStats: () =>
      fetch(`${API_URL}/api/dashboard/stats`, {
        method: 'GET',
        headers: getHeaders(),
      }).then((r) => r.json()),
  },
  activities: {
    list: () =>
      fetch(`${API_URL}/api/activities`, {
        method: 'GET',
        headers: getHeaders(),
      }).then((r) => r.json()),
  },
};
