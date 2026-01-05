# System Architecture

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Applications                          │
│                     (Cat House Platform, Mobile)                     │
│              Each client stores one Service API Key                  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTPS (X-API-Key: sk_prod_xxx)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Route 53 DNS (gamificator.click)                   │
│                  chapi.gamificator.click → ALB IP                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Application Load Balancer (ALB)                         │
│  - ACM Certificate (*.gamificator.click)                             │
│  - Health Check: GET /health (30s interval)                          │
│  - Target Group → ECS Tasks (port 8000)                              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ECS Fargate Cluster                               │
│  ┌──────────────────────┐      ┌──────────────────────┐             │
│  │  Task 1 (0.25 vCPU)  │      │  Task 2 (0.25 vCPU)  │             │
│  │  - FastAPI Container │      │  - FastAPI Container │             │
│  │  - 512MB RAM         │      │  - 512MB RAM         │             │
│  │  - Port 8000         │      │  - Port 8000         │             │
│  └──────────┬───────────┘      └──────────┬───────────┘             │
│             │                             │                          │
│             └──────────────┬──────────────┘                          │
│                            │                                         │
└────────────────────────────┼─────────────────────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │   AWS Secrets Manager        │
              │  - DATABASE_URL              │
              │  - Service API Keys          │
              └──────────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │   Neon PostgreSQL            │
              │   (External Serverless DB)   │
              │   - service_api_keys table   │
              │   - tasks table              │
              │   - Indexes on user_id       │
              └──────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       CI/CD Pipeline (GitHub Actions)                │
│                                                                      │
│  Push to main → Tests → Build → Push to ECR → Deploy to ECS         │
│                                                                      │
│  ┌─────────┐   ┌────────┐   ┌────────┐   ┌──────────────┐          │
│  │ Lint/   │ → │ Build  │ → │ AWS    │ → │ ECS Service  │          │
│  │ Test    │   │ Image  │   │ ECR    │   │ Update       │          │
│  └─────────┘   └────────┘   └────────┘   └──────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

## Development Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Developer Workstation (Windows)                   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────┐         │
│  │               VS Code / IDE                            │         │
│  │  - Edit code in app/ directory                         │         │
│  │  - Changes synced to container via volume mount        │         │
│  └───────────────────────┬────────────────────────────────┘         │
│                          │                                           │
│  ┌───────────────────────▼────────────────────────────────┐         │
│  │           Docker Desktop (Windows)                     │         │
│  │                                                        │         │
│  │  ┌────────────────────────────────────────────────┐   │         │
│  │  │  docker-compose.dev.yml                        │   │         │
│  │  │                                                │   │         │
│  │  │  ┌──────────────────┐  ┌──────────────────┐   │   │         │
│  │  │  │  API Container   │  │  PostgreSQL      │   │   │         │
│  │  │  │  (Hot Reload)    │  │  Container       │   │   │         │
│  │  │  │  - uvicorn       │  │  (Test DB)       │   │   │         │
│  │  │  │  - Port 8888     │  │  - Port 5435     │   │   │         │
│  │  │  │  - Volume: ./app │  │                  │   │   │         │
│  │  │  └──────────────────┘  └──────────────────┘   │   │         │
│  │  └────────────────────────────────────────────────┘   │         │
│  └────────────────────────────────────────────────────────┘         │
│                                                                      │
│  Access: http://localhost:8888/docs (Swagger UI)                    │
└─────────────────────────────────────────────────────────────────────┘
```

## Infrastructure Components

| Component | Purpose | Configuration |
|-----------|---------|---------------|
| **Route 53** | DNS management for gamificator.click | A record: chapi.gamificator.click → ALB |
| **ACM** | SSL/TLS certificate | Wildcard cert for *.gamificator.click |
| **ALB** | Load balancing & SSL termination | Listener: HTTPS (443) → Target Group (8000) |
| **ECS Cluster** | Container orchestration | Fargate launch type, 2 tasks for HA |
| **ECS Task** | Container definition | 0.25 vCPU, 512MB RAM, awsvpc network mode |
| **ECS Service** | Task management & scaling | Rolling deployment, health checks |
| **ECR** | Docker image registry | Private repository: task-manager-api |
| **Secrets Manager** | Secure config storage | DATABASE_URL, Service API Keys |
| **CloudWatch Logs** | Centralized logging | Log group: /ecs/task-api |
| **VPC** | Network isolation | Public subnets for ALB, private for ECS tasks |
| **Security Groups** | Firewall rules | ALB: 443 from 0.0.0.0/0, ECS: 8000 from ALB |

## Deployment Flow

1. **Developer pushes to main** → GitHub webhook triggers Actions workflow
2. **GitHub Actions:**
   - Runs tests (pytest, ruff, mypy)
   - Builds production Docker image
   - Tags image with git SHA and latest
   - Pushes to AWS ECR
3. **GitHub Actions (Deploy job):**
   - Runs database migrations (alembic upgrade head via ECS RunTask)
   - Updates ECS task definition with new image URI
   - Triggers ECS service update (rolling deployment)
4. **ECS Fargate:**
   - Starts new tasks with updated image
   - Waits for health checks to pass (GET /health → 200)
   - Drains connections from old tasks
   - Terminates old tasks
5. **Route 53 + ALB** → Routes traffic to new tasks at api.gamificator.click

## Estimated AWS Costs (Monthly)

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| ECS Fargate | 2 tasks × 0.25 vCPU × 512MB × 730 hours | ~$15 |
| Application Load Balancer | 1 ALB + minimal traffic | ~$16 |
| ECR | <1GB storage | <$1 |
| Route 53 | 1 hosted zone + queries | ~$0.50 |
| Secrets Manager | 2 secrets | ~$1 |
| Data Transfer | <10GB/month | ~$1 |
| **Total** | | **~$34/month** |

*Note: Neon PostgreSQL free tier (0.5GB) used for database, not counted in AWS costs.*

---
