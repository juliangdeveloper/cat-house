# Route 53 A records for frontend custom domains

# Staging frontend: chs.gamificator.click
resource "aws_route53_record" "frontend_staging" {
  count   = var.environment == "staging" ? 1 : 0
  zone_id = var.hosted_zone_id
  name    = var.frontend_domain_staging
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.frontend.domain_name
    zone_id                = aws_cloudfront_distribution.frontend.hosted_zone_id
    evaluate_target_health = false
  }
}

# Production frontend: chapp.gamificator.click
resource "aws_route53_record" "frontend_production" {
  count   = var.environment == "production" ? 1 : 0
  zone_id = var.hosted_zone_id
  name    = var.frontend_domain_production
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.frontend.domain_name
    zone_id                = aws_cloudfront_distribution.frontend.hosted_zone_id
    evaluate_target_health = false
  }
}

# Output frontend URL
output "frontend_url" {
  description = "Frontend URL (custom domain if configured, otherwise CloudFront domain)"
  value       = var.environment == "staging" ? "https://" : var.environment == "production" ? "https://" : "https://"
}
