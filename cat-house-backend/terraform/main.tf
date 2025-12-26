terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# API Gateway REST API
resource "aws_api_gateway_rest_api" "cathouse_api" {
  name        = "cathouse-api-gateway"
  description = "API Gateway for Cat House Platform"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

# API Gateway Stage
resource "aws_api_gateway_stage" "prod" {
  deployment_id = aws_api_gateway_deployment.prod.id
  rest_api_id   = aws_api_gateway_rest_api.cathouse_api.id
  stage_name    = "prod"

  variables = {
    auth_service_url         = var.auth_service_url
    catalog_service_url      = var.catalog_service_url
    installation_service_url = var.installation_service_url
    proxy_service_url        = var.proxy_service_url
    health_aggregator_url    = var.health_aggregator_url
  }
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "prod" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.api.id,
      aws_api_gateway_resource.v1.id,
      aws_api_gateway_resource.auth.id,
      aws_api_gateway_resource.catalog.id,
      aws_api_gateway_resource.installations.id,
      aws_api_gateway_resource.proxy.id,
      aws_api_gateway_resource.health.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.auth,
    aws_api_gateway_integration.catalog,
    aws_api_gateway_integration.installations,
    aws_api_gateway_integration.proxy,
    aws_api_gateway_integration.health,
  ]
}

# Enable CloudWatch Logging
resource "aws_api_gateway_account" "main" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch.arn
}

resource "aws_iam_role" "api_gateway_cloudwatch" {
  name = "api-gateway-cloudwatch-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch" {
  role       = aws_iam_role.api_gateway_cloudwatch.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

# Enable Access Logging
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/cathouse-api"
  retention_in_days = 7
}

resource "aws_api_gateway_method_settings" "prod" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  stage_name  = aws_api_gateway_stage.prod.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled        = true
    logging_level          = "INFO"
    data_trace_enabled     = true
    throttling_burst_limit = 100
    throttling_rate_limit  = 50
  }
}

# Usage Plan for Rate Limiting
resource "aws_api_gateway_usage_plan" "general" {
  name        = "general-usage-plan"
  description = "General usage plan with standard rate limits"

  api_stages {
    api_id = aws_api_gateway_rest_api.cathouse_api.id
    stage  = aws_api_gateway_stage.prod.stage_name
  }

  throttle_settings {
    burst_limit = 100
    rate_limit  = 50
  }

  quota_settings {
    limit  = 10000
    period = "DAY"
  }
}

resource "aws_api_gateway_usage_plan" "authenticated" {
  name        = "authenticated-usage-plan"
  description = "Usage plan for authenticated users with higher limits"

  api_stages {
    api_id = aws_api_gateway_rest_api.cathouse_api.id
    stage  = aws_api_gateway_stage.prod.stage_name
  }

  throttle_settings {
    burst_limit = 200
    rate_limit  = 100
  }

  quota_settings {
    limit  = 50000
    period = "DAY"
  }
}

# Gateway Response for CORS
resource "aws_api_gateway_gateway_response" "cors" {
  rest_api_id   = aws_api_gateway_rest_api.cathouse_api.id
  response_type = "DEFAULT_4XX"

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = "'https://gamificator.click'"
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Authorization,Content-Type,X-Requested-With'"
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
  }
}

resource "aws_api_gateway_gateway_response" "cors_5xx" {
  rest_api_id   = aws_api_gateway_rest_api.cathouse_api.id
  response_type = "DEFAULT_5XX"

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = "'https://gamificator.click'"
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Authorization,Content-Type,X-Requested-With'"
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
  }
}

# Custom Domain (Optional)
# Uncomment and configure if you have a custom domain
# resource "aws_api_gateway_domain_name" "api" {
#   domain_name              = "api.gamificator.click"
#   regional_certificate_arn = var.certificate_arn
#
#   endpoint_configuration {
#     types = ["REGIONAL"]
#   }
# }

# resource "aws_api_gateway_base_path_mapping" "api" {
#   api_id      = aws_api_gateway_rest_api.cathouse_api.id
#   stage_name  = aws_api_gateway_stage.prod.stage_name
#   domain_name = aws_api_gateway_domain_name.api.domain_name
# }
