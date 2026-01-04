# ECR Repositories for Docker images

resource "aws_ecr_repository" "services" {
  for_each = toset([
    "auth-service",
    "catalog-service",
    "installation-service",
    "proxy-service"
  ])

  name                 = "cat-house/${each.key}"
  image_tag_mutability = "MUTABLE"
  force_delete         = true # Allow deletion even if contains images

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Environment = var.environment
    Service     = each.key
    ManagedBy   = "Terraform"
  }
}

# Lifecycle policy to keep only recent images
resource "aws_ecr_lifecycle_policy" "services" {
  for_each   = aws_ecr_repository.services
  repository = each.value.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = {
        type = "expire"
      }
    }]
  })
}

output "ecr_repository_urls" {
  description = "ECR repository URLs for all services"
  value = {
    for k, v in aws_ecr_repository.services : k => v.repository_url
  }
}
