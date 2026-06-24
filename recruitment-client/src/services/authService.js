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
  getCurrentUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },
  isAuthenticated: () => {
    return !!localStorage.getItem('token');
  }
};

export default authService;