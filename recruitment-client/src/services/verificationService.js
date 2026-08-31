import api from './api';

const verificationService = {
  getCandidateVerification: async (candidateId, params = {}) => {
    const response = await api.get(`/verification/candidate/${candidateId}`, { params });
    return response.data;
  },

  verifyCandidate: async (candidateId, params = {}) => {
    const response = await api.post(`/verification/candidate/${candidateId}/verify`, null, { params });
    return response.data;
  },

  submitDecision: async (verificationId, decision, notes = '') => {
    const response = await api.post(`/verification/${verificationId}/decision`, { decision, notes });
    return response.data;
  },

  reverify: async (verificationId, params = {}) => {
    const response = await api.post(`/verification/${verificationId}/reverify`, null, { params });
    return response.data;
  }
};

export default verificationService;
