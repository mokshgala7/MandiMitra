/**
 * API Abstraction for MandiMitra-ML Price Prediction Service
 * 
 * Fetches: GET /api/v1/prediction?crop={crop}&mandi_id={mandiId}&variety={variety}&grade={grade}
 */
export const getMandiPrediction = async (crop, mandiId, variety = "Other", grade = "FAQ") => {
  try {
    const url = `http://localhost:8000/api/v1/prediction?crop=${crop}&mandi_id=${mandiId}&variety=${variety}&grade=${grade}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "ML prediction service failed");
    }
    
    return await response.json();
  } catch (error) {
    // If backend is down (TypeError: Failed to fetch)
    if (error.message.includes('Failed to fetch')) {
        throw new Error("ML prediction service not connected");
    }
    throw error;
  }
};
