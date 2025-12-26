import { View, Text, ScrollView } from 'react-native';
import { styled } from '@tamagui/core';

const Container = styled(ScrollView, {
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

const Description = styled(Text, {
  fontSize: '$5',
  color: '$colorFocus',
  marginBottom: '$6',
});

const Placeholder = styled(View, {
  padding: '$6',
  backgroundColor: '$backgroundHover',
  borderRadius: '$4',
  alignItems: 'center',
});

const PlaceholderText = styled(Text, {
  fontSize: '$6',
  color: '$color',
});

export default function CatalogScreen() {
  return (
    <Container>
      <Title>Cat Catalog</Title>
      <Description>
        Browse and discover available Cat services for installation
      </Description>
      <Placeholder>
        <PlaceholderText>Cat services will appear here</PlaceholderText>
      </Placeholder>
    </Container>
  );
}
