import api from './api';

const prescreeningService = {
  getJobQuestions: async (jobId) => {
    const response = await api.get(`/prescreening/job/${jobId}/questions`);
    return response.data;
  },

  generateQuestions: async (jobId, saveToJob = true) => {
    const response = await api.post(`/prescreening/job/${jobId}/generate`, null, {
      params: { save_to_job: saveToJob }
    });
    return response.data;
  },

  updateJobQuestions: async (jobId, questions) => {
    const response = await api.put(`/prescreening/job/${jobId}/questions`, { questions });
    return response.data;
  },

  getApplicationEvaluation: async (applicationId, params = {}) => {
    const response = await api.get(`/prescreening/application/${applicationId}`, { params });
    return response.data;
  }
};

export default prescreeningService;
