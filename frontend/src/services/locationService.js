/**
 * Retrieve the user's real geographic location via browser Geolocation API.
 * Returns a Promise that resolves with { latitude, longitude } or rejects with an error message.
 */
export const getUserLocation = () => {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject("Geolocation is not supported by your browser.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        });
      },
      (error) => {
        let errorMsg = "Unable to retrieve your location.";
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMsg = "Location access is required to find mandis near you. Please allow location access in your browser.";
            break;
          case error.POSITION_UNAVAILABLE:
            errorMsg = "Location information is unavailable right now.";
            break;
          case error.TIMEOUT:
            errorMsg = "The request to get your location timed out.";
            break;
        }
        reject(errorMsg);
      },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 0
      }
    );
  });
};
