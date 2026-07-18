import api from './api';

const buildUploadError = (err) => {
  const detail = err.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail?.message) {
    const reasons = detail.quality?.reasons || [];
    const tips = detail.quality?.tips || [];
    return [detail.message, ...reasons, ...tips.map(t => `Tip: ${t}`)].join('\n');
  }
  return err.message || 'Failed to upload resume. Please try again.';
};

const resumeService = {
  uploadResume: async (userId, file) => {
    if (!userId) throw new Error('User ID is missing. Please logout and login again.');
    if (!file) throw new Error('Resume file is missing.');
    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('file', file);
    try {
      const response = await api.post('/resumes/upload', formData);
      return response.data;
    } catch (err) {
      throw new Error(buildUploadError(err));
    }
  },

  getResume: async (userId, config = {}) => {
    const response = await api.get(`/resumes/${userId}`, config);
    const data = response.data;
    const parsedObj = typeof data.parsed_data === 'string' ? JSON.parse(data.parsed_data || '{}') : (data.parsed_data || {});
    return { ...data, ...parsedObj, parsed_data: parsedObj };
  },

  getCareerSuggestions: async (userId) => {
    const response = await api.get(`/resumes/${userId}/career-suggestions`);
    return response.data;
  },

  generateCareerSuggestions: async (userId, force = false) => {
    const response = await api.post(`/resumes/${userId}/career-suggestions/generate?force=${force}`);
    return response.data;
  },

  getResumeIntelligence: async (userId) => {
    const response = await api.get(`/resumes/${userId}/intelligence`);
    return response.data;
  },

  getResumeFile: async (userId, config = {}) => {
    const response = await api.get(`/resumes/${userId}/download`, {
      responseType: 'blob',
      ...config
    });
    return {
      blob: response.data,
      contentType: response.headers['content-type'] || response.headers['Content-Type'],
      contentDisposition: response.headers['content-disposition'] || response.headers['Content-Disposition']
    };
  },

  getApplicationResume: async (applicationId, config = {}) => {
    const response = await api.get(`/applications/${applicationId}/resume`, {
      responseType: 'blob',
      ...config
    });
    return {
      blob: response.data,
      contentType: response.headers['content-type'] || response.headers['Content-Type'],
      contentDisposition: response.headers['content-disposition'] || response.headers['Content-Disposition']
    };
  },

  getMyResumeFile: async (config = {}) => {
    const response = await api.get(`/resumes/me/download`, {
      responseType: 'blob',
      ...config
    });
    return {
      blob: response.data,
      contentType: response.headers['content-type'] || response.headers['Content-Type'],
      contentDisposition: response.headers['content-disposition'] || response.headers['Content-Disposition']
    };
  },

  getAIStatus: async () => {
    const response = await api.get('/analytics/ai-status');
    return response.data;
  },
};

export default resumeService;
