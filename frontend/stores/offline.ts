import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { Platform } from 'react-native';

export interface PendingAction {
  id: string;
  type: 'create' | 'update' | 'delete';
  resource: string;
  payload: any;
  timestamp: Date;
  retries: number;
}

interface OfflineState {
  isOnline: boolean;
  pendingActions: PendingAction[];
  lastSyncTime: Date | null;

  // Actions
  addPendingAction: (action: Omit<PendingAction, 'id' | 'timestamp' | 'retries'>) => void;
  removePendingAction: (id: string) => void;
  setOnlineStatus: (status: boolean) => void;
  updateLastSync: () => void;
  incrementRetries: (id: string) => void;
  clearPendingActions: () => void;
}

// Platform-specific storage (localStorage for web, AsyncStorage for native)
const storage = Platform.select({
  web: createJSONStorage(() => localStorage),
  default: createJSONStorage(() => {
    // For native, we'll use AsyncStorage (to be installed later)
    // For now, fallback to localStorage
    return localStorage;
  }),
});

export const useOfflineStore = create<OfflineState>()(persist(
  (set, get) => ({
    isOnline: true,
    pendingActions: [],
    lastSyncTime: null,

    addPendingAction: (action) => {
      const newAction: PendingAction = {
        ...action,
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date(),
        retries: 0,
      };
      set((state) => ({
        pendingActions: [...state.pendingActions, newAction],
      }));
    },

    removePendingAction: (id) => {
      set((state) => ({
        pendingActions: state.pendingActions.filter((action) => action.id !== id),
      }));
    },

    setOnlineStatus: (status) => {
      set({ isOnline: status });
    },

    updateLastSync: () => {
      set({ lastSyncTime: new Date() });
    },

    incrementRetries: (id) => {
      set((state) => ({
        pendingActions: state.pendingActions.map((action) =>
          action.id === id ? { ...action, retries: action.retries + 1 } : action
        ),
      }));
    },

    clearPendingActions: () => {
      set({ pendingActions: [] });
    },
  }),
  {
    name: 'offline-storage',
    storage,
  }
));
