const API_BASE = 'http://localhost:8000/api/v1';

export const signupUser = async (userData) => {
  const resp = await fetch(`${API_BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData)
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Signup failed');
  }
  const data = await resp.json();
  if (data.access_token) {
    localStorage.setItem('mandimitra_token', data.access_token);
    localStorage.setItem('mandimitra_user', JSON.stringify(data.user));
  }
  return data;
};

export const loginUser = async (username, password) => {
  const resp = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Login failed');
  }
  const data = await resp.json();
  if (data.access_token) {
    localStorage.setItem('mandimitra_token', data.access_token);
    localStorage.setItem('mandimitra_user', JSON.stringify(data.user));
  }
  return data;
};

export const getCurrentUser = async () => {
  const token = localStorage.getItem('mandimitra_token');
  if (!token) return null;
  try {
    const resp = await fetch(`${API_BASE}/auth/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!resp.ok) return null;
    const user = await resp.json();
    localStorage.setItem('mandimitra_user', JSON.stringify(user));
    return user;
  } catch {
    return null;
  }
};

export const getStoredUser = () => {
  try {
    const raw = localStorage.getItem('mandimitra_user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

export const logoutUser = () => {
  localStorage.removeItem('mandimitra_token');
  localStorage.removeItem('mandimitra_user');
};

export const logout = logoutUser;
