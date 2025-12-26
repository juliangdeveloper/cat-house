# 🚀 Quick Start: Configuración de Credenciales

## Archivos que DEBES crear antes de desplegar:

### 1. AWS Credentials (Terminal)
```bash
aws configure
# Ingresa: Access Key ID, Secret Access Key, Region (us-east-1)
```

### 2. Terraform Variables
```bash
cd cat-house-backend/terraform
cp terraform.tfvars.example terraform.tfvars
# Editar terraform.tfvars con las URLs reales de tus servicios
```

### 3. Service Environment Files
```bash
# Auth Service (IMPORTANTE: Genera JWT_SECRET)
cp cat-house-backend/auth-service/.env.example cat-house-backend/auth-service/.env

# Catalog Service
cp cat-house-backend/catalog-service/.env.example cat-house-backend/catalog-service/.env

# Installation Service
cp cat-house-backend/installation-service/.env.example cat-house-backend/installation-service/.env

# Proxy Service
cp cat-house-backend/proxy-service/.env.example cat-house-backend/proxy-service/.env
```

### 4. Genera JWT Secret (Auth Service)
```bash
# Opción 1: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Opción 2: PowerShell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

Copia el resultado y pégalo en `cat-house-backend/auth-service/.env`:
```
JWT_SECRET=el-valor-generado-aqui
```

### 5. Database URL (Todos los servicios)
En cada archivo `.env`, actualiza:
```
DATABASE_URL=postgresql+asyncpg://usuario:password@host.neon.tech/neondb
```

---

## ⚠️ Verificación antes de desplegar

- [ ] `aws configure` ejecutado
- [ ] `terraform.tfvars` creado con URLs reales
- [ ] Todos los `.env` creados
- [ ] `JWT_SECRET` generado en auth-service
- [ ] `DATABASE_URL` configurado en todos los servicios
- [ ] `DEBUG=False` en producción

---

📖 **Guía completa:** Ver [CONFIGURATION-GUIDE.md](./CONFIGURATION-GUIDE.md)
