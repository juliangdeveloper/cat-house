# Cat House Frontend

Universal Expo React Native application for Cat House platform - build once, deploy to web, iOS, and Android.

## 🚀 Quick Start

All development happens inside Docker containers. No local Node.js or Expo installation required.

### Prerequisites

- Docker Desktop installed
- Git

### First Time Setup

```bash
# Clone the repository (if not already done)
cd frontend

# Build the Docker container
docker-compose build frontend

# Start the development server
docker-compose up frontend
```

### Access the Application

- **Web**: http://localhost:8081
- **Mobile (Expo Go)**: Scan the QR code displayed in terminal with Expo Go app

## 📁 Project Structure

```
frontend/
├── app/                          # Expo Router file-based routing
│   ├── _layout.tsx              # Root layout with providers
│   └── (tabs)/                  # Tab navigation group
│       ├── _layout.tsx          # Tabs configuration
│       ├── index.tsx            # Home/Dashboard screen
│       ├── catalog.tsx          # Catalog browser screen
│       └── profile.tsx          # Profile screen
├── stores/                       # Zustand state management
│   ├── auth.ts                  # Authentication state
│   └── offline.ts               # Offline queue state
├── api/                         # API client and services
│   ├── client.ts                # Axios instance with interceptors
│   └── services/                # Typed API functions
│       ├── auth.ts              # Login, register, refresh
│       ├── catalog.ts           # Browse cats
│       └── installation.ts      # Install/manage cats
├── tamagui.config.ts            # UI theme configuration
├── Dockerfile                   # Development container
├── docker-compose.yml           # Service orchestration
├── package.json                 # Dependencies
├── app.json                     # Expo configuration
└── tsconfig.json                # TypeScript configuration
```

## 🐳 Docker Commands

### Development

```bash
# Start development server (detached)
docker-compose up -d frontend

# View logs
docker-compose logs -f frontend

# Stop server
docker-compose down

# Rebuild container (after Dockerfile changes)
docker-compose build --no-cache frontend

# Access container shell
docker-compose exec frontend sh
```

### Installing Packages

```bash
# Install a new package
docker-compose run --rm frontend npm install <package-name>

# Install with legacy peer deps (if conflicts)
docker-compose run --rm frontend npm install --legacy-peer-deps <package-name>

# Update all packages
docker-compose run --rm frontend npm update
```

### Running Commands

```bash
# Run any npm script
docker-compose run --rm frontend npm run <script>

# Run Expo CLI commands
docker-compose run --rm frontend npx expo <command>

# Type checking
docker-compose run --rm frontend npm run type-check

# Linting
docker-compose run --rm frontend npm run lint
```

## 🧪 Testing

```bash
# Run all tests
docker-compose run --rm frontend npm test

# Run tests in watch mode
docker-compose run --rm frontend npm run test:watch

# Generate coverage report
docker-compose run --rm frontend npm run test:coverage
```

## 🛠️ Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Expo SDK** | 54+ | Universal React Native framework |
| **Expo Router** | 6+ | File-based routing for web + native |
| **React Native** | 0.81+ | Cross-platform UI |
| **TypeScript** | 5.9+ | Type safety |
| **Tamagui** | 1.109+ | Cross-platform UI components & theming |
| **Zustand** | 4.5+ | State management |
| **Axios** | 1.6+ | HTTP client |
| **Expo SecureStore** | 14+ | Encrypted storage (native) |
| **Jest** | 29+ | Testing framework |
| **Docker** | Latest | Development environment |

## 🎨 UI Components (Tamagui)

The project uses Tamagui for cross-platform UI components with built-in theming.

```tsx
import { styled } from '@tamagui/core';
import { View, Text } from 'react-native';

const Container = styled(View, {
  flex: 1,
  backgroundColor: '$background',
  padding: '$4',
});

const Title = styled(Text, {
  fontSize: '$8',
  color: '$color',
});
```

**Theme Switching**: Automatic light/dark theme support based on device settings.

## 📡 API Integration

### Base URL

```
https://chapi.gamificator.click
```

### Available Services

- **Auth Service** (`api/services/auth.ts`): Login, register, token refresh
- **Catalog Service** (`api/services/catalog.ts`): Browse and search cats
- **Installation Service** (`api/services/installation.ts`): Install and manage cats

