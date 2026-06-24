import api from './api';

const jobService = {
  createJob: async (jobData, createdBy) => {
    const payload = {
      title: jobData.title,
      description: jobData.description,
      required_skills: Array.isArray(jobData.requiredSkills)
        ? jobData.requiredSkills.join(', ')
        : jobData.requiredSkills,
      experience_level: jobData.experienceLevel,
      education_requirement: jobData.educationRequirement,
    };
    const response = await api.post('/jobs', payload, { params: { created_by: createdBy } });
    return response.data;
  },
  getAllJobs: async (activeOnly = false) => {
    const response = await api.get('/jobs', { params: { active_only: activeOnly } });
    return response.data;
  },
  getJobById: async (jobId) => {
    const response = await api.get(`/jobs/${jobId}`);
    return response.data;
  },
  closeJob: async (jobId, reason) => {
    const response = await api.put(`/jobs/${jobId}/close`, { reason });
    return response.data;
  },
  reopenJob: async (jobId) => {
    const response = await api.put(`/jobs/${jobId}/reopen`);
    return response.data;
  },
  getRecommendedJobs: async (userId) => {
    const response = await api.get(`/jobs/recommended/${userId}`);
    return response.data;
  }
};

export default jobService;