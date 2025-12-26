# 🔐 Guía de Configuración de Variables de Entorno y API Keys

Este documento lista todas las configuraciones sensibles que necesitas configurar antes de desplegar el sistema.

## ⚠️ IMPORTANTE: Seguridad

**NUNCA** subas archivos con credenciales reales a Git:
- `.env` (servicios)
- `terraform.tfvars` (Terraform)
- Archivos con API keys o secrets

## 📑 Índice de Configuraciones

1. [Credenciales AWS](#1-credenciales-aws)
2. [Terraform Variables](#2-terraform-variables)
3. [Variables de Servicios Backend](#3-variables-de-servicios-backend)
4. [JWT Secret Keys](#4-jwt-secret-keys)
5. [Database Credentials](#5-database-credentials)

---

## 1. Credenciales AWS

### Ubicación
No se guardan en archivos del proyecto, se configuran con AWS CLI.

### Configuración

```bash
# Ejecuta este comando
aws configure

# Te pedirá:
AWS Access Key ID [None]: AKIA................
AWS Secret Access Key [None]: wJalr...........................
Default region name [None]: us-east-1
Default output format [None]: json
```

### Dónde Obtenerlas
1. AWS Console → IAM → Users → Tu usuario → Security credentials
2. Crear "Access key" si no tienes una

### Permisos Necesarios
Tu usuario IAM necesita permisos para:
- API Gateway (crear, modificar, eliminar)
- CloudWatch Logs (crear grupos de logs)
- IAM (crear roles para API Gateway)

---

## 2. Terraform Variables

### Archivo a Crear
`cat-house-backend/terraform/terraform.tfvars`

### Pasos

```bash
cd cat-house-backend/terraform
cp terraform.tfvars.example terraform.tfvars
```

### Configuración Requerida

```hcl
# Región AWS
aws_region = "us-east-1"  # O tu región preferida

# URLs de tus servicios backend
# DEBEN ser públicamente accesibles desde Internet
auth_service_url         = "https://tu-dominio-auth.com"
catalog_service_url      = "https://tu-dominio-catalog.com"
installation_service_url = "https://tu-dominio-installation.com"
proxy_service_url        = "https://tu-dominio-proxy.com"
health_aggregator_url    = "https://tu-dominio-health.com"

# Opcional: Para dominio personalizado
# certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/xxxxx"
```

### Notas Importantes
- ⚠️ Las URLs deben ser HTTPS en producción
- ⚠️ Deben ser accesibles públicamente (no localhost)
- ⚠️ Verifica que cada servicio responda en su URL antes de aplicar Terraform

---

## 3. Variables de Servicios Backend

### Archivos a Crear

Para cada servicio, copia el `.env.example` a `.env`:

```bash
# Auth Service
cp cat-house-backend/auth-service/.env.example cat-house-backend/auth-service/.env

# Catalog Service
cp cat-house-backend/catalog-service/.env.example cat-house-backend/catalog-service/.env

# Installation Service
cp cat-house-backend/installation-service/.env.example cat-house-backend/installation-service/.env

# Proxy Service
cp cat-house-backend/proxy-service/.env.example cat-house-backend/proxy-service/.env
```

### Variables Comunes en Todos los Servicios

```bash
# Entorno
DEBUG=False  # True en desarrollo, False en producción
ENVIRONMENT=production  # development, staging, o production

# Database - Neon PostgreSQL
DATABASE_URL=postgresql+asyncpg://usuario:password@host.neon.tech/neondb
```

---

## 4. JWT Secret Keys

### Auth Service REQUIERE esto

**Ubicación:** `cat-house-backend/auth-service/.env`

```bash
# JWT Configuration
JWT_SECRET=tu-clave-secreta-muy-segura-aqui-cambiala-en-produccion
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60
```

### 🔐 Cómo Generar un JWT Secret Seguro

**Opción 1: Python**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Opción 2: OpenSSL**
```bash
openssl rand -base64 32
```

**Opción 3: Node.js**
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

**Opción 4: PowerShell (Windows)**
```powershell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

### ⚠️ Importante
- Usa una clave diferente para cada entorno (dev, staging, prod)
- Nunca reutilices claves de otros proyectos
- Guarda la clave de producción en un gestor de secretos (AWS Secrets Manager, etc.)

---

## 5. Database Credentials

### Neon PostgreSQL Connection String

**Ubicación:** Todos los servicios necesitan `DATABASE_URL` en su `.env`

### Formato de la URL

```bash
# Para servicios (asyncpg)
DATABASE_URL=postgresql+asyncpg://USUARIO:PASSWORD@HOST.neon.tech/NOMBRE_DB

# Para migraciones (psycopg2) - Solo auth-service
MIGRATION_DATABASE_URL=postgresql://USUARIO:PASSWORD@HOST.neon.tech/NOMBRE_DB?sslmode=require
```

### Dónde Obtener las Credenciales

1. Ve a [Neon Console](https://console.neon.tech)
2. Selecciona tu proyecto
3. Ve a "Connection Details"
4. Copia la connection string
5. Reemplaza en los archivos `.env`

### Ejemplo Completo

```bash
DATABASE_URL=postgresql+asyncpg://neondb_owner:npg_ABC123xyz@ep-example.c-2.us-east-2.aws.neon.tech/neondb
```

### ⚠️ Seguridad de Base de Datos
- Usa pooling connections (ya configurado)
- Cada servicio tiene límites de pool configurados
- No compartas credenciales de producción

---

## 6. CORS Configuration

### Auth Service

**Ubicación:** `cat-house-backend/auth-service/.env`

```bash
# CORS Origins permitidos
ALLOWED_ORIGINS=["https://gamificator.click","https://app.gamificator.click"]
```

### Notas
- Formato: JSON array de strings
- Incluye todos los dominios frontend que necesiten acceso
- No uses `*` en producción

---

## 7. Pool de Conexiones (Opcional pero Recomendado)

Cada servicio puede tener configuración específica de pool:

```bash
# Auth Service
POOL_SIZE=2
MAX_OVERFLOW=1

# Catalog Service
POOL_SIZE=2
MAX_OVERFLOW=1

# Installation Service
POOL_SIZE=2
MAX_OVERFLOW=1

# Proxy Service
POOL_SIZE=2
MAX_OVERFLOW=1
```

---

## ✅ Checklist de Configuración

Antes de desplegar, verifica que has configurado:

### AWS
- [ ] AWS CLI configurado (`aws configure`)
- [ ] Credenciales con permisos adecuados
- [ ] Región seleccionada

### Terraform
- [ ] `terraform.tfvars` creado y configurado
- [ ] URLs de servicios actualizadas
- [ ] URLs son públicamente accesibles

### Servicios Backend
- [ ] Todos los `.env` creados desde `.env.example`
- [ ] `DATABASE_URL` configurado en cada servicio
- [ ] `JWT_SECRET` generado y configurado en auth-service
- [ ] `ALLOWED_ORIGINS` configurado con dominios correctos
- [ ] `DEBUG=False` en producción

### Base de Datos
- [ ] Neon project creado
- [ ] Connection strings obtenidas
- [ ] Migraciones ejecutadas (auth-service)

---

## 🔒 Gestión de Secretos en Producción

### Recomendaciones

**No uses archivos .env en producción**. En su lugar:

1. **AWS Secrets Manager** (Recomendado)
   ```bash
   aws secretsmanager create-secret --name cathouse/jwt-secret --secret-string "tu-secret"
   ```

2. **Variables de Entorno del Sistema**
   - Docker: `environment` en docker-compose
   - Kubernetes: ConfigMaps y Secrets
   - AWS ECS: Variables de entorno de tareas

3. **AWS Parameter Store**
   ```bash
   aws ssm put-parameter --name /cathouse/jwt-secret --value "tu-secret" --type SecureString
   ```

---

## 🆘 Troubleshooting

### Error: "Invalid JWT Secret"
- Verifica que `JWT_SECRET` esté configurado en auth-service
- Asegúrate de que no tenga espacios ni caracteres especiales problemáticos

### Error: "Database Connection Failed"
- Verifica la `DATABASE_URL`
- Comprueba que Neon project esté activo
- Verifica que el formato incluya `postgresql+asyncpg://`

### Error: "CORS Error"
- Verifica `ALLOWED_ORIGINS` incluye tu dominio frontend
- Formato debe ser JSON array válido
- Incluye protocolo (https://)

### Error: "502 Bad Gateway" en API Gateway
- Verifica que las URLs en `terraform.tfvars` sean accesibles
- Prueba con curl cada URL manualmente
- Verifica que servicios respondan en el puerto correcto

---

## 📚 Referencias

- [AWS CLI Configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)
- [Neon PostgreSQL Docs](https://neon.tech/docs)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
