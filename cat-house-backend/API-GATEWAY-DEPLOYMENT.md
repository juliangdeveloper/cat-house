# API Gateway Deployment Guide

## Overview

This guide covers the deployment of AWS API Gateway for the Cat House Platform using Terraform.

## Architecture

```
                        ┌─────────────────────┐
                        │   AWS API Gateway   │
                        │    (Regional)       │
                        └──────────┬──────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
         ┌──────────▼──┐   ┌──────▼──────┐   ┌──▼──────────┐
         │  Auth       │   │  Catalog    │   │ Installation│
         │  Service    │   │  Service    │   │  Service    │
         │  (8005)     │   │  (8002)     │   │  (8003)     │
         └─────────────┘   └─────────────┘   └─────────────┘
                    
         ┌─────────────┐   ┌─────────────────┐
         │  Proxy      │   │  Health         │
         │  Service    │   │  Aggregator     │
         │  (8004)     │   │  (8000)         │
         └─────────────┘   └─────────────────┘
```

## Prerequisites

### 1. AWS Account Setup

- AWS account with appropriate IAM permissions
- AWS CLI installed and configured
- Access to create API Gateway, CloudWatch, and IAM resources

### 2. Backend Services

All backend services must be:
- Deployed and running
- Publicly accessible via HTTPS (recommended) or HTTP
- Returning health check responses at `/health` endpoint

### 3. Tools

```bash
# Install Terraform
# macOS
brew install terraform

# Windows
choco install terraform

# Linux
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Verify installation
terraform --version
```

## Deployment Steps

### Step 1: Configure AWS Credentials

```bash
# Configure AWS CLI
aws configure

# Enter your credentials:
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region name: us-east-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

### Step 2: Prepare Backend Services

Ensure all services are deployed and note their URLs:

```bash
# Example service URLs
AUTH_URL="https://auth.your-domain.com"
CATALOG_URL="https://catalog.your-domain.com"
INSTALLATION_URL="https://installation.your-domain.com"
PROXY_URL="https://proxy.your-domain.com"
HEALTH_URL="https://health.your-domain.com"
```

### Step 3: Configure Terraform Variables

```bash
cd cat-house-backend/terraform

# Copy example file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars
nano terraform.tfvars
```

Update with your values:

```hcl
aws_region = "us-east-1"

auth_service_url         = "https://your-auth-service.com"
catalog_service_url      = "https://your-catalog-service.com"
installation_service_url = "https://your-installation-service.com"
proxy_service_url        = "https://your-proxy-service.com"
health_aggregator_url    = "https://your-health-aggregator.com"
```

### Step 4: Initialize Terraform

```bash
# Initialize Terraform (downloads providers)
terraform init

# Expected output:
# Terraform has been successfully initialized!
```

### Step 5: Review Plan

```bash
# Generate and review execution plan
terraform plan

# Review the resources that will be created:
# - aws_api_gateway_rest_api
# - aws_api_gateway_resource (multiple)
# - aws_api_gateway_method (multiple)
# - aws_api_gateway_integration (multiple)
# - aws_api_gateway_deployment
# - aws_api_gateway_stage
# - aws_api_gateway_usage_plan (2)
# - aws_cloudwatch_log_group
# - aws_iam_role
# etc.
```

### Step 6: Deploy

```bash
# Apply the configuration
terraform apply

# Review the plan and type 'yes' to confirm

# Deployment takes 2-5 minutes
```

### Step 7: Get API Gateway URL

```bash
# Get the API Gateway URL
terraform output api_gateway_url

# Example output:
# https://abc123def4.execute-api.us-east-1.amazonaws.com/prod
```

### Step 8: Test Deployment

```bash
# Set API URL
API_URL=$(terraform output -raw api_gateway_url)

# Test health endpoint
curl $API_URL/health

# Expected: Aggregated health status of all services

# Test individual services
curl $API_URL/api/v1/auth/health
curl $API_URL/api/v1/catalog/health
curl $API_URL/api/v1/installations/health
curl $API_URL/api/v1/proxy/health
```

## Custom Domain Setup (Optional)

### Step 1: Request ACM Certificate

```bash
# Request certificate in AWS Certificate Manager
aws acm request-certificate \
  --domain-name api.gamificator.click \
  --validation-method DNS \
  --region us-east-1

