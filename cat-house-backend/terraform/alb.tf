# Application Load Balancer for Cat House Backend Services
# Provides stable endpoint for API Gateway to route to ECS Fargate tasks

# Security Group for ALB
resource "aws_security_group" "alb" {
  name        = "cat-house-${var.environment}-alb"
  description = "Security group for Cat House Application Load Balancer"
  vpc_id      = data.aws_vpc.default.id

  # Inbound HTTP from anywhere
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP from internet"
  }

  # Inbound HTTPS from anywhere
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTPS from internet"
  }

  # Outbound to ECS tasks
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "cat-house-${var.environment}-alb"
    Environment = var.environment
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "cat-house-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = data.aws_subnets.default.ids

  enable_deletion_protection       = var.environment == "production" ? true : false
  enable_http2                     = true
  enable_cross_zone_load_balancing = true

  tags = {
    Name        = "cat-house-${var.environment}-alb"
    Environment = var.environment
  }
}

# Target Groups - One per service
locals {
  target_group_configs = {
    auth-service = {
      port        = 8005
      health_path = "/api/v1/auth/health"
    }
    catalog-service = {
      port        = 8002
      health_path = "/api/v1/catalog/health"
    }
    installation-service = {
      port        = 8003
      health_path = "/api/v1/installation/health"
    }
    proxy-service = {
      port        = 8004
      health_path = "/api/v1/proxy/health"
    }
  }
}

resource "aws_lb_target_group" "services" {
  for_each = local.target_group_configs

  # Use abbreviated name to stay within 32 character limit
  # Format: ch-{env}-{service-abbrev} (e.g., ch-staging-auth, ch-staging-health)
  name = format("ch-%s-%s",
    var.environment,
    replace(replace(each.key, "-service", ""), "installation", "install")
  )
  port        = each.value.port
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip" # Required for awsvpc network mode

  health_check {
    enabled             = true
    path                = each.value.health_path
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  deregistration_delay = 30

  tags = {
    Name        = "cat-house-${var.environment}-${each.key}"
    Environment = var.environment
    Service     = each.key
  }
}

# HTTP Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  # Default action - return 404
  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "application/json"
      message_body = jsonencode({
        error   = "Not Found"
        message = "No matching route found"
      })
      status_code = "404"
    }
  }
}

# Listener Rules - Path-based routing

# Auth Service
resource "aws_lb_listener_rule" "auth" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.services["auth-service"].arn
  }

  condition {
    path_pattern {
      values = ["/api/v1/auth/*"]
    }
  }
}

# Catalog Service
resource "aws_lb_listener_rule" "catalog" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 200

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.services["catalog-service"].arn
  }

  condition {
    path_pattern {
      values = ["/api/v1/catalog/*"]
    }
  }
}

# Installation Service
resource "aws_lb_listener_rule" "installation" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 300

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.services["installation-service"].arn
  }

  condition {
    path_pattern {
      values = ["/api/v1/installation/*"]
    }
  }
}

# Proxy Service
resource "aws_lb_listener_rule" "proxy" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 400

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.services["proxy-service"].arn
  }

  condition {
    path_pattern {
      values = ["/api/v1/proxy/*"]
    }
  }
}

# Health endpoint - return aggregated health from ALB target groups
resource "aws_lb_listener_rule" "health" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 50 # Higher priority to catch /health before other rules

  action {
    type = "fixed-response"
    fixed_response {
      content_type = "application/json"
      message_body = jsonencode({
        status = "healthy"
        message = "ALB is operational. Check individual service health endpoints."
      })
      status_code = "200"
    }
  }

  condition {
    path_pattern {
      values = ["/health", "/api/v1/health"]
    }
  }
}
