import { View, Text } from 'react-native';
import { styled } from '@tamagui/core';

const Container = styled(View, {
  flex: 1,
  backgroundColor: '$background',
  padding: '$4',
});

const Title = styled(Text, {
  fontSize: '$8',
  fontWeight: 'bold',
  color: '$color',
  marginBottom: '$4',
});

const Section = styled(View, {
  padding: '$4',
  backgroundColor: '$backgroundHover',
  borderRadius: '$4',
  marginBottom: '$4',
});

const SectionTitle = styled(Text, {
  fontSize: '$6',
  fontWeight: 'bold',
  color: '$color',
  marginBottom: '$2',
});

const SectionText = styled(Text, {
  fontSize: '$5',
  color: '$colorFocus',
});

export default function ProfileScreen() {
  return (
    <Container>
      <Title>My Profile</Title>
      <Section>
        <SectionTitle>Account Information</SectionTitle>
        <SectionText>User profile details will appear here</SectionText>
      </Section>
      <Section>
        <SectionTitle>Installed Cats</SectionTitle>
        <SectionText>Your installed Cat services will appear here</SectionText>
      </Section>
    </Container>
  );
}