# Note the CertificateArn from output
```

### Step 2: Validate Certificate

- Go to AWS Console → Certificate Manager
- Add DNS validation records to your domain's DNS
- Wait for certificate status to become "Issued"

### Step 3: Update Terraform Configuration

Uncomment custom domain section in `main.tf`:

```hcl
resource "aws_api_gateway_domain_name" "api" {
  domain_name              = "api.gamificator.click"
  regional_certificate_arn = var.certificate_arn

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_base_path_mapping" "api" {
  api_id      = aws_api_gateway_rest_api.cathouse_api.id
  stage_name  = aws_api_gateway_stage.prod.stage_name
  domain_name = aws_api_gateway_domain_name.api.domain_name
}
```

Update `terraform.tfvars`:

```hcl
certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/xxxxx"
```

### Step 4: Apply Changes

```bash
terraform apply
```

### Step 5: Update DNS

Create CNAME record:

```
Type: CNAME
Name: api.gamificator.click
Value: abc123def4.execute-api.us-east-1.amazonaws.com
TTL: 300
```

## Monitoring

### CloudWatch Logs

```bash
# View logs
aws logs tail /aws/apigateway/cathouse-api --follow

# Filter by error
aws logs filter-log-events \
  --log-group-name /aws/apigateway/cathouse-api \
  --filter-pattern "ERROR"
```

### CloudWatch Metrics

View metrics in AWS Console:
- API Gateway → Your API → Monitoring
- Metrics: Count, Latency, 4XXError, 5XXError

### CloudWatch Alarms

Create alarms for monitoring:

```bash
# Create alarm for 5XX errors
aws cloudwatch put-metric-alarm \
  --alarm-name "cathouse-api-5xx-errors" \
  --alarm-description "Alert on API Gateway 5XX errors" \
  --metric-name 5XXError \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1
```

## Updating Configuration

### Update Backend Service URLs

```bash
# Edit terraform.tfvars
nano terraform.tfvars

# Apply changes
terraform apply
```

### Update Rate Limits

Edit `main.tf` and modify usage plans:

```hcl
resource "aws_api_gateway_usage_plan" "general" {
  # ...
  throttle_settings {
    burst_limit = 150  # Updated from 100
    rate_limit  = 75   # Updated from 50
  }
}
```

Apply:

```bash
terraform apply
```

## Rollback

### Rollback to Previous Version

```bash
# View state versions
terraform state list

# Import previous state if using remote backend
terraform state pull > backup.tfstate

# Rollback (if you have a backup)
cp backup.tfstate terraform.tfstate
terraform apply
```

### Destroy Everything

```bash
# Destroy all resources
terraform destroy

# Type 'yes' to confirm
```

## Troubleshooting

### Issue: 502 Bad Gateway

**Cause:** Backend service unreachable

**Solution:**
```bash
# Test backend directly
curl https://your-service-url/health

# Check CloudWatch logs
aws logs tail /aws/apigateway/cathouse-api --follow

# Verify security groups/firewall rules
```

### Issue: CORS Errors

**Cause:** CORS headers not configured correctly

**Solution:**
- Verify OPTIONS method is configured
- Check response headers in browser DevTools
- Ensure backend returns CORS headers

### Issue: Rate Limiting Too Strict

**Cause:** Usage plan limits too low

**Solution:**
```bash
# Update limits in main.tf
# Apply changes
terraform apply
```

### Issue: High Latency

**Cause:** Backend services slow or timeout issues

**Solution:**
- Check backend service performance
- Review CloudWatch metrics for latency
- Consider increasing timeout values
- Optimize backend queries

## Cost Optimization

### Monitor Costs

```bash
# View current month's costs
aws ce get-cost-and-usage \
  --time-period Start=2025-12-01,End=2025-12-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter file://filter.json
```

### Reduce Costs

1. **Reduce logging level**
   ```hcl
   logging_level = "ERROR"  # Instead of "INFO"
   ```

2. **Decrease log retention**
   ```hcl
   retention_in_days = 1  # Instead of 7
   ```

3. **Disable data trace**
   ```hcl
   data_trace_enabled = false
   ```

## Security Best Practices

1. **Use API Keys** for authenticated requests
2. **Enable AWS WAF** for DDoS protection
3. **Use custom domain** with SSL/TLS
4. **Implement request validation**
5. **Set up CloudWatch alarms**
6. **Regular security audits**
7. **Use VPC Link** for private backend services

## Next Steps

1. Set up API keys for customer authentication
2. Configure custom domain
3. Implement request/response validation
4. Add AWS WAF rules
5. Set up automated backups
6. Create disaster recovery plan
7. Implement blue-green deployment strategy

## Support

For issues or questions:
- Check CloudWatch Logs
- Review AWS API Gateway documentation
- Contact platform team
