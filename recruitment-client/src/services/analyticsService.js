import api from './api';

const analyticsService = {
  getOverview: async () => {
    const response = await api.get('/analytics/overview');
    return response.data;
  }
};

export default analyticsService;