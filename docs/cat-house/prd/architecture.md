# Cat House Platform - System Architecture

**Created:** November 30, 2025 | **Version:** 2.0 | **Last Updated:** December 31, 2025

---

## Architecture Overview

Cat House uses a **completely decoupled architecture** with containerized backend services and independent frontend deployment. All communication flows through RESTful APIs with JWT authentication.

---

## High-Level Architecture

```mermaid
graph TB
    Users[Users] --> FE[Frontend Application]
    FE --> ALB[Application Load Balancer]
    ALB --> Auth[Auth Service]
    ALB --> Catalog[Catalog Service]
    ALB --> Install[Installation Service]
    ALB --> Proxy[Cat Proxy Service]
    
    Auth --> DB[(PostgreSQL)]
    Catalog --> DB
    Catalog --> S3[Object Storage]
    Install --> DB
    Proxy --> CatServices[External Cat Services]
    
    FE --> LocalStore[localStorage / SecureStore]
```

---

## Backend Architecture

### Containerized Microservices
- **Auth Service:** User authentication, JWT generation, role management
- **Catalog Service:** Cat discovery, metadata, reviews
- **Installation Service:** Instance management, permissions, credentials
- **Cat Proxy Service:** Request mediation, validation, audit

### Technology Stack
- **Language:** Python 3.11+ | **Framework:** FastAPI
- **Database:** Neon (Serverless PostgreSQL)
- **Storage:** AWS S3 | **Container:** Docker/ECS Fargate
- **Load Balancer:** AWS Application Load Balancer
- **Logging:** Structured JSON with X-Trace-ID correlation
- **Hosting:** AWS (sa-east-1) | **Domain:** gamificator.click
- **CI/CD:** GitHub Actions (consolidated pipeline)

---

## Frontend Architecture

### Universal Application (Web, iOS, Android)
- **Framework:** Expo + React Native (TypeScript)
- **Web Target:** Expo (web)
- **Routing:** Expo Router (file‑based, compatible con web y nativo)
- **State:** Zustand (persistencia por plataforma: SecureStore en nativo, localStorage en web)
- **UI/Design System:** Tamagui (componentes cross‑platform y theming)
- **Deployment (Web):** AWS S3 + CloudFront
- **Staging:** https://chs.gamificator.click
- **Production:** https://chapp.gamificator.click
- **Distribución (Mobile):** EAS Build para iOS/Android

### Cat UI Package System
- UI packages stored locally for offline usage (web/nativo)
- Dynamic loading (lazy loading / dynamic import según plataforma)
- Sandboxed/aislamiento de UI según plataforma
- Offline support: almacenamiento persistente + cola de acciones (según plataforma)

---

## API Communication

### RESTful Endpoints
```
POST   /api/v1/auth/login
GET    /api/v1/catalog/cats
POST   /api/v1/install/{catId}
POST   /api/v1/proxy/{catId}/action
```
**Staging ALB:** `http://cat-house-staging-alb-1968126506.sa-east-1.elb.amazonaws.com`  
**Production ALB:** `http://cat-house-production-alb-1773695723.sa-east-1.elb.amazonaws.com`

### Security
- JWT bearer tokens in `Authorization` header
- HTTPS only, proper CORS configuration
- Scoped credentials per cat installation
- Backend validates all permissions before proxying
- Structured JSON logging with X-Trace-ID for request tracking
- Secrets injection via GitHub Actions (no secrets in Terraform state)

---

**Document Owner:** Winston (Architect)