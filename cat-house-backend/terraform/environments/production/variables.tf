variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "sa-east-1"
}

variable "certificate_arn" {
  description = "ACM certificate ARN for ALB"
  type        = string
}

variable "certificate_arn_cloudfront" {
  description = "CloudFront ACM certificate ARN"
  type        = string
}

variable "domain_name" {
  description = "Base domain name"
  type        = string
  default     = "gamificator.click"
}

variable "app_prefix" {
  description = "Application prefix"
  type        = string
  default     = "cathouse"
}

variable "hosted_zone_id" {
  description = "Route53 hosted zone ID"
  type        = string
}

variable "frontend_domain_production" {
  description = "Production frontend domain"
  type        = string
  default     = "chapp.gamificator.click"
}

variable "alert_email" {
  description = "Email for CloudWatch alarms"
  type        = string
  default     = ""
}
