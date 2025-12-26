import { Stack } from 'expo-router';
import { TamaguiProvider } from '@tamagui/core';
import { useColorScheme } from 'react-native';
import config from '../tamagui.config';

export default function RootLayout() {
  const colorScheme = useColorScheme();

  return (
    <TamaguiProvider config={config} defaultTheme={colorScheme === 'dark' ? 'dark' : 'light'}>
      <Stack>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      </Stack>
    </TamaguiProvider>
  );
}
