# Cat House Infrastructure - Terraform

This directory contains Terraform configuration for deploying the complete Cat House infrastructure on AWS, including ECR, ECS Fargate, S3/CloudFront, and API Gateway.

## Infrastructure Components

### Core Services
- **ECR Repositories** (`ecr.tf`): Docker image registries for all 5 microservices
- **ECS Cluster** (`ecs.tf`): Fargate cluster with task definitions and CloudWatch logs
- **Frontend Hosting** (`frontend.tf`): S3 bucket + CloudFront distribution
- **API Gateway** (`main.tf`, `routes.tf`): HTTP API for routing requests
- **Secrets Management** (`ecs.tf`): AWS Secrets Manager for database credentials

### Services Deployed
1. `auth-service` (Port 8005) - Authentication and user management
2. `catalog-service` (Port 8002) - Cat catalog management
3. `installation-service` (Port 8003) - Installation tracking
4. `proxy-service` (Port 8004) - External API proxy
5. `health-aggregator` (Port 8000) - Health check aggregation

## Architecture

```
                    ┌─────────────────┐
                    │   CloudFront    │ (Frontend)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   S3 Bucket     │
                    └─────────────────┘

                    ┌─────────────────┐
         Client ───►│  API Gateway    │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐      ┌────▼────┐      ┌─────▼─────┐
    │ ECS Task  │      │ECS Task │      │ ECS Task  │
    │   Auth    │      │ Catalog │      │  Proxy    │
    └───────────┘      └─────────┘      └───────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    ┌────────▼────────┐
                    │ Neon PostgreSQL │
                    │  (Serverless)   │
                    └─────────────────┘
```

## Prerequisites

1. **AWS Account** with appropriate IAM permissions for:
   - ECR (Elastic Container Registry)
   - ECS (Elastic Container Service)
   - S3, CloudFront
   - API Gateway
   - IAM, Secrets Manager
   - CloudWatch Logs

2. **Terraform** >= 1.0 installed
   ```bash
   terraform version
   ```

3. **AWS CLI** configured with credentials
   ```bash
   aws configure
   ```

4. **Neon Database** URL (PostgreSQL connection string)

## Quick Start

### 1. Configure Variables

Create `terraform.tfvars`:

```hcl
aws_region = "us-east-1"
environment = "staging"  # or "production"

# Service URLs (for API Gateway routes - can be localhost during initial setup)
auth_service_url         = "http://localhost:8005"
catalog_service_url      = "http://localhost:8002"
installation_service_url = "http://localhost:8003"
proxy_service_url        = "http://localhost:8004"
health_aggregator_url    = "http://localhost:8000"
```

### 2. Create Database Secret

```bash
# Staging environment
aws secretsmanager create-secret \
  --name cat-house/staging/database-url \
  --secret-string "postgresql://user:pass@ep-xxx.us-east-1.aws.neon.tech/neondb" \
  --region us-east-1

# Production environment
aws secretsmanager create-secret \
  --name cat-house/production/database-url \
  --secret-string "postgresql://user:pass@ep-xxx.us-east-1.aws.neon.tech/neondb" \
  --region us-east-1
```

### 3. Initialize and Apply

```bash
# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply infrastructure
terraform apply
```

### 4. Build and Push Docker Images

```bash
# Get ECR login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $(terraform output -raw ecr_repository_urls | jq -r '.["auth-service"]' | cut -d'/' -f1)

# Build and push all services
cd ../
for service in auth-service catalog-service installation-service proxy-service health-aggregator; do
  echo "Building $service..."
  docker build -t cat-house/$service -f $service/Dockerfile $service
  
  ECR_URL=$(cd terraform && terraform output -json ecr_repository_urls | jq -r ".[\"$service\"]")
  docker tag cat-house/$service:latest $ECR_URL:latest
  docker push $ECR_URL:latest
done
```

### 5. Get Outputs

```bash
terraform output
terraform output cloudfront_domain_name
terraform output api_gateway_url
```

## Usage

### Testing Endpoints

```bash
# Health check
curl https://your-api-gateway-url/health

# Auth service
curl https://your-api-gateway-url/api/v1/auth/health

# Catalog service
curl https://your-api-gateway-url/api/v1/catalog/health
```

### Rate Limits

**General Usage Plan:**
- Burst: 100 requests
- Sustained: 50 requests/second
- Daily quota: 10,000 requests

**Authenticated Usage Plan:**
- Burst: 200 requests
- Sustained: 100 requests/second
- Daily quota: 50,000 requests

### Custom Domain (Optional)

To use a custom domain (e.g., `api.gamificator.click`):

1. Request an ACM certificate in AWS Certificate Manager
2. Uncomment the custom domain section in `main.tf`
3. Update `certificate_arn` variable
4. Apply changes: `terraform apply`
5. Create a CNAME record in your DNS:
   ```
   api.gamificator.click → xxxxxxxxxx.execute-api.us-east-1.amazonaws.com
   ```

## Monitoring

### CloudWatch Logs

Logs are sent to: `/aws/apigateway/cathouse-api`

View logs:
```bash
aws logs tail /aws/apigateway/cathouse-api --follow
```

### CloudWatch Metrics

Available metrics:
- `Count` - Number of API requests
- `Latency` - Time to process request
- `4XXError` - Client errors
- `5XXError` - Server errors

## Cost Estimate

**API Gateway Pricing (us-east-1):**
- First 333 million requests: $3.50 per million
- Logging: ~$0.50 per GB
- Data transfer: $0.09 per GB (out)

**Example Monthly Cost:**
- 1M requests/month: ~$3.50
- 10M requests/month: ~$35
- 100M requests/month: ~$350

## Terraform State

### Local State (Default)

State is stored locally in `terraform.tfstate`. **Do not commit this file to git.**

### Remote State (Recommended for Production)

Configure S3 backend for state:

```hcl
terraform {
  backend "s3" {
    bucket = "your-terraform-state-bucket"
    key    = "cathouse/api-gateway/terraform.tfstate"
    region = "us-east-1"
  }
}
```

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

## Files

- `main.tf` - Main API Gateway configuration
- `routes.tf` - Route definitions for all services
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `terraform.tfvars.example` - Example variables file

## Security

- CORS restricted to `https://gamificator.click`
- Rate limiting enabled with usage plans
- CloudWatch logging for audit trail
- Request/response size limits enforced
- Timeout protection (29s max)

## Troubleshooting

### 502 Bad Gateway

- Check backend service URLs are correct
- Verify services are accessible from internet
- Check CloudWatch logs for detailed errors

### CORS Errors

- Verify `Access-Control-Allow-Origin` header
- Check preflight OPTIONS requests are handled
- Ensure credentials are allowed if needed

### Rate Limiting

- Check CloudWatch metrics for throttling
- Adjust usage plan limits if needed
- Consider implementing API keys for authenticated users

## Next Steps

1. Set up API keys for authenticated users
2. Configure custom domain with ACM certificate
3. Set up CloudWatch alarms for errors
4. Implement request validation
5. Add AWS WAF for additional security
