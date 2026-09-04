const API_BASE = 'http://localhost:8000/api/v1';

export const getSellingRecommendation = async (params) => {
  const resp = await fetch(`${API_BASE}/recommendation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to calculate selling recommendation');
  }
  return await resp.json();
};
