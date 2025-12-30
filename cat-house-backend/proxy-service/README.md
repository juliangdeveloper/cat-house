# Cat Proxy Service

Request mediation and validation service for Cat House platform.

## Features

- Request routing to external cat services
- Permission validation
- Request/response auditing
- Rate limiting and retry logic

## API Endpoints

### Health Check
- `GET /api/v1/proxy/health` - Service health status

### Proxy (To be implemented)
- `POST /api/v1/proxy/{catId}/action` - Proxy request to cat service
- `GET /api/v1/proxy/{catId}/status` - Check cat service status

## Port

Default: **8004**
