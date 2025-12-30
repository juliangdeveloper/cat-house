# Catalog Service

Cat discovery and metadata service for Cat House platform.

## Features

- Cat application discovery
- Cat metadata and descriptions
- User reviews and ratings
- Asset management (icons, screenshots)

## API Endpoints

### Health Check
- `GET /api/v1/catalog/health` - Service health status

### Catalog (To be implemented)
- `GET /api/v1/catalog/cats` - List all cats
- `GET /api/v1/catalog/cats/{catId}` - Get cat details
- `GET /api/v1/catalog/cats/{catId}/reviews` - Get cat reviews
- `POST /api/v1/catalog/cats/{catId}/reviews` - Submit review

## Port

Default: **8002**
