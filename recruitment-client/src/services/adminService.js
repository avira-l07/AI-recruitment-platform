import api from './api';

export const createHRAccount = async (payload) => {
  const response = await api.post('/admin/hr-accounts', payload);
  return response.data;
};

export const getHRAccounts = async (params = {}) => {
  const response = await api.get('/admin/hr-accounts', { params });
  return response.data;
};

export const updateHRAccountStatus = async (hrId, isActive) => {
  const response = await api.patch(`/admin/hr-accounts/${hrId}/status`, { is_active: isActive });
  return response.data;
};

export const resetHRPassword = async (hrId, payload) => {
  const response = await api.post(`/admin/hr-accounts/${hrId}/reset-password`, payload);
  return response.data;
};

const adminService = {
  createHRAccount,
  getHRAccounts,
  updateHRAccountStatus,
  resetHRPassword,
};

export default adminService;
