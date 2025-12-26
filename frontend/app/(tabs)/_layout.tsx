import { Tabs } from 'expo-router';

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: true,
        tabBarStyle: {
          backgroundColor: '#f8f9fa',
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          headerTitle: 'Cat House Dashboard',
        }}
      />
      <Tabs.Screen
        name="catalog"
        options={{
          title: 'Catalog',
          headerTitle: 'Cat Catalog',
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          headerTitle: 'My Profile',
        }}
      />
    </Tabs>
  );
}
