const API_BASE = 'http://localhost:8000/api/v1';

export const getLocalWeather = async (latitude, longitude, locationName = 'Your Farm') => {
  try {
    const url = `${API_BASE}/weather?latitude=${latitude}&longitude=${longitude}&location_name=${encodeURIComponent(locationName)}`;
    const resp = await fetch(url);
    if (!resp.ok) return null;
    return await resp.json();
  } catch (error) {
    console.warn('Weather service warning:', error);
    return null;
  }
};
