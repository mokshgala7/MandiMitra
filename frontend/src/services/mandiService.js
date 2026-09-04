/**
 * API Abstraction for MandiMitra 500 KM Geographic Search
 * 
 * Fetches: GET /api/v1/mandis/nearby?crop={crop}&latitude={lat}&longitude={lng}&radius_km=500
 */
export const getNearbyMandis = async ({ crop, latitude, longitude, radiusKm = 500 }) => {
  try {
    const url = `http://localhost:8000/api/v1/mandis/nearby?crop=${crop}&latitude=${latitude}&longitude=${longitude}&radius_km=${radiusKm}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to search nearby mandis");
    }
    
    return await response.json();
  } catch (error) {
    // If backend is down (TypeError: Failed to fetch)
    if (error.message.includes('Failed to fetch')) {
        throw new Error("Backend API not connected");
    }
    throw error;
  }
};
