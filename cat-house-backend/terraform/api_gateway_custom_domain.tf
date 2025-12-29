# API Gateway Custom Domain
resource "aws_api_gateway_domain_name" "api" {
  domain_name              = var.environment == "production" ? "${var.app_prefix}-api.${var.domain_name}" : "${var.app_prefix}-api-${var.environment}.${var.domain_name}"
  regional_certificate_arn = var.certificate_arn

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Base Path Mapping
resource "aws_api_gateway_base_path_mapping" "api" {
  api_id      = aws_api_gateway_rest_api.cathouse_api.id
  stage_name  = aws_api_gateway_stage.prod.stage_name
  domain_name = aws_api_gateway_domain_name.api.domain_name
}

output "api_domain" {
  value       = aws_api_gateway_domain_name.api.domain_name
  description = "API Gateway custom domain name"
}

output "api_gateway_target_domain" {
  value       = aws_api_gateway_domain_name.api.regional_domain_name
  description = "Target domain for Route 53 A record"
}

output "api_gateway_hosted_zone_id" {
  value       = aws_api_gateway_domain_name.api.regional_zone_id
  description = "Hosted zone ID for API Gateway domain"
}
