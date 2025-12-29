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

variable "auth_service_url" {
  description = "URL for Auth Service backend"
  type        = string
}

variable "catalog_service_url" {
  description = "URL for Catalog Service backend"
  type        = string
}

variable "installation_service_url" {
  description = "URL for Installation Service backend"
  type        = string
}

variable "proxy_service_url" {
  description = "URL for Proxy Service backend"
  type        = string
}

variable "health_aggregator_url" {
  description = "URL for Health Aggregator Service"
  type        = string
}

variable "certificate_arn" {
  description = "ARN of ACM certificate for custom domain"
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
