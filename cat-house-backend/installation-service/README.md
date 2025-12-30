# Installation Service

Cat installation and instance management service for Cat House platform.

## Features

- Cat installation management
- Instance lifecycle (create, update, delete)
- Permission management
- Credential storage (encrypted)

## API Endpoints

### Health Check
- `GET /api/v1/installation/health` - Service health status

### Installation (To be implemented)
- `POST /api/v1/install/{catId}` - Install a cat
- `GET /api/v1/install` - List user installations
- `GET /api/v1/install/{installId}` - Get installation details
- `DELETE /api/v1/install/{installId}` - Uninstall a cat

## Port

Default: **8003**
