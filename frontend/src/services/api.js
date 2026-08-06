import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'https://kspdb-backend1.onrender.com'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const telemetryAPI = {
  ingest: (data) => api.post('/api/telemetry/', data),
  getPole: (poleId) => api.get(`/api/telemetry/pole/${poleId}`),
  getDevice: (deviceId) => api.get(`/api/telemetry/device/${deviceId}`),
}

export const polesAPI = {
  getAll: (params) => api.get('/api/poles/', { params }),
  getById: (poleId) => api.get(`/api/poles/${poleId}`),
  getByDT: (dtId) => api.get(`/api/poles/dt/${dtId}`),
  getByFeeder: (feederId) => api.get(`/api/poles/feeder/${feederId}`),
  getTransformers: () => api.get('/api/poles/transformers/all'),
  getTransformer: (dtId) => api.get(`/api/poles/transformers/${dtId}`),
}

export const ticketsAPI = {
  getAll: (params) => api.get('/api/tickets/', { params }),
  getById: (ticketId) => api.get(`/api/tickets/${ticketId}`),
  update: (ticketId, data) => api.put(`/api/tickets/${ticketId}`, data),
}

export const simulatorAPI = {
  injectFault: (data) => api.post('/api/simulator/inject-fault', data),
  injectNoise: (data) => api.post('/api/simulator/inject-noise', data),
  repairFault: (faultId) => api.post('/api/simulator/repair-fault', null, { params: { fault_id: faultId } }),
  generateNetwork: (params) => api.post('/api/simulator/generate-network', null, { params }),
  reset: () => api.post('/api/simulator/reset'),
}

export const scheduledOutagesAPI = {
  get: (params) => api.get('/api/scheduled-outages/', { params }),
  seed: () => api.post('/api/scheduled-outages/seed'),
}

export default api
