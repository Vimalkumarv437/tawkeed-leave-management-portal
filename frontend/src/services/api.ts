import axios, { AxiosInstance } from 'axios';
import { getCookie, deleteCookie } from '../utils/cookieUtils';

const rawBaseURL = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/+$/, '');
const baseURL = rawBaseURL ? (rawBaseURL.endsWith('/api') ? rawBaseURL : `${rawBaseURL}/api`) : '/api';

const api: AxiosInstance = axios.create({
  baseURL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: read access_token from Cookie and attach Authorization Bearer header
api.interceptors.request.use((config) => {
  const token = getCookie('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle 401 Unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const isLoginRequest = error.config?.url?.includes('/auth/login');
      if (!isLoginRequest) {
        deleteCookie('access_token');
        if (
          window.location.pathname !== '/login' &&
          !window.location.pathname.startsWith('/auth')
        ) {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;






