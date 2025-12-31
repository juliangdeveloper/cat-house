# Cat House - Deployment Guide

**Last Updated:** December 31, 2025  
**Story Reference:** [Story 1.5 - CI/CD Pipeline Setup](../stories/1.5.cicd-pipeline-setup.md)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [GitHub Configuration](#github-configuration)
3. [AWS Infrastructure Setup](#aws-infrastructure-setup)
4. [Terraform Deployment](#terraform-deployment)
5. [First Deployment](#first-deployment)
6. [Verification & Testing](#verification--testing)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### ✅ Completed
- [x] GitHub repository created: https://github.com/juliangdeveloper/cat-house
- [x] Code pushed to develop/main branches
- [x] Consolidated CI/CD pipeline deployed (staging-pipeline.yml)
- [x] Production-ready logging configured (JSON + X-Trace-ID)
- [x] Terraform infrastructure deployed (ALB-only architecture)
- [x] Neon database branches: production, staging, development, test
- [x] Custom domains configured (chs.gamificator.click, chapp.gamificator.click)

### 📋 Required Accounts & Access
- [x] GitHub account with repository access
- [x] AWS account with IAM user created (`cathouse-deployer`)
- [x] Neon account with project and branches
- [x] AWS CLI installed and configured locally
- [x] Terraform installed (v1.0+)

---

## GitHub Configuration

### 1. Repository Secrets Configured ✅

Navigate to: https://github.com/juliangdeveloper/cat-house/settings/secrets/actions

**Current Secrets:**
```
# AWS Access
✅ AWS_ACCESS_KEY_ID              (from AWS IAM)
✅ AWS_SECRET_ACCESS_KEY          (from AWS IAM)

# Database URLs (from Neon)
✅ NEON_TEST_DATABASE_URL         (development branch - for CI tests)
✅ NEON_STAGING_DATABASE_URL      (staging branch - for staging deploy)
✅ NEON_PRODUCTION_DATABASE_URL   (main branch - for production deploy)

# Application Secrets
✅ JWT_SECRET                     (configured)
✅ ENCRYPTION_KEY                 (configured)

# CloudFront Distribution IDs
✅ CLOUDFRONT_STAGING_ID          (E2P1VZI2R1DYQF)
✅ CLOUDFRONT_PRODUCTION_ID       (ECZ0AQQPGNTPJ)
```

**Generate Secure Secrets:**
```powershell
# Generate JWT_SECRET (minimum 32 characters)
openssl rand -base64 32

# Generate ENCRYPTION_KEY (exactly 32 characters)
openssl rand -hex 16
```

Add these to GitHub Secrets before first deployment.

### 2. GitHub Environments ✅

Navigate to: https://github.com/juliangdeveloper/cat-house/settings/environments

**Environments:**
- ✅ `staging` - No protection rules
- ✅ `production` - Required reviewers enabled

---

## AWS Infrastructure Setup

### 1. Configure AWS CLI Locally

```powershell
# Install AWS CLI (if not installed)
winget install Amazon.AWSCLI

# Configure credentials
aws configure
# Enter:
# - AWS Access Key ID: [same as GitHub secret]
# - AWS Secret Access Key: [same as GitHub secret]
# - Default region: sa-east-1
# - Default output: json
```

### 2. Verify AWS Access

```powershell
# Verify credentials
aws sts get-caller-identity

# Should output your AWS account ID and IAM user
```

**Note:** Database credentials, JWT secrets, and encryption keys are managed via GitHub Secrets and injected during deployment. No AWS Secrets Manager configuration required.

---

## Terraform Deployment

### 1. Navigate to Terraform Directory

```powershell
cd "c:\Users\Rog\OneDrive - Universidad de Antioquia\Main\Empresas\Micro SaaS\My cat manager\cat-house-backend\terraform"
```

### 2. Initialize Terraform

```powershell
terraform init
```

**Expected Output:**
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
Terraform has been successfully initialized!
```

### 3. Create Terraform Variables File

Create `terraform.tfvars`:

```powershell
@"
aws_region = "sa-east-1"
environment = "staging"
certificate_arn = "arn:aws:acm:us-east-1:578492750346:certificate/25745008-889d-4163-bba2-d71065c1b353"
hosted_zone_id = "Z060186227WPZP8YF5ZX8"
domain_name = "chs.gamificator.click"
app_prefix = "cat-house"
"@ | Out-File -FilePath terraform.tfvars -Encoding utf8
```

### 4. Plan Deployment (Review Changes)

```powershell
terraform plan -var-file="terraform.tfvars"
```

**Review Output:**
- ECR repositories (4) will be created
- ECS cluster will be created
- ECS task definitions (4) will be created
- ECS services (4) will be created
- Application Load Balancer will be created
- S3 bucket for frontend will be created
- CloudFront distribution with custom domain will be created
- CloudWatch log groups (4) will be created
- IAM roles and policies will be created

### 5. Apply Terraform (Create Infrastructure)

```powershell
terraform apply -var-file="terraform.tfvars"
```

Type `yes` when prompted.

**⏱️ Expected Duration:** 5-10 minutes

### 6. Capture Terraform Outputs

After successful deployment:

```powershell
# Get ECR repository URLs
terraform output ecr_repository_urls

# Get ALB DNS name
terraform output alb_dns_name

# Get CloudFront distribution ID
terraform output cloudfront_distribution_id

# Get CloudFront domain name
terraform output cloudfront_domain_name

# Get ECS cluster name
terraform output ecs_cluster_name
```

**Save these values!** You'll need them for:
- CloudFront IDs → GitHub Secrets
- ECR URLs → Docker image push
- ECS cluster → Deployment workflows

### 7. Add CloudFront IDs to GitHub Secrets

```
CLOUDFRONT_STAGING_ID = [distribution ID from terraform output]
CLOUDFRONT_PRODUCTION_ID = [will be same for now, or deploy prod separately]
```

---

## First Deployment

### Deployment Flow Overview

```
Push to develop → Test (4 services) → Build → Migrate → Deploy Backend → Deploy Frontend
```

### Automated Deployment via GitHub Actions

El pipeline consolidado `staging-pipeline.yml` maneja todo automáticamente:

```powershell
# Push to develop branch triggers full pipeline
git checkout develop
git add .
git commit -m "Deploy to staging"
git push origin develop
```

**Pipeline ejecuta:**
1. **Test:** pytest + black + pylint en 4 servicios
2. **Build:** Docker images → ECR con tags :staging y :sha
3. **Migrate:** Alembic migrations en auth-service
4. **Deploy Backend:** 4 servicios a ECS con secrets injection
5. **Deploy Frontend:** Expo web → S3 → CloudFront invalidation

### Production Deployment

```powershell
# 1. Merge develop to main (triggers retag workflow)
git checkout main
git merge develop
git push origin main

# 2. Manually trigger production deployment
# Go to: https://github.com/juliangdeveloper/cat-house/actions
# Run: deploy-production.yml (requires approval)
```

### Manual Database Migration (if needed)

```powershell
# Migrations run automatically via GitHub Actions
# Manual execution (solo si es necesario):
aws ecs run-task `
  --cluster cat-house-staging `
  --task-definition cat-house-staging-auth-service `
  --launch-type FARGATE `
  --overrides '{"containerOverrides":[{"name":"auth-service","command":["alembic","upgrade","head"]}]}' `
  --region sa-east-1
```

---

## Verification & Testing

### 1. Verify ECS Services are Running

```powershell
aws ecs list-services --cluster cat-house-staging --region sa-east-1
aws ecs describe-services --cluster cat-house-staging --services cat-house-staging-auth-service --region sa-east-1
```

**Check:**
- `runningCount` should equal `desiredCount`
- `deployments` should show ACTIVE status

### 2. Check CloudWatch Logs

```powershell
# View logs for auth-service
aws logs tail /ecs/cat-house/staging/auth-service --follow --region sa-east-1
```

**Verify:**
- JSON formatted logs (production mode)
- Trace IDs present (X-Trace-ID)
- No errors during startup

### 3. Test ALB Health Endpoints

```powershell
# Test ALB health check
curl http://cat-house-staging-alb-1968126506.sa-east-1.elb.amazonaws.com/health

# Test service-specific endpoints
curl http://cat-house-staging-alb-1968126506.sa-east-1.elb.amazonaws.com/api/v1/auth/health
curl http://cat-house-staging-alb-1968126506.sa-east-1.elb.amazonaws.com/api/v1/catalog/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "auth-service",
  "timestamp": "2025-12-31T...",
  "database": "connected"
}
```

### 4. Test Frontend Deployment

```powershell
# Staging frontend
start https://chs.gamificator.click

# Production frontend
start https://chapp.gamificator.click
```

### 5. Monitor Deployment in GitHub Actions

- Go to: https://github.com/juliangdeveloper/cat-house/actions
- Workflow: `staging-pipeline.yml` (auto-deploy on develop)
- Workflow: `deploy-production.yml` (manual approval required)
- Verify all 5 jobs pass: test → build → migrate → deploy-backend → deploy-frontend

---

## Troubleshooting

### Issue: Terraform Apply Fails

**Error:** `Error creating ECR repository`
```powershell
# Check if repositories already exist
aws ecr describe-repositories --region sa-east-1

# If exists, import to Terraform state
terraform import aws_ecr_repository.services["auth-service"] auth-service
```

### Issue: ECS Tasks Not Starting

**Check:**
```powershell
# Describe service
aws ecs describe-services --cluster cat-house-staging --services cat-house-staging-auth-service

# Check stopped tasks
aws ecs list-tasks --cluster cat-house-staging --desired-status STOPPED
aws ecs describe-tasks --cluster cat-house-staging --tasks [task-arn]
```

**Common Causes:**
- Missing or invalid DATABASE_URL secret
- Docker image not found in ECR
- Insufficient CPU/memory
- Security group blocking traffic

### Issue: Health Checks Failing

**Check logs:**
```powershell
aws logs tail /ecs/cat-house/staging/auth-service --since 10m
```

**Common Causes:**
- Database connection issues (check Neon URL)
- Port mismatch in health check
- Container failing to start

### Issue: GitHub Actions Workflows Failing

**Check:**
- Secrets are correctly configured
- AWS credentials have correct permissions
- ECR repositories exist
- Neon database is accessible

**View workflow logs:**
- Go to Actions tab in GitHub
- Click on failed workflow
- Expand failed steps

### Issue: CloudFront Not Updating

```powershell
# Create cache invalidation manually
aws cloudfront create-invalidation `
  --distribution-id [DISTRIBUTION_ID] `
  --paths "/*"
```

---

## Next Steps After Successful Deployment

1. **Set Up Monitoring:**
   - Configure CloudWatch alarms
   - Set up SNS notifications
   - Enable X-Ray tracing

3. **Production Deployment:**
   - Repeat Terraform deployment with `environment = "production"`
   - Configure production branch protection
   - Test manual approval workflow

4. **Documentation:**
   - Document API endpoints
   - Create runbook for common tasks
   - Update architecture diagrams

---

## Useful Commands Reference

```powershell
# View all ECS services
aws ecs list-services --cluster cat-house-staging

# Force new deployment
aws ecs update-service --cluster cat-house-staging --service [service-name] --force-new-deployment

# View CloudWatch logs
aws logs tail /ecs/cat-house/staging/[service-name] --follow

# Check ECR images
aws ecr list-images --repository-name cat-house/auth-service

# Describe CloudFront distribution
aws cloudfront get-distribution --id [DISTRIBUTION_ID]

# Terraform commands
terraform plan
terraform apply
terraform destroy
terraform output
terraform state list
```

---

## Support & Resources

- **GitHub Repository:** https://github.com/juliangdeveloper/cat-house
- **Story 1.5:** [CI/CD Pipeline Setup](../stories/1.5.cicd-pipeline-setup.md)
- **AWS Console:** https://console.aws.amazon.com/
- **Neon Console:** https://console.neon.tech/
