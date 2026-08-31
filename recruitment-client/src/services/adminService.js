import api from './api';

export const createHRAccount = async (payload) => {
  const response = await api.post('/admin/hr-accounts', payload);
  return response.data;
};

export const getHRAccounts = async (params = {}) => {
  const response = await api.get('/admin/hr-accounts', { params });
  return response.data;
};

export const terminateHRAccount = async (hrId) => {
  const response = await api.patch(`/admin/hr-accounts/${hrId}/terminate`);
  return response.data;
};

export const reactivateHRAccount = async (hrId) => {
  const response = await api.patch(`/admin/hr-accounts/${hrId}/reactivate`);
  return response.data;
};

export const resetHRPassword = async (hrId, payload) => {
  const response = await api.post(`/admin/hr-accounts/${hrId}/reset-password`, payload);
  return response.data;
};

const adminService = {
  createHRAccount,
  getHRAccounts,
  terminateHRAccount,
  reactivateHRAccount,
  resetHRPassword,
};

export default adminService;
