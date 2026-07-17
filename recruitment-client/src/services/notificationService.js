import api from './api';

const notificationService = {
  getNotifications: async (unreadOnly = false) => {
    const response = await api.get('/notifications', { params: { unread_only: unreadOnly } });
    return response.data;
  },
  markRead: async (id) => {
    const response = await api.put(`/notifications/${id}/read`);
    return response.data;
  },
  markAllRead: async () => {
    const response = await api.put('/notifications/read-all');
    return response.data;
  },
};

export default notificationService;
