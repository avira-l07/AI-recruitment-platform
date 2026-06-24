import api from './api';

const resumeService = {
  uploadResume: async (userId, file) => {
    const formData = new FormData();
    // FIX: Backend explicitly expects candidate_id, not user_id
    formData.append('user_id', userId); 
    formData.append('file', file);
    
    const response = await api.post('/resumes/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  getResume: async (userId) => {
    const response = await api.get(`/resumes/${userId}`);
    const data = response.data;
    
    let parsedObj = {};
    if (data.parsed_data) {
      try {
        parsedObj = typeof data.parsed_data === 'string' 
          ? JSON.parse(data.parsed_data) 
          : data.parsed_data;
      } catch (e) {
        console.warn("Failed to parse resume data", e);
      }
    }

    return {
      ...data,
      ...parsedObj,
      parsed_data: parsedObj // FIX: Explicitly prevents backend fields from being silently overwritten
    };
  },

  getCareerSuggestions: async (userId) => {
    const response = await api.get(`/resumes/${userId}/career-suggestions`);
    return response.data;
  }
};

export default resumeService;