import { useOfflineStore } from '../../stores/offline';

describe('Offline Store', () => {
  beforeEach(() => {
    // Reset store state before each test
    useOfflineStore.setState({
      isOnline: true,
      pendingActions: [],
      lastSyncTime: null,
    });
  });

  it('should initialize with default state', () => {
    const state = useOfflineStore.getState();
    expect(state.isOnline).toBe(true);
    expect(state.pendingActions).toEqual([]);
    expect(state.lastSyncTime).toBeNull();
  });

  it('should add pending action', () => {
    const { addPendingAction } = useOfflineStore.getState();
    
    addPendingAction({
      type: 'create',
      resource: '/api/v1/cats',
      payload: { name: 'Test Cat' },
    });
    
    const state = useOfflineStore.getState();
    expect(state.pendingActions).toHaveLength(1);
    expect(state.pendingActions[0].type).toBe('create');
    expect(state.pendingActions[0].resource).toBe('/api/v1/cats');
    expect(state.pendingActions[0].retries).toBe(0);
  });

  it('should remove pending action by id', () => {
    const { addPendingAction, removePendingAction } = useOfflineStore.getState();
    
    addPendingAction({
      type: 'create',
      resource: '/api/v1/cats',
      payload: { name: 'Test Cat' },
    });
    
    const state = useOfflineStore.getState();
    const actionId = state.pendingActions[0].id;
    
    removePendingAction(actionId);
    
    const newState = useOfflineStore.getState();
    expect(newState.pendingActions).toHaveLength(0);
  });

  it('should set online status', () => {
    const { setOnlineStatus } = useOfflineStore.getState();
    
    setOnlineStatus(false);
    expect(useOfflineStore.getState().isOnline).toBe(false);
    
    setOnlineStatus(true);
    expect(useOfflineStore.getState().isOnline).toBe(true);
  });

  it('should update last sync time', () => {
    const { updateLastSync } = useOfflineStore.getState();
    
    const beforeSync = new Date();
    updateLastSync();
    const afterSync = new Date();
    
    const state = useOfflineStore.getState();
    expect(state.lastSyncTime).not.toBeNull();
    expect(new Date(state.lastSyncTime!).getTime()).toBeGreaterThanOrEqual(beforeSync.getTime());
    expect(new Date(state.lastSyncTime!).getTime()).toBeLessThanOrEqual(afterSync.getTime());
  });

  it('should increment retries for specific action', () => {
    const { addPendingAction, incrementRetries } = useOfflineStore.getState();
    
    addPendingAction({
      type: 'create',
      resource: '/api/v1/cats',
      payload: { name: 'Test Cat' },
    });
    
    const state = useOfflineStore.getState();
    const actionId = state.pendingActions[0].id;
    
    incrementRetries(actionId);
    
    const newState = useOfflineStore.getState();
    expect(newState.pendingActions[0].retries).toBe(1);
  });

  it('should clear all pending actions', () => {
    const { addPendingAction, clearPendingActions } = useOfflineStore.getState();
    
    addPendingAction({
      type: 'create',
      resource: '/api/v1/cats',
      payload: { name: 'Test Cat 1' },
    });
    addPendingAction({
      type: 'update',
      resource: '/api/v1/cats/1',
      payload: { name: 'Test Cat 2' },
    });
    
    expect(useOfflineStore.getState().pendingActions).toHaveLength(2);
    
    clearPendingActions();
    
    expect(useOfflineStore.getState().pendingActions).toHaveLength(0);
  });
});
