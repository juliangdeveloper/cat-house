# 👥 Guía para Colaboradores - Cat House

## 🎯 Resumen de Permisos

Como colaborador de este proyecto, tienes los siguientes permisos:

### ✅ Puedes:
- Trabajar en la rama `dev/julianclawd`
- Crear commits en tu rama
- Crear Pull Requests hacia `main`
- Ver todo el código del repositorio
- Clonar y hacer fork del repositorio

### ❌ No puedes:
- Hacer push directo a `main`
- Hacer merge de PRs (requiere aprobación del owner)
- Modificar configuraciones de deployment
- Ejecutar workflows de GitHub Actions en `main`

## 🚀 Workflow de Trabajo

### 1. **Configuración Inicial**

```bash
# Clonar el repositorio
git clone https://github.com/juliangdeveloper/cat-house.git
cd cat-house

# Cambiar a tu rama de desarrollo
git checkout dev/julianclawd
```

### 2. **Trabajando en Nuevas Features**

```bash
# Asegúrate de estar en tu rama
git checkout dev/julianclawd

# Actualiza tu rama con los últimos cambios de main
git fetch origin
git merge origin/main

# Haz tus cambios
# ... edita archivos ...

# Commit y push
git add .
git commit -m "feat: descripción del cambio"
git push origin dev/julianclawd
```

### 3. **Crear Pull Request**

1. Ve a GitHub: https://github.com/juliangdeveloper/cat-house
2. Click en "Pull requests" → "New pull request"
3. Base: `main` ← Compare: `dev/julianclawd`
4. Describe tus cambios detalladamente
5. Asigna el PR a @juliangdeveloper para revisión

### 4. **Proceso de Revisión**

- El owner (@juliangdeveloper) revisará tu código
- Puede solicitar cambios
- Una vez aprobado, el owner hará el merge
- Tu rama se actualizará automáticamente

## 📋 Mejores Prácticas

### Commits
- Usa mensajes descriptivos
- Formato recomendado: `tipo: descripción`
  - `feat:` nuevas características
  - `fix:` correcciones de bugs
  - `docs:` documentación
  - `refactor:` refactorización de código
  - `test:` añadir o modificar tests

### Pull Requests
- Un PR por feature/fix
- Incluye descripción detallada
- Referencia issues relacionados (#número)
- Asegúrate de que los tests pasen

### Comunicación
- Comenta en los PRs si necesitas feedback
- Usa issues para reportar bugs o proponer features
- Mantén actualizada tu rama con `main` regularmente

## 🔧 Desarrollo Local

### Backend Services
```bash
cd cat-house-backend
docker-compose up -d
```

### Frontend
```bash
cd frontend
npm install
npm start
```

### Tests
```bash
# Backend
cd cat-house-backend/auth-service
pytest

# Frontend
cd frontend
npm test
```

## 📞 Soporte

Si tienes dudas o problemas:
1. Revisa la documentación en `/docs`
2. Crea un issue en GitHub
3. Contacta a @juliangdeveloper

## 🔒 Seguridad

**NUNCA** commitees:
- Credenciales o secrets
- API keys
- Contraseñas
- Tokens de acceso

Usa variables de entorno y archivos `.env` (que están en `.gitignore`)
