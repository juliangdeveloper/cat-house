import { useAuthStore } from '../../stores/auth';

describe('Auth Store', () => {
  beforeEach(() => {
    // Reset store state before each test
    useAuthStore.setState({
      token: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
    });
  });

  it('should initialize with default state', () => {
    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.refreshToken).toBeNull();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('should set token and mark as authenticated', () => {
    const { setToken } = useAuthStore.getState();
    
    setToken('test-token', 'test-refresh-token');
    
    const state = useAuthStore.getState();
    expect(state.token).toBe('test-token');
    expect(state.refreshToken).toBe('test-refresh-token');
    expect(state.isAuthenticated).toBe(true);
  });

  it('should set user information', () => {
    const { setUser } = useAuthStore.getState();
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      name: 'Test User',
    };
    
    setUser(mockUser);
    
    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
  });

  it('should clear all auth data', () => {
    const { setToken, setUser, clearAuth } = useAuthStore.getState();
    
    // Set some data
    setToken('test-token', 'test-refresh-token');
    setUser({
      id: '123',
      email: 'test@example.com',
    });
    
    // Clear auth
    clearAuth();
    
    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.refreshToken).toBeNull();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('should update token without affecting refresh token', () => {
    const { setToken, updateToken } = useAuthStore.getState();
    
    setToken('original-token', 'original-refresh-token');
    updateToken('new-token');
    
    const state = useAuthStore.getState();
    expect(state.token).toBe('new-token');
    expect(state.refreshToken).toBe('original-refresh-token');
  });
});
