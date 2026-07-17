import api from './api';

const analyticsService = {
  getOverview: async () => {
    const response = await api.get('/analytics/overview');
    return response.data;
  },

  getAiStatus: async () => {
    const response = await api.get('/analytics/ai-status');
    return response.data;
  },

  getEvents: async (limit = 50) => {
    const response = await api.get(`/analytics/events?limit=${limit}`);
    return response.data;
  }
};

export default analyticsService;
