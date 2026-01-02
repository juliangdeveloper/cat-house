# SNS Topics for CloudWatch Alarms
# Following AWS best practices for SNS topic naming and configuration

resource "aws_sns_topic" "critical_alerts" {
  name = "cat-house-${var.environment}-critical-alerts"

  tags = {
    Environment = var.environment
    AlertLevel  = "critical"
    ManagedBy   = "terraform"
  }
}

resource "aws_sns_topic" "warning_alerts" {
  name = "cat-house-${var.environment}-warning-alerts"

  tags = {
    Environment = var.environment
    AlertLevel  = "warning"
    ManagedBy   = "terraform"
  }
}

# SNS Topic Subscriptions
# Email subscriptions require manual confirmation via email

resource "aws_sns_topic_subscription" "critical_email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.critical_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_sns_topic_subscription" "warning_email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.warning_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Slack webhook integration
# Note: Slack webhooks use HTTPS protocol in SNS
resource "aws_sns_topic_subscription" "critical_slack" {
  count     = var.slack_webhook_url != "" ? 1 : 0
  topic_arn = aws_sns_topic.critical_alerts.arn
  protocol  = "https"
  endpoint  = var.slack_webhook_url
}

resource "aws_sns_topic_subscription" "warning_slack" {
  count     = var.slack_webhook_url != "" ? 1 : 0
  topic_arn = aws_sns_topic.warning_alerts.arn
  protocol  = "https"
  endpoint  = var.slack_webhook_url
}

# Outputs for reference
output "critical_alerts_topic_arn" {
  description = "ARN of the critical alerts SNS topic"
  value       = aws_sns_topic.critical_alerts.arn
}

output "warning_alerts_topic_arn" {
  description = "ARN of the warning alerts SNS topic"
  value       = aws_sns_topic.warning_alerts.arn
}
