import api from './api';

const authService = {
  register: async (fullName, email, password, role) => {
    const response = await api.post('/auth/register', { name: fullName, email, password, role });
    return response.data;
  },
  login: async (email, password, role) => {
    const response = await api.post('/auth/login', { email, password, role });
    const data = response.data;

    // FIX: Save the token and user info so the dashboard pages recognize you as logged in
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify({
      id: data.user_id,
      role: data.role,
      name: data.name,
      email: data.email,
    }));

    return data;
  },
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
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
