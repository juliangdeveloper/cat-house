# Route53 A record for backend API custom domain
# Uses alias record (AWS best practice) instead of CNAME to point to ALB
# Reference: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-choosing-alias-non-alias.html

resource "aws_route53_record" "backend_api" {
  zone_id = var.hosted_zone_id
  name    = var.api_domain # chapi.gamificator.click or chapi-staging.gamificator.click
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# Output backend API URL
output "backend_api_url" {
  description = "Backend API URL (custom domain)"
  value       = "https://${var.api_domain}"
}
