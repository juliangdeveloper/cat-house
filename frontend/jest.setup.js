// Jest setup file

// Define global variables needed by React Native
global.__DEV__ = true;

// Mock localStorage for web platform tests
global.localStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

// Mock React Native Platform (before importing anything)
global.Platform = {
  OS: 'web',
  select: (obj) => obj.web || obj.default,
};

// Import testing library extend matchers - do this BEFORE mocking react-native
// to avoid circular dependency issues
// import '@testing-library/jest-native/extend-expect';

// Mock Expo SecureStore
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

// Mock Expo Constants
jest.mock('expo-constants', () => ({
  __esModule: true,
  default: {
    expoConfig: {
      extra: {
        EXPO_PUBLIC_API_URL: 'https://chapi.gamificator.click',
      },
    },
  },
}));

// Mock React Native - full mock to avoid loading actual RN
jest.mock('react-native', () => ({
  Platform: {
    OS: 'web',
    select: (obj) => obj.web || obj.default,
  },
  useColorScheme: jest.fn(() => 'light'),
  StyleSheet: {
    create: (styles) => styles,
  },
  View: 'View',
  Text: 'Text',
  TouchableOpacity: 'TouchableOpacity',
}));
