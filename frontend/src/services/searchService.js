const API_BASE = 'http://localhost:8000/api/v1';

export const getRecentSearches = async () => {
  const token = localStorage.getItem('mandimitra_token');
  const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
  try {
    const resp = await fetch(`${API_BASE}/search-history`, { headers });
    if (!resp.ok) return [];
    return await resp.json();
  } catch (err) {
    console.warn('Search history warning:', err);
    return [];
  }
};

export const saveSearchHistory = async (searchData) => {
  const token = localStorage.getItem('mandimitra_token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  try {
    const resp = await fetch(`${API_BASE}/search-history`, {
      method: 'POST',
      headers,
      body: JSON.stringify(searchData)
    });
    if (!resp.ok) return null;
    return await resp.json();
  } catch (err) {
    console.warn('Save search warning:', err);
    return null;
  }
};
