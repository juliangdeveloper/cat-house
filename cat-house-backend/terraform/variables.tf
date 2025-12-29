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

# Sensitive variables - values should be passed from GitHub Secrets during deployment
# These should NOT have default values to prevent accidental exposure
variable "database_url" {
  description = "Neon PostgreSQL database connection string (from GitHub Secrets)"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT secret key for authentication (from GitHub Secrets)"
  type        = string
  sensitive   = true
}

variable "encryption_key" {
  description = "Encryption key for sensitive data (from GitHub Secrets)"
  type        = string
  sensitive   = true
}
