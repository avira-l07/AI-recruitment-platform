import api from './api';

const authService = {
  register: async (fullName, email, password) => {
    const response = await api.post('/auth/register', { name: fullName, email, password });
    return response.data;
  },
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    const data = response.data;

    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify({
      id: data.id || data.user_id,
      role: data.role,
      name: data.full_name || data.name,
      email: data.email,
      is_active: data.is_active,
      must_change_password: data.must_change_password,
    }));
    window.dispatchEvent(new Event('auth-changed'));

    return data;
  },
  changePassword: async (current_password, new_password, confirm_new_password) => {
    const response = await api.post('/auth/change-password', {
      current_password,
      new_password,
      confirm_new_password,
    });
    const data = response.data;

    if (data.access_token) {
      localStorage.setItem('token', data.access_token);
    }
    if (data.user) {
      localStorage.setItem('user', JSON.stringify({
        id: data.user.id,
        role: data.user.role,
        name: data.user.full_name || data.user.name,
        email: data.user.email,
        is_active: data.user.is_active,
        must_change_password: data.user.must_change_password,
      }));
    }
    window.dispatchEvent(new Event('auth-changed'));
    return data;
  },
  fetchMe: async () => {
    const response = await api.get('/auth/me');
    const data = response.data;
    localStorage.setItem('user', JSON.stringify({ ...data, name: data.full_name || data.name }));
    window.dispatchEvent(new Event('auth-changed'));
    return data;
  },
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.dispatchEvent(new Event('auth-changed'));
  },
  isTokenExpired: (token) => {
    if (!token) return true;
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return true;
      const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
      if (!payload.exp) return false;
      return payload.exp * 1000 < Date.now();
    } catch (e) {
      return true;
    }
  },
  getCurrentUser: () => {
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');
    if (!token || !userStr) return null;
    if (authService.isTokenExpired(token)) {
      authService.logout();
      return null;
    }
    try {
      return JSON.parse(userStr);
    } catch (e) {
      return null;
    }
  },
  getToken: () => {
    return localStorage.getItem('token');
  },
  isAuthenticated: () => {
    return !!localStorage.getItem('token');
  }
};

export default authService;
