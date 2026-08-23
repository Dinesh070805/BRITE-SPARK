import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getHealth = () => api.get('/health');
export const getDashboard = () => api.get('/dashboard');
export const getAppointments = (params) => api.get('/appointments', { params });
export const getAppointmentById = (id) => api.get(`/appointments/${id}`);
export const getResidents = (params) => api.get('/residents', { params });
export const getResidentById = (id) => api.get(`/residents/${id}`);
export const getReminders = (params) => api.get('/reminders', { params });
export const getReminderById = (id) => api.get(`/reminders/${id}`);
export const runReminderEngine = () => api.post('/reminders/run');
export const retryReminder = (id) => api.post(`/reminders/${id}/retry`);
export const getAuditLogs = (params) => api.get('/audit-logs', { params });
export const getMetrics = () => api.get('/metrics');
export const getPolicies = () => api.get('/policies');
export const updatePolicies = (data) => api.put('/policies', data);

export default api;
