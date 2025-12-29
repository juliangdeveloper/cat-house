# VPC and Networking for ECS Services
# Note: This assumes you have a default VPC. For production, create a dedicated VPC.

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_tasks" {
  name        = "cat-house-${var.environment}-ecs-tasks"
  description = "Security group for ECS tasks"
  vpc_id      = data.aws_vpc.default.id

  # Allow inbound from anywhere on service ports (API Gateway will proxy)
  ingress {
    description = "Auth Service"
    from_port   = 8005
    to_port     = 8005
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Catalog Service"
    from_port   = 8002
    to_port     = 8002
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Installation Service"
    from_port   = 8003
    to_port     = 8003
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Proxy Service"
    from_port   = 8004
    to_port     = 8004
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound traffic (for Neon DB, etc.)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# ECS Services
resource "aws_ecs_service" "services" {
  for_each = local.services

  name            = "cat-house-${var.environment}-${each.key}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.services[each.key].arn
  desired_count   = var.environment == "production" ? 2 : 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true  # Required for Fargate without NAT Gateway
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.services[each.key].arn
    container_name   = each.key
    container_port   = each.value.port
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  health_check_grace_period_seconds = 60

  # Enable ECS Exec for debugging
  enable_execute_command = true

  tags = {
    Environment = var.environment
    Service     = each.key
    ManagedBy   = "Terraform"
  }

  depends_on = [
    aws_iam_role_policy_attachment.ecs_execution_role_policy,
    aws_lb_listener.http
  ]
}

# CloudWatch Alarms for Service Health
resource "aws_cloudwatch_metric_alarm" "service_cpu" {
  for_each = local.services

  alarm_name          = "cat-house-${var.environment}-${each.key}-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ECS CPU utilization"

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.services[each.key].name
  }

  tags = {
    Environment = var.environment
    Service     = each.key
    ManagedBy   = "Terraform"
  }
}

resource "aws_cloudwatch_metric_alarm" "service_memory" {
  for_each = local.services

  alarm_name          = "cat-house-${var.environment}-${each.key}-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ECS memory utilization"

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.services[each.key].name
  }

  tags = {
    Environment = var.environment
    Service     = each.key
    ManagedBy   = "Terraform"
  }
}

# Auto Scaling (Optional - for production)
resource "aws_appautoscaling_target" "ecs_services" {
  for_each = var.environment == "production" ? local.services : {}

  max_capacity       = 4
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.services[each.key].name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_cpu_scaling" {
  for_each = var.environment == "production" ? local.services : {}

  name               = "cat-house-${var.environment}-${each.key}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_services[each.key].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_services[each.key].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_services[each.key].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Outputs
output "ecs_service_names" {
  description = "ECS service names"
  value = {
    for k, v in aws_ecs_service.services : k => v.name
  }
}

output "ecs_service_urls" {
  description = "Public URLs for ECS services (use these in API Gateway variables)"
  value = {
    for k, v in aws_ecs_service.services : k => "http://${aws_ecs_service.services[k].network_configuration[0].assign_public_ip}:${local.services[k].port}"
  }
}
