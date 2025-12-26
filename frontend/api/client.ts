import axios, { AxiosError, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios';
import Constants from 'expo-constants';
import { useAuthStore } from '../stores/auth';
import { useOfflineStore } from '../stores/offline';

// Get API URL from environment
const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_API_URL || 'https://chapi.gamificator.click';

// Create Axios instance
export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to inject JWT token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().token;
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and token refresh
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // Handle 401 Unauthorized - token expired
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = useAuthStore.getState().refreshToken;
        
        if (refreshToken) {
          // Attempt to refresh token
          const response = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
            refreshToken,
          });

          const { token } = response.data;
          useAuthStore.getState().updateToken(token);

          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, clear auth and redirect to login
        useAuthStore.getState().clearAuth();
        // TODO: Navigate to login screen
      }
    }

    // Handle network errors (offline)
    if (!error.response) {
      useOfflineStore.getState().setOnlineStatus(false);
      
      // Queue the request for later (if it's a mutation)
      if (originalRequest.method && ['post', 'put', 'patch', 'delete'].includes(originalRequest.method.toLowerCase())) {
        useOfflineStore.getState().addPendingAction({
          type: originalRequest.method === 'delete' ? 'delete' : 'create',
          resource: originalRequest.url || '',
          payload: originalRequest.data,
        });
      }
    } else {
      useOfflineStore.getState().setOnlineStatus(true);
    }

    return Promise.reject(error);
  }
);

export default apiClient;
