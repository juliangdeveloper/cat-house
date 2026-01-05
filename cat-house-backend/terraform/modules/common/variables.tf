variable "environment" {
  description = "Environment name (staging or production)"
  type        = string
  
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be staging or production."
  }
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "sa-east-1"
}

variable "certificate_arn" {
  description = "ACM certificate ARN for ALB (sa-east-1)"
  type        = string
}

variable "certificate_arn_cloudfront" {
  description = "ACM certificate ARN for CloudFront (us-east-1)"
  type        = string
}

variable "domain_name" {
  description = "Base domain name"
  type        = string
  default     = "gamificator.click"
}

variable "app_prefix" {
  description = "Prefix for this application"
  type        = string
  default     = "cathouse"
}

variable "hosted_zone_id" {
  description = "Route 53 Hosted Zone ID for the domain"
  type        = string
}

variable "frontend_domain" {
  description = "Custom domain for frontend CloudFront distribution"
  type        = string
}

variable "api_domain" {
  description = "Custom domain for backend API (e.g., chapi.gamificator.click)"
  type        = string
}

variable "alert_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  default     = ""
}
