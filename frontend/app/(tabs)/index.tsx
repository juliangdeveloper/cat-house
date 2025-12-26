import { View, Text } from 'react-native';
import { styled } from '@tamagui/core';

const Container = styled(View, {
  flex: 1,
  justifyContent: 'center',
  alignItems: 'center',
  backgroundColor: '$background',
  padding: '$4',
});

const Title = styled(Text, {
  fontSize: '$9',
  fontWeight: 'bold',
  color: '$color',
  marginBottom: '$4',
});

const Subtitle = styled(Text, {
  fontSize: '$6',
  color: '$colorFocus',
  textAlign: 'center',
});

export default function HomeScreen() {
  return (
    <Container>
      <Title>Welcome to Cat House</Title>
      <Subtitle>
        Your universal platform for discovering and managing Cat services
      </Subtitle>
    </Container>
  );
}
