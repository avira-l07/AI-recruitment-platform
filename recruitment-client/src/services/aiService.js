import api from './api';

const aiService = {
  getStatus: async () => {
    const response = await api.get('/ai/status');
    return response.data;
  },
  getActivity: async (page = 1, pageSize = 20) => {
    const response = await api.get('/ai/activity', { params: { page, page_size: pageSize } });
    return response.data;
  },
  askRecruiter: async (message, conversationId = null) => {
    const response = await api.post('/ai/recruiter', {
      message,
      conversation_id: conversationId,
    });
    return response.data;
  },
};

export default aiService;
