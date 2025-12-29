# Cat House - Deployment Guide

**Last Updated:** December 28, 2025  
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
- [x] Code pushed to master branch
- [x] CI/CD workflows created in `.github/workflows/`
- [x] Production-ready logging configured (JSON + correlation IDs)
- [x] Terraform infrastructure code created
- [x] Neon database branches created (main, staging, development)

### 📋 Required Accounts & Access
- [x] GitHub account with repository access
- [x] AWS account with IAM user created (`github-actions-cathouse`)
- [x] Neon account with project and branches
- [ ] AWS CLI installed and configured locally
- [ ] Terraform installed (v1.0+)

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
⚠️ JWT_SECRET                     (generate with: openssl rand -base64 32)
⚠️ ENCRYPTION_KEY                 (generate with: openssl rand -hex 32)

# CloudFront (added after Terraform)
⏳ CLOUDFRONT_STAGING_ID          (will be added after Terraform)
⏳ CLOUDFRONT_PRODUCTION_ID       (will be added after Terraform)
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
# - Default region: us-east-1
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
aws_region = "us-east-1"
environment = "staging"

# Service URLs will be updated after ECS deployment
auth_service_url = "http://placeholder:8005"
catalog_service_url = "http://placeholder:8002"
installation_service_url = "http://placeholder:8003"
proxy_service_url = "http://placeholder:8004"
health_aggregator_url = "http://placeholder:8000"
"@ | Out-File -FilePath terraform.tfvars -Encoding utf8
```

### 4. Plan Deployment (Review Changes)

```powershell
terraform plan -var-file="terraform.tfvars"
```

**Review Output:**
- ECR repositories (5) will be created
- ECS cluster will be created
- ECS task definitions (5) will be created
- ECS services (5) will be created
- S3 bucket for frontend will be created
- CloudFront distribution will be created
- CloudWatch log groups (5) will be created
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
Code Change → Push to GitHub → CI Tests → Build Docker Images → Push to ECR → Deploy to ECS → Verify Health
```

### 1. Build and Push Docker Images Manually (First Time)

Since workflows need images to exist in ECR first:

```powershell
# Get ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin [AWS_ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com

# Build and push auth-service
cd "cat-house-backend/auth-service"
docker build -t cat-house/auth-service:latest .
docker tag cat-house/auth-service:latest [ECR_URL]/cat-house/auth-service:latest
docker push [ECR_URL]/cat-house/auth-service:latest

# Repeat for other services:
# - catalog-service
# - installation-service
# - proxy-service
# - health-aggregator
```

### 2. Update ECS Services with New Images

```powershell
aws ecs update-service `
  --cluster cat-house-staging `
  --service cat-house-staging-auth-service `
  --force-new-deployment `
  --region us-east-1

# Repeat for all 5 services
```

### 3. Run Database Migration

```powershell
# Get auth-service task definition
aws ecs run-task `
  --cluster cat-house-staging `
  --task-definition cat-house-staging-auth-service `
  --launch-type FARGATE `
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" `
  --overrides '{"containerOverrides":[{"name":"auth-service","command":["alembic","upgrade","head"]}]}' `
  --region us-east-1
```

### 4. Test Automated Workflows

**Create a feature branch:**
```powershell
cd "c:\Users\Rog\OneDrive - Universidad de Antioquia\Main\Empresas\Micro SaaS\My cat manager"
git checkout -b feature/test-ci
```

**Make a small change:**
```powershell
# Edit any file (e.g., README.md)
git add .
git commit -m "Test CI/CD pipeline"
git push -u origin feature/test-ci
```

**Create Pull Request:**
- Go to GitHub: https://github.com/juliangdeveloper/cat-house/pulls
- Click "New pull request"
- Select `feature/test-ci` → `master`
- Create PR

**Watch Workflows Run:**
- Backend CI will run tests and linting
- Frontend CI will run tests and build
- Both must pass before merge

---

## Verification & Testing

### 1. Verify ECS Services are Running

```powershell
aws ecs list-services --cluster cat-house-staging --region us-east-1
aws ecs describe-services --cluster cat-house-staging --services [service-name] --region us-east-1
```

**Check:**
- `runningCount` should equal `desiredCount`
- `deployments` should show ACTIVE status

### 2. Check CloudWatch Logs

```powershell
# View logs for auth-service
aws logs tail /ecs/cat-house/staging/auth-service --follow --region us-east-1
```

**Verify:**
- JSON formatted logs (production mode)
- Trace IDs present (X-Trace-ID)
- No errors during startup

### 3. Test Service Health Endpoints

```powershell
# Get service public IP (from ECS task)
$TASK_ARN = aws ecs list-tasks --cluster cat-house-staging --service-name cat-house-staging-auth-service --query 'taskArns[0]' --output text
$TASK_DETAILS = aws ecs describe-tasks --cluster cat-house-staging --tasks $TASK_ARN --query 'tasks[0].attachments[0].details' --output json
# Extract public IP from network interface

# Test health endpoint
curl http://[PUBLIC_IP]:8005/api/v1/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "auth-service",
  "timestamp": "2025-12-28T...",
  "database": "connected"
}
```

### 4. Test API Gateway (when configured)

```powershell
curl https://api-staging.gamificator.click/health
curl https://api-staging.gamificator.click/api/v1/auth/health
```

### 5. Test Frontend Deployment

```powershell
# Get CloudFront URL
terraform output cloudfront_domain_name

# Visit in browser
start https://[cloudfront-url]
```

### 6. Monitor Deployment in GitHub Actions

- Go to: https://github.com/juliangdeveloper/cat-house/actions
- Check workflow runs
- Verify all steps pass

---

## Troubleshooting

### Issue: Terraform Apply Fails

**Error:** `Error creating ECR repository`
```powershell
# Check if repositories already exist
aws ecr describe-repositories --region us-east-1

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

1. **Configure Custom Domain (Optional):**
   - Request ACM certificate for `api.gamificator.click`
   - Update API Gateway custom domain
   - Configure Route 53 DNS

2. **Set Up Monitoring:**
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
