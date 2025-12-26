# Epic 5: Testing & Deployment Readiness

**Goal:** Containerize the application with production-ready Docker image, set up CI/CD pipeline for automated testing and deployment, and prepare production deployment configuration with AWS infrastructure.

**Prerequisites (Already Completed):**
- ✅ Testing framework (pytest, pytest-asyncio, pytest-cov) configured in Epic 1
- ✅ Unit tests implemented for all business logic (tests/unit/)
- ✅ Integration tests implemented for all command actions (tests/integration/)
- ✅ Development Docker environment with hot-reload (Dockerfile.dev, docker-compose.dev.yml)

**This Epic Delivers:**
- Production Docker image with multi-stage build and security hardening
- AWS infrastructure as code with Terraform (ECS Fargate, ALB, ECR, Secrets Manager)
- Automated CI/CD pipeline with GitHub Actions for testing and deployment

## Story 5.0: AWS Account & Prerequisites Setup (Manual)

As a **DevOps engineer**,  
I want **AWS account and local tools configured**,  
so that **I can execute Terraform and deploy to AWS in subsequent stories**.

**Acceptance Criteria:**
1. Create AWS account at https://aws.amazon.com/ with payment method verified
2. Create IAM user "github-actions-user" with programmatic access and policies:
   - AmazonEC2ContainerRegistryPowerUser (for ECR image push/pull)
   - AmazonECS_FullAccess (for ECS deployments)
   - SecretsManagerReadWrite (for Secrets Manager access)
3. Save IAM user credentials: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
4. Install AWS CLI locally (verify with: aws --version)
5. Install Terraform locally (verify with: terraform --version)
6. Configure AWS credentials locally: aws configure (enter Access Key, Secret Key, Region: us-east-1)
7. Register domain or configure Route 53 hosted zone for api.gamificator.click
8. Configure GitHub repository secrets (Settings → Secrets and variables → Actions):
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - AWS_REGION (us-east-1)
9. Create docs/aws-setup-guide.md documenting the setup process with screenshots
10. Verify setup: aws sts get-caller-identity (should return IAM user details)

**Estimated Time:** 30-40 minutes (one-time setup)  
**Type:** Manual (human-executed)  
**Blocks:** Story 5.2, 5.3  
**Cost:** AWS Free Tier eligible (first 12 months)

## Story 5.1: Production Docker Image & Multi-Stage Build

As a **DevOps engineer**,  
I want **an optimized production Docker image using multi-stage builds**,  
so that **the final image is small (~150MB), secure, and production-ready**.

**Acceptance Criteria:**
1. Create Dockerfile with two stages: builder (installs deps) and runtime (minimal)
2. Builder stage installs gcc and compiles Python packages
3. Runtime stage copies only compiled dependencies and application code
4. Final image runs as non-root user (appuser) for security
5. Production command uses gunicorn with uvicorn workers (2 workers for 0.25 vCPU)
6. Image successfully builds with: docker build -t task-api:latest .
7. Test image locally: docker run -p 8000:8000 --env-file .env.prod task-api:latest
8. Document build process in README.md

## Story 5.2: AWS Infrastructure with Terraform

As a **DevOps engineer**,  
I want **AWS infrastructure defined as code using Terraform**,  
so that **infrastructure is reproducible, version-controlled, and easy to replicate for staging/production**.

**Acceptance Criteria:**
1. Create terraform/ directory with main.tf, variables.tf, outputs.tf, and provider.tf files
2. Define AWS provider configuration (region: us-east-1)
3. Create ECR repository resource for Docker images (task-manager-api)
4. Define ECS Fargate cluster, task definition (0.25 vCPU, 512MB RAM), and service (desired_count: 2)
5. Configure Application Load Balancer with target group pointing to ECS tasks
6. Create Route 53 A record for api.gamificator.click pointing to ALB
7. Request/validate ACM certificate for api.gamificator.click with DNS validation
8. Configure ALB listener for HTTPS (port 443) using ACM certificate
8. Configure security groups: ALB allows 443 from internet, ECS tasks allow 8000 from ALB only
9. Create AWS Secrets Manager secrets for DATABASE_URL, ADMIN_API_KEY, and service API keys (with support for current/previous keys during rotation - post-MVP feature)
10. Configure security groups: ALB allows 443 from internet, ECS tasks allow 8000 from ALB only
11. Document Terraform commands in README: terraform init, plan, apply
12. Add terraform.tfvars.example with required variables

