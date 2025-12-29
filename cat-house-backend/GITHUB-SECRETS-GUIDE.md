# Cat House - GitHub Secrets Configuration Guide

**Last Updated:** December 29, 2025  
**Purpose:** Centralized documentation for all GitHub Secrets used in Cat House deployment

---

## Overview

Cat House uses **GitHub Secrets exclusively** for managing sensitive credentials across all environments. Secrets are injected into ECS task definitions during deployment via GitHub Actions workflows.

**Benefits:**
- ✅ Single source of truth for credentials
- ✅ No additional AWS Secrets Manager costs
- ✅ Simple rotation process
- ✅ Centralized in GitHub repository settings

---

## Required GitHub Secrets

Navigate to: `https://github.com/[your-username]/cat-house/settings/secrets/actions`

### 1. AWS Access Credentials

| Secret Name | Description | How to Generate |
|------------|-------------|-----------------|
| `AWS_ACCESS_KEY_ID` | AWS IAM access key for GitHub Actions | Create IAM user `github-actions-cathouse` with ECS/ECR permissions |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key | Generated with access key above |

**IAM Permissions Required:**
- `AmazonECS_FullAccess`
- `AmazonEC2ContainerRegistryPowerUser`
- `CloudWatchLogsFullAccess`

---

### 2. Database Connection Strings

| Secret Name | Description | Format | Source |
|------------|-------------|--------|--------|
| `NEON_TEST_DATABASE_URL` | Development branch for CI tests | `postgresql://user:pass@host/db` | Neon development branch |
| `NEON_STAGING_DATABASE_URL` | Staging environment database | `postgresql://user:pass@host/db` | Neon staging branch |
| `NEON_PRODUCTION_DATABASE_URL` | Production environment database | `postgresql://user:pass@host/db` | Neon main branch |

**Format Examples:**
```
# For asyncpg (runtime)
postgresql+asyncpg://user:password@host.region.aws.neon.tech/database

# For psycopg2 (migrations)
postgresql://user:password@host.region.aws.neon.tech/database?sslmode=require
```

**Get from Neon Console:**
1. Go to https://console.neon.tech/
2. Select your project
3. Select branch (development/staging/main)
4. Click "Connection Details"
5. Copy the connection string

---

### 3. Application Security Secrets

| Secret Name | Description | How to Generate | Min Length |
|------------|-------------|-----------------|------------|
| `JWT_SECRET` | Secret key for JWT token signing | `openssl rand -base64 32` | 32 chars |
| `ENCRYPTION_KEY` | Encryption key for sensitive data | `openssl rand -hex 16` | Exactly 32 chars |

**Generate Secure Values:**

```powershell
# Generate JWT_SECRET (minimum 32 characters)
openssl rand -base64 32

# Generate ENCRYPTION_KEY (exactly 32 characters)
openssl rand -hex 16
```

**⚠️ CRITICAL:**
- Never commit these values to git
- Rotate every 90 days
- Different values for staging/production (recommended)

---

### 4. CloudFront Distribution IDs

| Secret Name | Description | Source |
|------------|-------------|--------|
| `CLOUDFRONT_STAGING_ID` | CloudFront distribution for staging | Terraform output after first deployment |
| `CLOUDFRONT_PRODUCTION_ID` | CloudFront distribution for production | Terraform output after first deployment |

**Get After Terraform Deployment:**
```powershell
cd cat-house-backend/terraform
terraform output cloudfront_distribution_id
```

---

## How Secrets Are Used

### CI/CD Workflow Integration

Secrets are injected into workflows in `.github/workflows/`:

```yaml
# Example: deploy-production.yml
- name: Deploy to ECS
  env:
    DATABASE_URL: ${{ secrets.NEON_PRODUCTION_DATABASE_URL }}
    JWT_SECRET: ${{ secrets.JWT_SECRET }}
    ENCRYPTION_KEY: ${{ secrets.ENCRYPTION_KEY }}
  run: |
    # Update ECS task definition with secrets
    aws ecs update-service ...
```

### Terraform Variable Passing

During deployment, GitHub Actions passes secrets to Terraform:

```powershell
terraform apply \
  -var="database_url=${{ secrets.NEON_PRODUCTION_DATABASE_URL }}" \
  -var="jwt_secret=${{ secrets.JWT_SECRET }}" \
  -var="encryption_key=${{ secrets.ENCRYPTION_KEY }}"
```

### ECS Task Definitions

Terraform injects secrets as environment variables in ECS containers:

```hcl
# terraform/ecs.tf
environment = [
  {
    name  = "DATABASE_URL"
    value = var.database_url  # From GitHub Secret
  },
  {
    name  = "JWT_SECRET"
    value = var.jwt_secret    # From GitHub Secret
  }
]
```

---

## Initial Setup

