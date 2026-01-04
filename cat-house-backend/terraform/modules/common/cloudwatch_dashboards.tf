# CloudWatch Dashboards
# Following AWS best practices for dashboard configuration

resource "aws_cloudwatch_dashboard" "service_health" {
  dashboard_name = "cat-house-${var.environment}-service-health"
  dashboard_body = file("${path.module}/cloudwatch_dashboards/service_health.json")
}

resource "aws_cloudwatch_dashboard" "api_performance" {
  dashboard_name = "cat-house-${var.environment}-api-performance"
  dashboard_body = file("${path.module}/cloudwatch_dashboards/api_performance.json")
}

resource "aws_cloudwatch_dashboard" "business_metrics" {
  dashboard_name = "cat-house-${var.environment}-business-metrics"
  dashboard_body = file("${path.module}/cloudwatch_dashboards/business_metrics.json")
}

# Outputs for easy access to dashboard URLs
output "service_health_dashboard_url" {
  description = "URL to the Service Health dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.service_health.dashboard_name}"
}

output "api_performance_dashboard_url" {
  description = "URL to the API Performance dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.api_performance.dashboard_name}"
}

output "business_metrics_dashboard_url" {
  description = "URL to the Business Metrics dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.business_metrics.dashboard_name}"
}
