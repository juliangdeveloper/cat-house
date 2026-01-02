variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "sa-east-1"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "staging"
}

variable "certificate_arn" {
  description = "ARN of ACM certificate for API Gateway (sa-east-1)"
  type        = string
  default     = "arn:aws:acm:sa-east-1:578492750346:certificate/9ec24c1d-36cb-46a2-92d0-195b8f2afc53"
}

variable "certificate_arn_cloudfront" {
  description = "ARN of ACM certificate for CloudFront (us-east-1)"
  type        = string
  default     = "arn:aws:acm:us-east-1:578492750346:certificate/25745008-889d-4163-bba2-d71065c1b353"
}

variable "domain_name" {
  description = "Base domain name"
  type        = string
  default     = "gamificator.click"
}

variable "app_prefix" {
  description = "Prefix for this application (e.g., cathouse)"
  type        = string
  default     = "cathouse"
}

variable "hosted_zone_id" {
  description = "Route 53 Hosted Zone ID for the domain"
  type        = string
  default     = "Z060186227WPZP8YF5ZX8"
}

variable "frontend_domain_staging" {
  description = "Custom domain for staging frontend"
  type        = string
  default     = "chs.gamificator.click"
}

variable "frontend_domain_production" {
  description = "Custom domain for production frontend"
  type        = string
  default     = "chapp.gamificator.click"
}

# Sensitive variables are NOT defined in Terraform to keep credentials out of state files.
# These are injected during deployment via GitHub Actions workflows using GitHub Secrets:
#   - DATABASE_URL: Connection string from secrets.NEON_STAGING_DATABASE_URL or NEON_PRODUCTION_DATABASE_URL
#   - JWT_SECRET: Secret key from secrets.JWT_SECRET  
#   - ENCRYPTION_KEY: Encryption key from secrets.ENCRYPTION_KEY
# See .github/workflows/deploy-staging.yml and deploy-production.yml for implementation.

# Monitoring and Alerting
variable "alert_email" {
  description = "Email address for CloudWatch alarm notifications (optional)"
  type        = string
  default     = ""  # Can be set in terraform.tfvars for email notifications
}

# Note: Slack notifications are now handled via AWS Chatbot (configured in AWS Console)
# See docs/monitoring/aws-chatbot-setup.md for setup instructions
