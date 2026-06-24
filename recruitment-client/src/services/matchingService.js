import api from './api';

const matchingService = {
  getAllMatches: async () => {
    const response = await api.get('/matching/all');
    return response.data;
  },

  getCandidateMatches: async (userId) => {
    const response = await api.get(`/matching/candidate/${userId}`);
    return response.data;
  },

  getJobMatches: async (jobId) => {
    const response = await api.get(`/matching/job/${jobId}`);
    return response.data;
  },

  updateMatchStatus: async (matchId, status) => {
    const response = await api.put(`/matching/${matchId}/status`, { status });
    return response.data;
  },

  applyToJob: async (userId, jobId) => {
    const response = await api.post('/matching/apply', { user_id: userId, job_id: jobId });
    return response.data;
  }
};

export default matchingService;