import api from './api';

// Calls FastAPI Google Maps endpoint
export async function getNearbyHospitals(lat, lng, diseaseText = '', radius = 5000) {
  try {
    const params = { lat, lng, radius };
    if (diseaseText && diseaseText.trim()) {
      params.disease_text = diseaseText.trim();
    }

    const response = await api.get('/chat/places/nearby-hospitals', {
      params,
    });

    // Backend already sorts by specialty + rating.
    // Frontend will still slice top‑5 if needed.
    return response.data.places || [];
  } catch (error) {
    console.error('Error fetching hospitals from backend:', error);
    return [];
  }
}
