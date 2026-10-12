import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;

    try {
      const userStr = localStorage.getItem('user');
      const user = userStr ? JSON.parse(userStr) : null;
      if (user && user.role === 'hr') {
        const isBlind = localStorage.getItem(`blind_screening_hr_${user.id}`) === 'true';
        if (isBlind) {
          const url = config.url || '';
          const isHrCandidateRoute = (
            url.includes('/applications/hr/me') ||
            url.includes('/applications/') ||
            url.includes('/matching/all') ||
            url.includes('/matching/candidate/') ||
            url.includes('/matching/job/') ||
            url.includes('/candidates') ||
            url.includes('/resumes/') ||
            url.includes('/search') ||
            url.includes('/ai/recruiter') ||
            url.includes('/verification') ||
            url.includes('/prescreening') ||
            url.includes('/analytics/events') ||
            url.includes('/notifications')
          );
          const isExcluded = url.includes('/resumes/upload') || url.includes('/resumes/me/download') || url.includes('/auth/');
          if (isHrCandidateRoute && !isExcluded) {
            config.headers['X-Blind-Screening'] = 'true';
          }
        }
      }
    } catch {}

    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const isLoginRequest = error.config?.url?.includes('/auth/login');
      if (!isLoginRequest && window.location.pathname !== '/login') {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
