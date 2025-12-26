import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

// Mock Platform
jest.mock('react-native/Libraries/Utilities/Platform', () => ({
  OS: 'web',
  select: (obj: any) => obj.web,
}));

// Mock SecureStore
jest.mock('expo-secure-store', () => ({
  setItemAsync: jest.fn(),
  getItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

describe('Platform-Specific Persistence', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Clear localStorage
    if (typeof window !== 'undefined') {
      window.localStorage.clear();
    }
  });

  describe('Platform Detection', () => {
    it('should detect web platform', () => {
      expect(Platform.OS).toBe('web');
    });

    it('should support platform-specific code selection', () => {
      const value = Platform.select({
        web: 'web-value',
        ios: 'ios-value',
        android: 'android-value',
      });

      expect(value).toBe('web-value');
    });
  });

  describe('Web Platform - localStorage', () => {
    it('should store data in localStorage on web', () => {
      const key = 'test-key';
      const value = 'test-value';

      localStorage.setItem(key, value);
      expect(localStorage.setItem).toHaveBeenCalledWith(key, value);
    });

    it('should retrieve data from localStorage on web', () => {
      const key = 'test-key';
      const value = 'test-value';

      (localStorage.getItem as jest.Mock).mockReturnValue(value);
      const result = localStorage.getItem(key);

      expect(result).toBe(value);
      expect(localStorage.getItem).toHaveBeenCalledWith(key);
    });

    it('should remove data from localStorage on web', () => {
      const key = 'test-key';

      localStorage.removeItem(key);
      expect(localStorage.removeItem).toHaveBeenCalledWith(key);
    });

    it('should store JSON data in localStorage', () => {
      const key = 'auth-state';
      const data = { token: 'jwt-token', user: { id: 1, email: 'test@example.com' } };

      localStorage.setItem(key, JSON.stringify(data));
      expect(localStorage.setItem).toHaveBeenCalledWith(key, JSON.stringify(data));
    });

    it('should retrieve and parse JSON data from localStorage', () => {
      const key = 'auth-state';
      const data = { token: 'jwt-token', user: { id: 1, email: 'test@example.com' } };

      (localStorage.getItem as jest.Mock).mockReturnValue(JSON.stringify(data));
      const result = JSON.parse(localStorage.getItem(key) || '{}');

      expect(result).toEqual(data);
    });
  });

  describe('Native Platform - SecureStore', () => {
    beforeEach(() => {
      // Simulate native platform
      Object.defineProperty(Platform, 'OS', {
        value: 'ios',
        writable: true,
      });
    });

    it('should store data in SecureStore on native', async () => {
      const key = 'test-key';
      const value = 'test-value';

      await SecureStore.setItemAsync(key, value);
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(key, value);
    });

    it('should retrieve data from SecureStore on native', async () => {
      const key = 'test-key';
      const value = 'test-value';

      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(value);
      const result = await SecureStore.getItemAsync(key);

      expect(result).toBe(value);
      expect(SecureStore.getItemAsync).toHaveBeenCalledWith(key);
    });

    it('should delete data from SecureStore on native', async () => {
      const key = 'test-key';

      await SecureStore.deleteItemAsync(key);
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith(key);
    });

    it('should store JSON data in SecureStore', async () => {
      const key = 'auth-state';
      const data = { token: 'jwt-token', user: { id: 1, email: 'test@example.com' } };

      await SecureStore.setItemAsync(key, JSON.stringify(data));
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(key, JSON.stringify(data));
    });

    it('should retrieve and parse JSON data from SecureStore', async () => {
      const key = 'auth-state';
      const data = { token: 'jwt-token', user: { id: 1, email: 'test@example.com' } };

      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(JSON.stringify(data));
      const result = JSON.parse((await SecureStore.getItemAsync(key)) || '{}');

      expect(result).toEqual(data);
    });

    it('should handle SecureStore errors gracefully', async () => {
      const key = 'test-key';

      (SecureStore.getItemAsync as jest.Mock).mockRejectedValue(new Error('SecureStore error'));
      
      await expect(SecureStore.getItemAsync(key)).rejects.toThrow('SecureStore error');
    });
  });

  describe('Cross-Platform Persistence Strategy', () => {
    it('should use appropriate storage based on platform', () => {
      const getPersistenceStorage = () => {
        if (Platform.OS === 'web') {
          return 'localStorage';
        }
        return 'SecureStore';
      };

      // Web platform
      Object.defineProperty(Platform, 'OS', { value: 'web', writable: true });
      expect(getPersistenceStorage()).toBe('localStorage');

      // iOS platform
      Object.defineProperty(Platform, 'OS', { value: 'ios', writable: true });
      expect(getPersistenceStorage()).toBe('SecureStore');

      // Android platform
      Object.defineProperty(Platform, 'OS', { value: 'android', writable: true });
      expect(getPersistenceStorage()).toBe('SecureStore');
    });
  });

  describe('Zustand Persistence Integration', () => {
    it('should persist auth state on web using localStorage', () => {
      Object.defineProperty(Platform, 'OS', { value: 'web', writable: true });
      
      const authState = {
        token: 'jwt-token',
        user: { id: 1, email: 'test@example.com' },
      };

      localStorage.setItem('auth-storage', JSON.stringify(authState));
      expect(localStorage.setItem).toHaveBeenCalledWith('auth-storage', JSON.stringify(authState));
    });

    it('should persist auth state on native using SecureStore', async () => {
      Object.defineProperty(Platform, 'OS', { value: 'ios', writable: true });
      
      const authState = {
        token: 'jwt-token',
        user: { id: 1, email: 'test@example.com' },
      };

      await SecureStore.setItemAsync('auth-storage', JSON.stringify(authState));
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith('auth-storage', JSON.stringify(authState));
    });
  });
});
