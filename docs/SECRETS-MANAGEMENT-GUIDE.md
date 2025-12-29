# 🔐 Guía de Gestión de Secretos y Variables Sensibles

## 📋 Índice

1. [Introducción](#introducción)
2. [Configuración de GitHub Secrets](#configuración-de-github-secrets)
3. [Variables de Entorno por Servicio](#variables-de-entorno-por-servicio)
4. [Workflow de Desarrollo](#workflow-de-desarrollo)
5. [Seguridad y Mejores Prácticas](#seguridad-y-mejores-prácticas)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Introducción

Este repositorio es **PÚBLICO**, por lo que es crítico nunca almacenar información sensible directamente en el código fuente. Toda la información confidencial debe gestionarse mediante:

- **GitHub Secrets**: Para CI/CD y workflows de GitHub Actions
- **AWS Secrets Manager**: Para credenciales de producción en ECS
- **Variables de entorno locales**: Archivo `.env` (nunca commiteado)

### ⚠️ Información Sensible NUNCA debe incluir:

- ❌ Contraseñas de bases de datos
- ❌ API keys y tokens
- ❌ Claves de JWT
- ❌ AWS Access Keys y Secret Keys
- ❌ Claves de encriptación
- ❌ Credenciales de servicios externos

---

## 🔑 Configuración de GitHub Secrets

### Paso 1: Acceder a GitHub Secrets

1. Ve a tu repositorio: https://github.com/juliangdeveloper/cat-house
2. Click en **Settings** → **Secrets and variables** → **Actions**
3. Click en **New repository secret**

### Paso 2: Secrets Requeridos

#### 🗄️ Base de Datos (Neon PostgreSQL)

```yaml
NEON_DATABASE_URL
# Formato: postgresql+asyncpg://USERNAME:PASSWORD@HOST/DATABASE
# Ejemplo: postgresql+asyncpg://neondb_owner:xxxxx@ep-xxxxx-pooler.c-2.us-east-2.aws.neon.tech/neondb

NEON_MIGRATION_DATABASE_URL
# Formato: postgresql://USERNAME:PASSWORD@HOST/DATABASE?sslmode=require
# Solo necesario para auth-service (maneja migraciones)
```

#### ☁️ AWS Credentials

```yaml
AWS_ACCESS_KEY_ID
# Tu AWS Access Key ID para ECR y ECS deployments

AWS_SECRET_ACCESS_KEY
# Tu AWS Secret Access Key

AWS_REGION
# Región de AWS (ejemplo: sa-east-1, us-east-1)

AWS_ACCOUNT_ID
# ID de tu cuenta de AWS (ejemplo: 578492750346)
```

#### 🔐 Authentication & Security

```yaml
JWT_SECRET
# Clave secreta para firmar tokens JWT
# Generar con: openssl rand -hex 32

ENCRYPTION_KEY
# Clave de encriptación de 32 caracteres para installation-service
# Generar con: openssl rand -base64 32

API_KEY_SECRET
# Clave secreta para generar API keys (task-manager-cat)
# Generar con: openssl rand -hex 32

ADMIN_API_KEY
# Clave admin para endpoints de administración
# Generar con: openssl rand -hex 24
```

#### 🪣 AWS S3

```yaml
S3_BUCKET
# Nombre del bucket S3 para assets
# Ejemplo: cathouse-assets-prod

S3_REGION
# Región del bucket S3
# Ejemplo: us-east-1
```

### Paso 3: Uso en GitHub Actions

Los secrets se usan en workflows de la siguiente manera:

```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}

      - name: Build and push Docker image
        env:
          DATABASE_URL: ${{ secrets.NEON_DATABASE_URL }}
          JWT_SECRET: ${{ secrets.JWT_SECRET }}
        run: |
          docker build \
            --build-arg DATABASE_URL="$DATABASE_URL" \
            --build-arg JWT_SECRET="$JWT_SECRET" \
            -t my-image .
```

---

## 📦 Variables de Entorno por Servicio

### Auth Service (`cat-house-backend/auth-service`)

**Archivo local:** `.env` (copiar desde `.env.example`)

```bash
# Servicio
SERVICE_NAME=Auth Service
DEBUG=false
PORT=8005
ENVIRONMENT=production

# Base de datos (usar GitHub Secret en producción)
DATABASE_URL=postgresql+asyncpg://USERNAME:PASSWORD@HOST/DATABASE
MIGRATION_DATABASE_URL=postgresql://USERNAME:PASSWORD@HOST/DATABASE?sslmode=require

# Autenticación (usar GitHub Secret)
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# CORS
ALLOWED_ORIGINS=["https://app.gamificator.click"]

# Connection Pooling
POOL_SIZE=5
MAX_OVERFLOW=10
```

### Catalog Service (`cat-house-backend/catalog-service`)

```bash
# Base de datos
DATABASE_URL=postgresql+asyncpg://USERNAME:PASSWORD@HOST/DATABASE

# S3 (usar GitHub Secrets)
S3_BUCKET=cathouse-assets-prod
S3_REGION=us-east-1
```

### Installation Service (`cat-house-backend/installation-service`)

```bash
# Base de datos
DATABASE_URL=postgresql+asyncpg://USERNAME:PASSWORD@HOST/DATABASE

# Encriptación (usar GitHub Secret)
ENCRYPTION_KEY=32-character-encryption-key-here
```

### Proxy Service (`cat-house-backend/proxy-service`)

```bash
# Base de datos
DATABASE_URL=postgresql+asyncpg://USERNAME:PASSWORD@HOST/DATABASE

# Request Configuration
REQUEST_TIMEOUT=30
MAX_RETRIES=3
```

### Task Manager Cat (`task-manager-cat`)

```bash
# Base de datos
DATABASE_URL=postgresql+asyncpg://USERNAME:PASSWORD@HOST/DATABASE?sslmode=require
MIGRATION_DATABASE_URL=postgresql://USERNAME:PASSWORD@HOST/DATABASE?sslmode=require

# API Keys (usar GitHub Secrets)
API_KEY_SECRET=your-secret-key-min-32-chars
ADMIN_API_KEY=admin-key-secure-value

# CORS
CORS_ORIGINS=https://cathouse.gamificator.click
```

### Frontend (`frontend`)

```bash
# API URL
EXPO_PUBLIC_API_URL=https://chapi.gamificator.click
EXPO_PUBLIC_ENV=production
EXPO_PUBLIC_DEBUG=false
```

---

## 🔄 Workflow de Desarrollo

### Para Desarrollo Local

1. **Clona el repositorio**
   ```bash
   git clone https://github.com/juliangdeveloper/cat-house.git
   cd cat-house
   ```

2. **Configura variables de entorno locales**
   ```bash
   # Backend services
   cd cat-house-backend/auth-service
   cp .env.example .env
   # Edita .env con tus credenciales locales o de desarrollo
   
   # Repite para cada servicio
   ```

3. **Nunca commitees archivos .env**
   ```bash
   # Verifica que .env esté en .gitignore
   git check-ignore .env
   # Debería retornar: .env
   ```

4. **Usa docker-compose para desarrollo**
   ```bash
   # Los archivos docker-compose.yml pueden usar variables de .env
   docker-compose up
   ```

### Para CI/CD (GitHub Actions)

1. **Los secrets se configuran una vez** en GitHub Settings
2. **Los workflows automáticamente usan los secrets** definidos
3. **No es necesario hacer nada más** - los secrets se inyectan en build time

### Para Producción (AWS ECS)

1. **Opción A: Variables de entorno en Task Definition**
   - Definir en `terraform/ecs_services.tf`
   - Usar secrets de GitHub para valores sensibles en Terraform

2. **Opción B: AWS Secrets Manager (Recomendado)**
   ```terraform
   # terraform/ecs_services.tf
   resource "aws_ecs_task_definition" "auth_service" {
     # ...
     secrets = [
       {
         name      = "DATABASE_URL"
         valueFrom = aws_secretsmanager_secret.db_url.arn
       }
     ]
   }
   ```

---

## 🛡️ Seguridad y Mejores Prácticas

### ✅ DO - Hacer

1. **Usa archivos .example como plantillas**
   - Los archivos `.env.example` deben tener placeholders
   - Nunca incluir credenciales reales en archivos .example

2. **Rota credenciales regularmente**
   - Cambiar passwords de BD cada 90 días
   - Rotar API keys y JWT secrets periódicamente

3. **Usa secrets específicos por ambiente**
   - Desarrollo: Credenciales locales/dev
   - Staging: Credenciales de staging
   - Producción: Credenciales de producción

4. **Verifica antes de commit**
   ```bash
   # Usar pre-commit hooks (ver siguiente sección)
   git diff --staged
   ```

5. **Revisa regularmente GitHub Secrets**
   - Eliminar secrets obsoletos
   - Actualizar documentación cuando cambien secrets

### ❌ DON'T - No Hacer

1. **NUNCA** commitear archivos `.env` reales
2. **NUNCA** incluir credenciales en mensajes de commit
3. **NUNCA** compartir secrets por Slack, email o WhatsApp
4. **NUNCA** usar las mismas credenciales en dev y producción
5. **NUNCA** hardcodear credenciales en el código fuente
6. **NUNCA** loggear valores de secrets en aplicaciones

### 🔍 Pre-commit Hooks (Protección adicional)

Instala `pre-commit` para detectar secrets antes de commit:

```bash
# Instalar pre-commit
pip install pre-commit

# Crear archivo .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: package-lock.json

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.1
    hooks:
      - id: gitleaks
EOF

# Activar pre-commit hooks
pre-commit install

# Crear baseline (primera vez)
detect-secrets scan > .secrets.baseline
```

Ahora, cada vez que intentes hacer commit, se verificará automáticamente si hay secrets expuestos.

---

## 🔧 Troubleshooting

### Problema: "Database connection failed"

**Solución:**
1. Verifica que `DATABASE_URL` esté correctamente configurado
2. Verifica conectividad a Neon PostgreSQL
3. Confirma que el secret en GitHub esté actualizado

### Problema: "JWT decode error"

**Solución:**
1. Verifica que `JWT_SECRET` sea el mismo en todos los servicios
2. Confirma que el secret en GitHub coincida con el usado en producción

### Problema: "AWS credentials not found"

**Solución:**
1. Verifica que `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY` estén en GitHub Secrets
2. Confirma que el workflow use `aws-actions/configure-aws-credentials@v1`

### Problema: "Secret not found in GitHub Actions"

**Solución:**
1. Verifica que el secret esté definido en Settings → Secrets and variables → Actions
2. Confirma el nombre exacto (case-sensitive)
3. Verifica que uses `${{ secrets.SECRET_NAME }}` en el workflow

---

## 📚 Referencias

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
- [Neon PostgreSQL Connection Strings](https://neon.tech/docs/connect/connect-from-any-app)
- [Pre-commit Hooks](https://pre-commit.com/)
- [detect-secrets](https://github.com/Yelp/detect-secrets)
- [gitleaks](https://github.com/gitleaks/gitleaks)

---

## 🚨 En Caso de Exposición de Secrets

Si accidentalmente commiteas un secret:

1. **INMEDIATAMENTE rotar la credencial expuesta**
   - Cambiar password en Neon
   - Generar nuevo JWT secret
   - Rotar AWS keys

2. **Actualizar GitHub Secrets con nuevos valores**

3. **Limpiar historial de Git (si es necesario)**
   ```bash
   # Usar BFG Repo-Cleaner o git filter-branch
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch path/to/sensitive/file' \
     --prune-empty --tag-name-filter cat -- --all
   
   git push origin --force --all
   ```

4. **Notificar al equipo**

---

**Última actualización:** 29 de diciembre de 2025  
**Mantenedor:** @juliangdeveloper  
**Versión:** 1.0.0
