output "ecr_repository_urls" {
  description = "ECR repository URLs"
  value       = module.infrastructure.ecr_repository_urls
}

output "alb_url" {
  description = "Application Load Balancer URL"
  value       = "http://${module.infrastructure.alb_dns_name}"
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.infrastructure.alb_dns_name
}

output "cloudfront_url" {
  description = "CloudFront distribution URL"
  value       = "https://${module.infrastructure.cloudfront_domain_name}"
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (for GitHub Secrets)"
  value       = module.infrastructure.cloudfront_distribution_id
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.infrastructure.ecs_cluster_name
}

output "frontend_bucket" {
  description = "S3 bucket for frontend"
  value       = module.infrastructure.s3_bucket_name
}

output "frontend_url" {
  description = "Custom frontend URL"
  value       = "https://chapp.gamificator.click"
}