### Example Usage

```tsx
import { authService } from './api/services/auth';
import { useAuthStore } from './stores/auth';

const handleLogin = async (email: string, password: string) => {
  try {
    const response = await authService.login({ email, password });
    useAuthStore.getState().setToken(response.token, response.refreshToken);
    useAuthStore.getState().setUser(response.user);
  } catch (error) {
    console.error('Login failed:', error);
  }
};
```

## 🔐 Environment Variables

Environment variables are prefixed with `EXPO_PUBLIC_` to be accessible in client code.

```bash
# .env.development
EXPO_PUBLIC_API_URL=https://chapi.gamificator.click
EXPO_PUBLIC_ENV=development
EXPO_PUBLIC_DEBUG=true
```

**Files:**
- `.env.development` - Development configuration
- `.env.production` - Production configuration  
- `.env.example` - Template with all variables

**Note**: `.env*.local` and `.env.production` are gitignored for security.

## 🗃️ State Management (Zustand)

### Auth Store

```tsx
import { useAuthStore } from './stores/auth';

function MyComponent() {
  const { token, user, setToken, clearAuth } = useAuthStore();
  
  // Use state and actions
}
```

### Offline Store

```tsx
import { useOfflineStore } from './stores/offline';

function MyComponent() {
  const { isOnline, pendingActions, addPendingAction } = useOfflineStore();
  
  // Queue actions when offline
}
```

## 🚢 Build & Deployment

### Web Build (Docker)

```bash
# Export static web build
docker-compose run --rm frontend npx expo export --platform web

# Output directory: dist/
```

**Deployment**: Upload `dist/` contents to AWS S3 + CloudFront.

### Mobile Build (EAS Build - Cloud)

Mobile builds use Expo Application Services (EAS) which runs in the cloud.

```bash
# Install EAS CLI (one-time, in container)
docker-compose run --rm frontend npm install -g eas-cli

# Configure EAS project
docker-compose run --rm frontend eas build:configure

# Build for iOS
docker-compose run --rm frontend eas build --platform ios

# Build for Android
docker-compose run --rm frontend eas build --platform android
```

**Note**: EAS builds require an Expo account and run in Expo's cloud infrastructure.

## 🧭 Navigation

The app uses Expo Router for file-based routing:

- `/` → `app/(tabs)/index.tsx` - Home/Dashboard
- `/catalog` → `app/(tabs)/catalog.tsx` - Cat Catalog
- `/profile` → `app/(tabs)/profile.tsx` - User Profile

### Deep Linking

The app supports deep linking with scheme: `cathouse://`

```
cathouse://catalog/cat-123
```

Configure in `app.json`:
```json
{
  "expo": {
    "scheme": "cathouse"
  }
}
```

## 🔧 Development Workflow

1. **Make code changes** - Files are synced via Docker volume mounts
2. **Hot reload** - Changes auto-refresh in browser/Expo Go
3. **Test changes** - Run `npm test` in container
4. **Type check** - Run `npm run type-check`
5. **Commit** - Commit changes to Git

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Stop all containers
docker-compose down

# Or kill process on port 8081 (Windows)
netstat -ano | findstr :8081
taskkill /PID <PID> /F
```

### Container Won't Start

```bash
# Rebuild without cache
docker-compose build --no-cache frontend

# Remove volumes and restart
docker-compose down -v
docker-compose up frontend
```

### Package Installation Fails

```bash
# Use legacy peer deps flag
docker-compose run --rm frontend npm install --legacy-peer-deps
```

### Metro Bundler Issues

```bash
# Clear Metro cache
docker-compose run --rm frontend npx expo start -c
```

## 📚 Additional Resources

- [Expo Documentation](https://docs.expo.dev/)
- [Expo Router Guide](https://docs.expo.dev/router/introduction/)
- [Tamagui Documentation](https://tamagui.dev/)
- [Zustand Documentation](https://zustand-demo.pmnd.rs/)
- [React Native Documentation](https://reactnavigation.org/)

## 🤝 Contributing

1. Create a feature branch
2. Make changes in Docker environment
3. Write tests for new features
4. Run full test suite
5. Submit pull request

## 📄 License

Proprietary - Cat House Platform
