# Route 53 A record for frontend custom domain

resource "aws_route53_record" "frontend" {
  zone_id = var.hosted_zone_id
  name    = var.frontend_domain
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
