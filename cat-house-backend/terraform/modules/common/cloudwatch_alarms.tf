# CloudWatch Alarms
# Following AWS best practices for alarm configuration and threshold settings

locals {
  # Production services only (health-aggregator is dev-only)
  service_names = [
    "auth-service",
    "catalog-service",
    "installation-service",
    "proxy-service"
  ]
}

# Critical Alarm: Service Down
# Triggers when ECS service has no running tasks
resource "aws_cloudwatch_metric_alarm" "service_down" {
  for_each = toset(local.service_names)

  alarm_name          = "${var.environment}-${each.key}-down"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "RunningTaskCount"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 1
  alarm_description   = "${each.key} has no running tasks"
  alarm_actions       = [aws_sns_topic.critical_alerts.arn]
  ok_actions          = [aws_sns_topic.critical_alerts.arn]
  treat_missing_data  = "breaching"

  dimensions = {
    ServiceName = "cat-house-${var.environment}-${each.key}"
    ClusterName = "cat-house-${var.environment}"
  }

  tags = {
    Service     = each.key
    Environment = var.environment
    Severity    = "critical"
    ManagedBy   = "terraform"
  }
}

# Critical Alarm: High Error Rate
# Triggers when error rate exceeds 5%
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  for_each = toset(local.service_names)

  alarm_name          = "${var.environment}-${each.key}-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  threshold           = 5  # 5% error rate
  alarm_description   = "${each.key} has high error rate (>5%)"
  alarm_actions       = [aws_sns_topic.critical_alerts.arn]
  ok_actions          = [aws_sns_topic.critical_alerts.arn]
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "error_rate"
    expression  = "IF(m2 > 0, m1 / m2 * 100, 0)"
    label       = "Error Rate %"
    return_data = true
  }

  metric_query {
    id = "m1"
    metric {
      metric_name = "http_requests_total"
      namespace   = "CatHouse/Services"
      period      = 300
      stat        = "Sum"
      dimensions = {
        service = each.key
        status  = "5xx"
      }
    }
  }

  metric_query {
    id = "m2"
    metric {
      metric_name = "http_requests_total"
      namespace   = "CatHouse/Services"
      period      = 300
      stat        = "Sum"
      dimensions = {
        service = each.key
      }
    }
  }

  tags = {
    Service     = each.key
    Environment = var.environment
    Severity    = "critical"
    ManagedBy   = "terraform"
  }
}

# Warning Alarm: High Latency
# Triggers when p95 latency exceeds 500ms for 2 out of 3 periods
resource "aws_cloudwatch_metric_alarm" "high_latency" {
  for_each = toset(local.service_names)

  alarm_name          = "${var.environment}-${each.key}-high-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  datapoints_to_alarm = 2
  threshold           = 0.5  # 500ms in seconds
  alarm_description   = "${each.key} p95 latency > 500ms"
  alarm_actions       = [aws_sns_topic.warning_alerts.arn]
  ok_actions          = [aws_sns_topic.warning_alerts.arn]
  treat_missing_data  = "notBreaching"

  metric_name        = "http_request_duration_seconds"
  namespace          = "CatHouse/Services"
  period             = 300
  extended_statistic = "p95"

  dimensions = {
    service = each.key
  }

  tags = {
    Service     = each.key
    Environment = var.environment
    Severity    = "warning"
    ManagedBy   = "terraform"
  }
}

# Warning Alarm: High CPU Usage
# Triggers when CPU utilization exceeds 80% for 3 consecutive periods
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  for_each = toset(local.service_names)

  alarm_name          = "${var.environment}-${each.key}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "${each.key} CPU > 80%"
  alarm_actions       = [aws_sns_topic.warning_alerts.arn]
  ok_actions          = [aws_sns_topic.warning_alerts.arn]

  dimensions = {
    ServiceName = "cat-house-${var.environment}-${each.key}"
    ClusterName = "cat-house-${var.environment}"
  }

  tags = {
    Service     = each.key
    Environment = var.environment
    Severity    = "warning"
    ManagedBy   = "terraform"
  }
}

# Warning Alarm: High Memory Usage
# Triggers when memory utilization exceeds 85% for 3 consecutive periods
resource "aws_cloudwatch_metric_alarm" "high_memory" {
  for_each = toset(local.service_names)

  alarm_name          = "${var.environment}-${each.key}-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 85
  alarm_description   = "${each.key} memory > 85%"
  alarm_actions       = [aws_sns_topic.warning_alerts.arn]
  ok_actions          = [aws_sns_topic.warning_alerts.arn]

  dimensions = {
    ServiceName = "cat-house-${var.environment}-${each.key}"
    ClusterName = "cat-house-${var.environment}"
  }

  tags = {
    Service     = each.key
    Environment = var.environment
    Severity    = "warning"
    ManagedBy   = "terraform"
  }
}

# Outputs for reference
output "alarms_created" {
  description = "List of CloudWatch alarms created"
  value = {
    service_down     = [for k, v in aws_cloudwatch_metric_alarm.service_down : v.alarm_name]
    high_error_rate  = [for k, v in aws_cloudwatch_metric_alarm.high_error_rate : v.alarm_name]
    high_latency     = [for k, v in aws_cloudwatch_metric_alarm.high_latency : v.alarm_name]
    high_cpu         = [for k, v in aws_cloudwatch_metric_alarm.high_cpu : v.alarm_name]
    high_memory      = [for k, v in aws_cloudwatch_metric_alarm.high_memory : v.alarm_name]
  }
}
