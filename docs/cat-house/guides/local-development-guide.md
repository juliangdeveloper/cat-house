# Cat House - Local Development Guide

**Last Updated:** January 5, 2026

Desarrollo local completamente offline con PostgreSQL, Docker, y hot-reload automático.

---

## Prerequisites

- Docker Desktop 24.0+
- Git 2.40+

```powershell
docker --version
docker-compose --version
```

---

## Quick Start

### 1. Verificar archivos .env.local

```powershell
cd cat-house-backend

# Verificar que existan (deben estar configurados)
ls auth-service/.env.local
ls catalog-service/.env.local
ls installation-service/.env.local
ls proxy-service/.env.local
```

**Si falta alguno**, copiar desde `.env.example` y configurar:
```bash
DATABASE_URL=postgresql+asyncpg://catuser:catpass@postgres:5432/cathouse
CORS_ORIGINS=["http://localhost:8080","http://localhost:8081"]
JWT_SECRET=dev-secret-change-in-production
```

### 2. Iniciar servicios

```powershell
# Levantar contenedores
docker-compose up -d --build

# Ejecutar migraciones
.\scripts\init-local-db.ps1
```

### 3. Verificar

```powershell
curl http://localhost:8080/api/v1/health
```

**Salida esperada:** JSON con status "healthy" de todos los servicios.

---

## Conexión a Base de Datos

```
Host: localhost
Port: 5435
Database: cathouse
User: catuser
Password: catpass
```

**psql:**
```powershell
docker exec -it cathouse-postgres psql -U catuser -d cathouse
```

**Esquemas creados:**
- `auth` → users
- `catalog` → cats, permissions  
- `installation` → installations, installation_permissions

---

## Daily Workflow

```powershell
# Iniciar
docker-compose up -d

# Ver logs
docker-compose logs -f

# Editar código → Hot-reload automático

# Detener
docker-compose down
```

---

## Database Management

**Migration Architecture:** Each service manages its own schema independently.

**Schemas:**
- `auth` → auth-service (users table)
- `catalog` → catalog-service (cats, permissions tables)
- `installation` → installation-service (installations, installation_permissions tables)

**Migraciones:**
```powershell
.\scripts\init-local-db.ps1              # Aplicar todas (auth + catalog + installation)
.\scripts\generate-migrations.ps1        # Generar nuevas en cada servicio
.\scripts\reset-and-migrate.ps1          # Reset completo (⚠️ borra datos)
```

**Generar migración para servicio específico:**
```powershell
cd cat-house-backend/auth-service
docker-compose exec -T auth-service alembic revision --autogenerate -m "Add column"

# O para catalog-service:
cd cat-house-backend/catalog-service
docker-compose exec -T catalog-service alembic revision --autogenerate -m "Add table"
```

**Inspeccionar:**
```powershell
docker exec -it cathouse-postgres psql -U catuser -d cathouse

\dt auth.*         # Tablas en auth
\dt catalog.*      # Tablas en catalog
\d auth.users      # Estructura de tabla
\q                 # Salir
```

---

## Troubleshooting

**PostgreSQL no inicia:**
```powershell
netstat -ano | findstr :5435  # Verificar puerto en uso
```

**Migraciones fallan:**
```powershell
docker-compose logs auth-service
.\scripts\reset-and-migrate.ps1  # Reset completo
```

**Nginx 502:**
```powershell
docker-compose ps              # Verificar servicios corriendo
docker-compose restart nginx   # Restart después de rebuild
```

**Hot-reload no funciona:**
```powershell
docker-compose restart <service-name>
docker-compose restart nginx  # Importante después de rebuild
```

---

## Referencias

- **Deployment:** [deployment-guide.md](./deployment-guide.md)
- **Database Schema:** [../database-schema.md](../database-schema.md)
- **CI/CD:** `.github/workflows/staging-pipeline.yml`
- **Secrets Management:** [../SECRETS-MANAGEMENT-GUIDE.md](../SECRETS-MANAGEMENT-GUIDE.md)

---

**Arquitectura detallada, configuración de frontend, y workflows avanzados:** Ver [deployment-guide.md](./deployment-guide.md)
