import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

interface User {
  id: string;
  email: string;
  name?: string;
}

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;

  // Actions
  setToken: (token: string, refreshToken?: string) => void;
  setUser: (user: User) => void;
  clearAuth: () => void;
  updateToken: (token: string) => void;
}

// Platform-specific storage
const storage = Platform.select({
  web: createJSONStorage(() => localStorage),
  default: {
    getItem: async (name: string) => {
      return await SecureStore.getItemAsync(name);
    },
    setItem: async (name: string, value: string) => {
      await SecureStore.setItemAsync(name, value);
    },
    removeItem: async (name: string) => {
      await SecureStore.deleteItemAsync(name);
    },
  },
});

export const useAuthStore = create<AuthState>()(persist(
  (set) => ({
    token: null,
    refreshToken: null,
    user: null,
    isAuthenticated: false,

    setToken: (token: string, refreshToken?: string) => {
      set({
        token,
        refreshToken: refreshToken || null,
        isAuthenticated: true,
      });
    },

    setUser: (user: User) => {
      set({ user });
    },

    clearAuth: () => {
      set({
        token: null,
        refreshToken: null,
        user: null,
        isAuthenticated: false,
      });
    },

    updateToken: (token: string) => {
      set({ token });
    },
  }),
  {
    name: 'auth-storage',
    storage,
  }
));
