import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('fraud_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('fraud_token');
      localStorage.removeItem('fraud_user');
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (credentials) => api.post('/auth/login', credentials).then((res) => res.data),
  me: () => api.get('/auth/me').then((res) => res.data),
};

export const dashboardApi = {
  summary: () => api.get('/dashboard/summary').then((res) => res.data),
  stats: () => api.get('/dashboard/stats').then((res) => res.data),
  riskDistribution: () => api.get('/dashboard/risk-distribution').then((res) => res.data),
};

export const transactionsApi = {
  list: (params = {}) => api.get('/transactions/', { params }).then((res) => res.data),
  reference: () => api.get('/transactions/reference').then((res) => res.data),
  get: (id) => api.get(`/transactions/${id}`).then((res) => res.data),
  create: (payload) => api.post('/transactions/', payload).then((res) => res.data),
};

export const fraudApi = {
  alerts: (params = {}) => api.get('/fraud/alerts', { params }).then((res) => res.data),
  updateAlert: (id, payload) => api.patch(`/fraud/alerts/${id}`, payload).then((res) => res.data),
  riskScores: (params = {}) => api.get('/fraud/risk-scores', { params }).then((res) => res.data),
  analyze: (id) => api.post(`/fraud/analyze/${id}`).then((res) => res.data),
};

export const graphApi = {
  network: (params = {}) => api.get('/graph/network', { params }).then((res) => res.data),
  metrics: () => api.get('/graph/metrics').then((res) => res.data),
  customer: (id, params = {}) => api.get(`/graph/customer/${id}`, { params }).then((res) => res.data),
};

export const investigationApi = {
  cases: (params = {}) => api.get('/investigation/cases', { params }).then((res) => res.data),
  updateStatus: (id, payload) => api.patch(`/investigation/cases/${id}/status`, payload).then((res) => res.data),
  addNote: (payload) => api.post('/investigation/notes', payload).then((res) => res.data),
};

export default api;
