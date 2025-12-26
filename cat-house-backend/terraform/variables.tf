variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
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
  description = "ARN of ACM certificate for custom domain (optional)"
  type        = string
  default     = ""
}