### Step 1: Add Secrets to GitHub

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret from the table above

### Step 2: Verify Secrets

Create a test workflow to verify secrets are accessible:

```yaml
name: Test Secrets
on: workflow_dispatch

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Check secrets exist
        run: |
          echo "AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID != '' }}"
          echo "JWT_SECRET: ${{ secrets.JWT_SECRET != '' }}"
          echo "DATABASE_URL: ${{ secrets.NEON_PRODUCTION_DATABASE_URL != '' }}"
```

---

## Secret Rotation

### When to Rotate
- **Immediately:** If credentials are exposed/committed to git
- **Every 90 days:** Regular security practice
- **After team changes:** When team members leave

### Rotation Process

#### 1. Generate New Values

```powershell
# New JWT secret
openssl rand -base64 32

# New encryption key
openssl rand -hex 16
```

#### 2. Update GitHub Secrets

1. Go to repository **Settings** → **Secrets**
2. Click on secret name (e.g., `JWT_SECRET`)
3. Click **Update**
4. Paste new value
5. Save

#### 3. Trigger Deployment

```powershell
# Push a commit or manually trigger workflow
git commit --allow-empty -m "Rotate secrets"
git push origin master
```

#### 4. Verify Services

```powershell
# Check ECS services are healthy
aws ecs describe-services --cluster cat-house-production --services auth-service

# Test authentication endpoint
curl https://chapi.gamificator.click/api/v1/health
```

---

## Troubleshooting

### Secret Not Found Error

**Error:** `Error: Required variable not set: database_url`

**Solution:**
1. Verify secret exists in GitHub: Settings → Secrets
2. Check secret name matches exactly (case-sensitive)
3. Verify workflow has correct syntax: `${{ secrets.SECRET_NAME }}`

### Invalid Secret Format

**Error:** `ValueError: Invalid PostgreSQL URL format`

**Solution:**
1. Check connection string format:
   - Should start with `postgresql://` or `postgresql+asyncpg://`
   - Include username, password, host, and database
   - Example: `postgresql://user:pass@host.neon.tech/dbname`

### Encryption Key Length Error

**Error:** `ValueError: Encryption key must be exactly 32 characters`

**Solution:**
```powershell
# Generate exactly 32 characters
openssl rand -hex 16  # This outputs 32 hex characters
```

### GitHub Actions Can't Access Secrets

**Error:** Secrets are empty in workflow

**Solution:**
1. Check repository permissions
2. Verify secrets are repository secrets, not environment secrets
3. Check workflow has correct syntax
4. Re-create secret if needed

---

## Security Best Practices

### ✅ DO

- Use strong, randomly generated secrets
- Rotate secrets regularly (90 days)
- Use different secrets for staging/production
- Remove old secrets after rotation
- Audit secret access logs in GitHub
- Use GitHub environments for production (requires approval)

### ❌ DON'T

- Never commit secrets to git (even in .env.example)
- Don't share secrets via Slack/email
- Don't use same secret across environments
- Don't use predictable secrets ("changeme", "password123")
- Don't log secret values in CI/CD outputs
- Don't store secrets in code comments

---

## Migration from AWS Secrets Manager

If you previously used AWS Secrets Manager:

### 1. Export Current Secrets

```powershell
# Get current database URL
aws secretsmanager get-secret-value \
  --secret-id cat-house/production/database-url \
  --query SecretString \
  --output text
```

### 2. Add to GitHub Secrets

Follow the "Initial Setup" section above.

### 3. Update Terraform

Already completed - `terraform/ecs.tf` now uses environment variables instead of `secrets` blocks.

### 4. Clean Up AWS Secrets Manager

```powershell
# Delete old secrets (optional - only after verifying GitHub Secrets work)
aws secretsmanager delete-secret \
  --secret-id cat-house/production/database-url \
  --force-delete-without-recovery
```

---

## Reference

### Workflows Using Secrets

| Workflow | Secrets Used |
|----------|--------------|
| `backend-ci.yml` | `NEON_TEST_DATABASE_URL` |
| `build-images.yml` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` |
| `deploy-staging.yml` | `AWS_*`, `NEON_STAGING_DATABASE_URL`, `JWT_SECRET`, `ENCRYPTION_KEY`, `CLOUDFRONT_STAGING_ID` |
| `deploy-production.yml` | `AWS_*`, `NEON_PRODUCTION_DATABASE_URL`, `JWT_SECRET`, `ENCRYPTION_KEY`, `CLOUDFRONT_PRODUCTION_ID` |

### Related Documentation

- [Deployment Guide](deployment-guide.md)
- [Database Setup](database-setup.md)
- [CI/CD Pipeline Story](../stories/1.5.cicd-pipeline-setup.md)

---

**Document Owner:** DevOps Team  
**Review Schedule:** Every 90 days or when secrets are rotated
