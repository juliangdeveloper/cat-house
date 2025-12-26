# Development Dockerfile for Expo React Native Application
# Node.js 20 Alpine for minimal image size
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install Expo CLI and dependencies globally
RUN npm install -g expo-cli@latest

# Install system dependencies for Expo
RUN apk add --no-cache \
    git \
    bash

# Expose ports for Expo development
# 8081: Metro bundler web interface
# 19000: Expo DevTools
# 19001: Expo DevTools websocket
# 19002: Expo Dev server
EXPOSE 8081 19000 19001 19002

# Copy package files (will be overridden by volume mount in development)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code (will be overridden by volume mount in development)
COPY . .

# Health check endpoint (simple file check)
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD node -e "require('fs').accessSync('/app/package.json')" || exit 1

# Default command to start Expo dev server
CMD ["npx", "expo", "start", "--web"]
