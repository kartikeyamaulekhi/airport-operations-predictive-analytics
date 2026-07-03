import axios from 'axios';

const API_BASE_URL = 'http://localhost:8080';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const airportService = {
  // -- Delay Prediction Engine --
  getDelayPrediction: async (data) => {
    const response = await apiClient.post('/api/predict/delay', data);
    return response.data;
  },

  // -- Traffic Forecasting Engine --
  getTrafficForecast: async (days = 30) => {
    const response = await apiClient.get(`/api/forecast/traffic?days=${days}`);
    return response.data;
  },

  // -- Dashboard Metrics & Telemetry Summary --
  getDashboardSummary: async () => {
    const response = await apiClient.get('/api/dashboard/summary');
    return response.data;
  },
};

export default apiClient;
