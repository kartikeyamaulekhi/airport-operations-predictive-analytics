import axios from 'axios';

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8080';

const client = axios.create({ baseURL: BASE, timeout: 35000 });

client.interceptors.response.use(
  r => r,
  err => {
    const msg = err.response?.data?.message || err.message || 'Request failed';
    return Promise.reject(new Error(msg));
  }
);

export const api = {
  health:          () => client.get('/api/health'),
  dashboardSummary:() => client.get('/api/dashboard/summary'),
  history:         () => client.get('/api/history'),
  alerts:          () => client.get('/api/history/alerts'),
  forecast:        (days=30) => client.get(`/api/forecast/traffic?days=${days}`),
  predict:         (payload) => client.post('/api/predict/delay', payload),
};
