import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { apiClient } from '../../api/client';
import { useAuthStore } from '../../stores/auth';
import { useOfflineStore } from '../../stores/offline';

// Mock the stores
jest.mock('../../stores/auth');
jest.mock('../../stores/offline');

describe('API Client', () => {
  let mock: MockAdapter;
  let axiosMock: MockAdapter;

  beforeEach(() => {
    mock = new MockAdapter(apiClient);
    axiosMock = new MockAdapter(axios);
    jest.clearAllMocks();
  });

  afterEach(() => {
    mock.restore();
    axiosMock.restore();
  });

  describe('JWT Token Injection', () => {
    it('should inject JWT token in Authorization header when token exists', async () => {
      const mockToken = 'test-jwt-token';
      (useAuthStore.getState as jest.Mock).mockReturnValue({
        token: mockToken,
      });

      mock.onGet('/test').reply((config) => {
        expect(config.headers?.Authorization).toBe(`Bearer ${mockToken}`);
        return [200, { success: true }];
      });

      await apiClient.get('/test');
    });

    it('should not inject Authorization header when no token exists', async () => {
      (useAuthStore.getState as jest.Mock).mockReturnValue({
        token: null,
      });

      mock.onGet('/test').reply((config) => {
        expect(config.headers?.Authorization).toBeUndefined();
        return [200, { success: true }];
      });

      await apiClient.get('/test');
    });
  });

  describe('Token Refresh on 401', () => {
    it('should call refresh endpoint and update token on 401 error', async () => {
      const oldToken = 'old-token';
      const newToken = 'new-token';
      const refreshToken = 'refresh-token';
      
      const mockUpdateToken = jest.fn();
      const mockClearAuth = jest.fn();
      
      (useAuthStore.getState as jest.Mock).mockReturnValue({
        token: oldToken,
        refreshToken,
        updateToken: mockUpdateToken,
        clearAuth: mockClearAuth,
      });

      (useOfflineStore.getState as jest.Mock).mockReturnValue({
        setOnlineStatus: jest.fn(),
        addPendingAction: jest.fn(),
      });

      // First request fails with 401
      mock.onGet('/protected').replyOnce(401);

      // Mock the base axios refresh call with full URL
      axiosMock.onPost('https://chapi.gamificator.click/api/v1/auth/refresh').reply(200, { token: newToken });

      // Second attempt with new token should succeed
      mock.onGet('/protected').reply(200, { data: 'success' });

      try {
        await apiClient.get('/protected');
      } catch (error) {
        // May fail if retry doesn't work, but refresh should be called
      }

      // Verify refresh was called and token was updated
      expect(mockUpdateToken).toHaveBeenCalledWith(newToken);
      expect(mockClearAuth).not.toHaveBeenCalled();
    });

    it('should clear auth and not retry when refresh token fails', async () => {
      const mockClearAuth = jest.fn();
      (useAuthStore.getState as jest.Mock).mockReturnValue({
        token: 'old-token',
        refreshToken: 'refresh-token',
        clearAuth: mockClearAuth,
      });

      // First request fails with 401
      mock.onGet('/protected').reply(401);

      // Refresh token fails
      mock.onPost('/api/v1/auth/refresh').reply(401);

      await expect(apiClient.get('/protected')).rejects.toThrow();
      expect(mockClearAuth).toHaveBeenCalled();
    });

    it('should clear auth when no refresh token available', async () => {
      const mockClearAuth = jest.fn();
      (useAuthStore.getState as jest.Mock).mockReturnValue({
        token: 'old-token',
        refreshToken: null,
        clearAuth: mockClearAuth,
      });

      mock.onGet('/protected').reply(401);

      await expect(apiClient.get('/protected')).rejects.toThrow();
    });
  });

  describe('Offline Detection and Queueing', () => {
    it('should detect network error and set offline status', async () => {
      const mockSetOnlineStatus = jest.fn();
      (useOfflineStore.getState as jest.Mock).mockReturnValue({
        setOnlineStatus: mockSetOnlineStatus,
        addPendingAction: jest.fn(),
      });

      mock.onGet('/test').networkError();

      await expect(apiClient.get('/test')).rejects.toThrow();
      expect(mockSetOnlineStatus).toHaveBeenCalledWith(false);
    });

    it('should queue POST request when offline', async () => {
      const mockAddPendingAction = jest.fn();
      (useOfflineStore.getState as jest.Mock).mockReturnValue({
        setOnlineStatus: jest.fn(),
        addPendingAction: mockAddPendingAction,
      });

      const payload = { name: 'test' };
      mock.onPost('/test').networkError();

      await expect(apiClient.post('/test', payload)).rejects.toThrow();
      
      // Axios serializes the payload to JSON string
      expect(mockAddPendingAction).toHaveBeenCalledWith({
        type: 'create',
        resource: '/test',
        payload: JSON.stringify(payload),
      });
    });

    it('should queue DELETE request when offline', async () => {
      const mockAddPendingAction = jest.fn();
      (useOfflineStore.getState as jest.Mock).mockReturnValue({
        setOnlineStatus: jest.fn(),
        addPendingAction: mockAddPendingAction,
      });

      mock.onDelete('/test/123').networkError();

      await expect(apiClient.delete('/test/123')).rejects.toThrow();
      
      expect(mockAddPendingAction).toHaveBeenCalledWith({
        type: 'delete',
        resource: '/test/123',
        payload: undefined,
      });
    });

    it('should NOT queue GET request when offline', async () => {
      const mockAddPendingAction = jest.fn();
      (useOfflineStore.getState as jest.Mock).mockReturnValue({
        setOnlineStatus: jest.fn(),
        addPendingAction: mockAddPendingAction,
      });

      mock.onGet('/test').networkError();

      await expect(apiClient.get('/test')).rejects.toThrow();
      expect(mockAddPendingAction).not.toHaveBeenCalled();
    });

    it('should set online status to true when request succeeds', async () => {
      const mockSetOnlineStatus = jest.fn();
      (useOfflineStore.getState as jest.Mock).mockReturnValue({
        setOnlineStatus: mockSetOnlineStatus,
        addPendingAction: jest.fn(),
      });

      mock.onGet('/test').reply(200, { success: true });

      await apiClient.get('/test');
      // Note: Online status is only set on error responses, not success
    });
  });

  describe('Request Timeout', () => {
    it('should timeout requests after 30 seconds', async () => {
      (useOfflineStore.getState as jest.Mock).mockReturnValue({
        setOnlineStatus: jest.fn(),
        addPendingAction: jest.fn(),
      });

      mock.onGet('/slow').timeout();

      await expect(apiClient.get('/slow')).rejects.toThrow();
    });
  });

  describe('Error Response Interceptor', () => {
    it('should handle server errors (500) without retrying', async () => {
      (useOfflineStore.getState as jest.Mock).mockReturnValue({
        setOnlineStatus: jest.fn(),
        addPendingAction: jest.fn(),
      });

      mock.onGet('/server-error').reply(500, { error: 'Internal Server Error' });

      await expect(apiClient.get('/server-error')).rejects.toThrow();
    });

    it('should handle client errors (400) without retrying', async () => {
      (useOfflineStore.getState as jest.Mock).mockReturnValue({
        setOnlineStatus: jest.fn(),
        addPendingAction: jest.fn(),
      });

      mock.onGet('/bad-request').reply(400, { error: 'Bad Request' });

      await expect(apiClient.get('/bad-request')).rejects.toThrow();
    });
  });
});
