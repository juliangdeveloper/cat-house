# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "cat-house-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# CloudWatch Log Groups for each service
resource "aws_cloudwatch_log_group" "services" {
  for_each = toset([
    "auth-service",
    "catalog-service",
    "installation-service",
    "proxy-service",
    "health-aggregator"
  ])

  name              = "/ecs/cat-house/${var.environment}/${each.key}"
  retention_in_days = var.environment == "production" ? 90 : 30

  tags = {
    Environment = var.environment
    Service     = each.key
    ManagedBy   = "Terraform"
  }
}

# ECS Task Execution Role
resource "aws_iam_role" "ecs_execution_role" {
  name = "cat-house-${var.environment}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Allow reading secrets from Secrets Manager
resource "aws_iam_role_policy" "ecs_execution_secrets" {
  name = "ecs-execution-secrets"
  role = aws_iam_role.ecs_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = [
        aws_secretsmanager_secret.database_url.arn
      ]
    }]
  })
}

# ECS Task Role (for application permissions)
resource "aws_iam_role" "ecs_task_role" {
  name = "cat-house-${var.environment}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Service configuration
locals {
  services = {
    auth-service = {
      port   = 8005
      cpu    = 256
      memory = 512
    }
    catalog-service = {
      port   = 8002
      cpu    = 256
      memory = 512
    }
    installation-service = {
      port   = 8003
      cpu    = 256
      memory = 512
    }
    proxy-service = {
      port   = 8004
      cpu    = 256
      memory = 512
    }
    health-aggregator = {
      port   = 8000
      cpu    = 256
      memory = 512
    }
  }
}

# ECS Task Definitions
resource "aws_ecs_task_definition" "services" {
  for_each = local.services

  family                   = "cat-house-${var.environment}-${each.key}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = each.value.cpu
  memory                   = each.value.memory
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{
    name  = each.key
    image = "${aws_ecr_repository.services[each.key].repository_url}:latest"

    portMappings = [{
      containerPort = each.value.port
      protocol      = "tcp"
    }]

    environment = [
      {
        name  = "ENVIRONMENT"
        value = var.environment
      },
      {
        name  = "SERVICE_NAME"
        value = each.key
      },
      {
        name  = "PORT"
        value = tostring(each.value.port)
      }
    ]

    secrets = [
      {
        name      = "DATABASE_URL"
        valueFrom = aws_secretsmanager_secret.database_url.arn
      }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.services[each.key].name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }

    healthCheck = {
      command = [
        "CMD-SHELL",
        each.key == "health-aggregator" ? 
          "curl -f http://localhost:${each.value.port}/health || exit 1" :
          "curl -f http://localhost:${each.value.port}/api/v1/health || exit 1"
      ]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])

  tags = {
    Environment = var.environment
    Service     = each.key
    ManagedBy   = "Terraform"
  }
}

# Secrets Manager for database URL
resource "aws_secretsmanager_secret" "database_url" {
  name        = "cat-house/${var.environment}/database-url"
  description = "Neon PostgreSQL database URL for ${var.environment}"

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Note: The actual secret value must be set manually or via separate process
# to avoid storing credentials in Terraform state

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN"
  value       = aws_ecs_cluster.main.arn
}

output "task_definitions" {
  description = "ECS task definition ARNs"
  value = {
    for k, v in aws_ecs_task_definition.services : k => v.arn
  }
}
