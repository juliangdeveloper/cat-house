# AWS API Gateway for Cat House Platform

This directory contains Terraform configuration for deploying AWS API Gateway as the entry point for the Cat House Platform microservices.

## Features

- ✅ **Path-based routing** to all backend services
- ✅ **CORS configuration** for gamificator.click domain
- ✅ **Rate limiting** with usage plans
- ✅ **CloudWatch logging** and monitoring
- ✅ **Throttling protection** (burst and sustained)
- ✅ **Health check aggregation** endpoint
- ✅ **Custom domain support** (optional)

## Architecture

```
Client Request
    ↓
AWS API Gateway (Regional)
    ↓
┌─────────────────────────────────┐
│  /api/v1/auth        → Auth     │
│  /api/v1/catalog     → Catalog  │
│  /api/v1/installations → Install│
│  /api/v1/proxy       → Proxy    │
│  /health             → Health   │
└─────────────────────────────────┘
```

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Terraform** >= 1.0 installed
3. **AWS CLI** configured with credentials
4. **Backend services** deployed and accessible via HTTP/HTTPS

## Setup

### 1. Configure Variables

Copy the example variables file:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
aws_region = "us-east-1"

auth_service_url         = "https://your-auth-service.com"
catalog_service_url      = "https://your-catalog-service.com"
installation_service_url = "https://your-installation-service.com"
proxy_service_url        = "https://your-proxy-service.com"
health_aggregator_url    = "https://your-health-aggregator.com"
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Review Plan

```bash
terraform plan
```

### 4. Deploy

```bash
terraform apply
```

### 5. Get API Gateway URL

After deployment, get the API Gateway URL:

```bash
terraform output api_gateway_url
```

Example output:
```
https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod
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