## Story 5.3: CI/CD Pipeline with GitHub Actions

As a **DevOps engineer**,  
I want **an automated CI/CD pipeline that deploys to ECS Fargate on every merge to main**,  
so that **testing and deployment are automated with zero manual intervention**.

**Acceptance Criteria:**
1. Create .github/workflows/deploy-ecs.yml workflow file
2. Workflow triggers on push to main and pull_request events
3. Test job runs: ruff linting, mypy type checking, pytest unit tests with coverage report
4. Build-and-push job (only on main): builds Docker image, tags with git SHA, pushes to ECR
5. Deploy job (only on main): updates ECS task definition with new image, triggers service update
6. Migration job (only on main): runs alembic upgrade head via ECS RunTask before deployment
7. Configure GitHub secrets: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
8. Workflow uses rolling deployment strategy (ECS replaces tasks one by one)
9. Deployment waits for service stability before marking success
10. Document pipeline in README with badge showing build status

## Story 5.4: Production Database & Secrets Configuration

As a **DevOps engineer**,  
I want **a production PostgreSQL database provisioned and all secrets configured**,  
so that **the API is fully functional and accessible from internet with real data persistence**.

**Acceptance Criteria:**
1. Create Neon PostgreSQL database at https://neon.tech:
   - Sign up for Neon account (Free tier: 0.5GB storage, shared compute)
   - Create new project: "task-manager-prod"
   - Create database: "taskdb"
   - Note connection string with pooled connection (uses pgbouncer)
2. Configure Neon database settings:
   - Enable connection pooling for better performance with Fargate
   - Note: Connection string format: postgresql://user:pass@ep-xxx.region.aws.neon.tech/taskdb?sslmode=require
   - Keep Neon dashboard credentials secure
3. Populate AWS Secrets Manager with production values:
   - prod/task-api/database-url: Use Neon pooled connection string
   - prod/task-api/admin-key: Generate secure random key (openssl rand -hex 32)
   - prod/task-api/service-keys: JSON with initial service keys {"cat-house": "generated-key-1"}
4. Update ECS task definition in Terraform to load secrets from Secrets Manager
5. Run initial database migration via ECS RunTask: alembic upgrade head
6. Verify database connectivity from ECS task: aws ecs execute-command (test connection)
7. Test admin endpoint from internet: curl -H "X-API-Key: $ADMIN_KEY" https://api.gamificator.click/admin/keys
8. Test task creation via command endpoint with valid service key
9. Document Neon connection details and backup strategy in README
10. Add migration rollback plan in case of issues

**Why Neon for Production (MVP):**
- Cost: $0 (Free tier sufficient for initial launch)
- Pros: Serverless PostgreSQL, auto-scaling, branching, point-in-time restore
- Cons: 0.5GB storage limit (upgrade to paid ~$19/month when needed)
- Migration path: Easy to migrate to RDS later if needed

**Post-Deployment Verification Checklist:**
- [ ] API health check: curl https://api.gamificator.click/health
- [ ] Admin endpoint: curl -H "X-API-Key: $ADMIN_KEY" https://api.gamificator.click/admin/keys
- [ ] Create task: curl -X POST -H "X-API-Key: $SERVICE_KEY" https://api.gamificator.click/cmd/tasks.create -d '{"name":"test"}'
- [ ] List tasks: curl -H "X-API-Key: $SERVICE_KEY" https://api.gamificator.click/cmd/tasks.list
- [ ] Get stats: curl -H "X-API-Key: $SERVICE_KEY" https://api.gamificator.click/cmd/stats.get
- [ ] Verify HTTPS certificate valid (browser shows padlock)
- [ ] Check CloudWatch logs for any errors

---
