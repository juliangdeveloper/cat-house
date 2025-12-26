# Resources for API Gateway routing structure

# /api resource
resource "aws_api_gateway_resource" "api" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  parent_id   = aws_api_gateway_rest_api.cathouse_api.root_resource_id
  path_part   = "api"
}

# /api/v1 resource
resource "aws_api_gateway_resource" "v1" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "v1"
}

# /health resource (at root level)
resource "aws_api_gateway_resource" "health" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  parent_id   = aws_api_gateway_rest_api.cathouse_api.root_resource_id
  path_part   = "health"
}

# ============================================
# AUTH SERVICE ROUTES
# ============================================

resource "aws_api_gateway_resource" "auth" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "auth"
}

resource "aws_api_gateway_resource" "auth_proxy" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  parent_id   = aws_api_gateway_resource.auth.id
  path_part   = "{proxy+}"
}

# Auth ANY method
resource "aws_api_gateway_method" "auth" {
  rest_api_id   = aws_api_gateway_rest_api.cathouse_api.id
  resource_id   = aws_api_gateway_resource.auth_proxy.id
  http_method   = "ANY"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.proxy" = true
  }
}

# Auth OPTIONS method for CORS
resource "aws_api_gateway_method" "auth_options" {
  rest_api_id   = aws_api_gateway_rest_api.cathouse_api.id
  resource_id   = aws_api_gateway_resource.auth_proxy.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# Auth Integration
resource "aws_api_gateway_integration" "auth" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  resource_id = aws_api_gateway_resource.auth_proxy.id
  http_method = aws_api_gateway_method.auth.http_method
  
  integration_http_method = "ANY"
  type                    = "HTTP_PROXY"
  uri                     = "${var.auth_service_url}/{proxy}"
  connection_type         = "INTERNET"

  timeout_milliseconds = 29000

  request_parameters = {
    "integration.request.path.proxy" = "method.request.path.proxy"
  }
}

# Auth OPTIONS Integration for CORS
resource "aws_api_gateway_integration" "auth_options" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  resource_id = aws_api_gateway_resource.auth_proxy.id
  http_method = aws_api_gateway_method.auth_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "auth_options" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  resource_id = aws_api_gateway_resource.auth_proxy.id
  http_method = aws_api_gateway_method.auth_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "auth_options" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  resource_id = aws_api_gateway_resource.auth_proxy.id
  http_method = aws_api_gateway_method.auth_options.http_method
  status_code = aws_api_gateway_method_response.auth_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Authorization,Content-Type,X-Requested-With'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'https://gamificator.click'"
  }
}

# ============================================
# CATALOG SERVICE ROUTES
# ============================================

resource "aws_api_gateway_resource" "catalog" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "catalog"
}

resource "aws_api_gateway_resource" "catalog_proxy" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  parent_id   = aws_api_gateway_resource.catalog.id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "catalog" {
  rest_api_id   = aws_api_gateway_rest_api.cathouse_api.id
  resource_id   = aws_api_gateway_resource.catalog_proxy.id
  http_method   = "ANY"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.proxy" = true
  }
}

resource "aws_api_gateway_method" "catalog_options" {
  rest_api_id   = aws_api_gateway_rest_api.cathouse_api.id
  resource_id   = aws_api_gateway_resource.catalog_proxy.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "catalog" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  resource_id = aws_api_gateway_resource.catalog_proxy.id
  http_method = aws_api_gateway_method.catalog.http_method
  
  integration_http_method = "ANY"
  type                    = "HTTP_PROXY"
  uri                     = "${var.catalog_service_url}/{proxy}"
  connection_type         = "INTERNET"

  timeout_milliseconds = 29000

  request_parameters = {
    "integration.request.path.proxy" = "method.request.path.proxy"
  }
}

resource "aws_api_gateway_integration" "catalog_options" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  resource_id = aws_api_gateway_resource.catalog_proxy.id
  http_method = aws_api_gateway_method.catalog_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "catalog_options" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  resource_id = aws_api_gateway_resource.catalog_proxy.id
  http_method = aws_api_gateway_method.catalog_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "catalog_options" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  resource_id = aws_api_gateway_resource.catalog_proxy.id
  http_method = aws_api_gateway_method.catalog_options.http_method
  status_code = aws_api_gateway_method_response.catalog_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Authorization,Content-Type,X-Requested-With'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'https://gamificator.click'"
  }
}

# ============================================
# INSTALLATION SERVICE ROUTES
# ============================================

resource "aws_api_gateway_resource" "installations" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "installations"
}

resource "aws_api_gateway_resource" "installations_proxy" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  parent_id   = aws_api_gateway_resource.installations.id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "installations" {
  rest_api_id   = aws_api_gateway_rest_api.cathouse_api.id
  resource_id   = aws_api_gateway_resource.installations_proxy.id
  http_method   = "ANY"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.proxy" = true
  }
}

resource "aws_api_gateway_method" "installations_options" {
  rest_api_id   = aws_api_gateway_rest_api.cathouse_api.id
  resource_id   = aws_api_gateway_resource.installations_proxy.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "installations" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  resource_id = aws_api_gateway_resource.installations_proxy.id
  http_method = aws_api_gateway_method.installations.http_method
  
  integration_http_method = "ANY"
  type                    = "HTTP_PROXY"
  uri                     = "${var.installation_service_url}/{proxy}"
  connection_type         = "INTERNET"

  timeout_milliseconds = 29000

  request_parameters = {
    "integration.request.path.proxy" = "method.request.path.proxy"
  }
}

resource "aws_api_gateway_integration" "installations_options" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  resource_id = aws_api_gateway_resource.installations_proxy.id
  http_method = aws_api_gateway_method.installations_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "installations_options" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  resource_id = aws_api_gateway_resource.installations_proxy.id
  http_method = aws_api_gateway_method.installations_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "installations_options" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  resource_id = aws_api_gateway_resource.installations_proxy.id
  http_method = aws_api_gateway_method.installations_options.http_method
  status_code = aws_api_gateway_method_response.installations_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Authorization,Content-Type,X-Requested-With'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'https://gamificator.click'"
  }
}

# ============================================
# PROXY SERVICE ROUTES
# ============================================

resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "proxy"
}

resource "aws_api_gateway_resource" "proxy_proxy" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  parent_id   = aws_api_gateway_resource.proxy.id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = aws_api_gateway_rest_api.cathouse_api.id
  resource_id   = aws_api_gateway_resource.proxy_proxy.id
  http_method   = "ANY"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.proxy" = true
  }
}

resource "aws_api_gateway_method" "proxy_options" {
  rest_api_id   = aws_api_gateway_rest_api.cathouse_api.id
  resource_id   = aws_api_gateway_resource.proxy_proxy.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  resource_id = aws_api_gateway_resource.proxy_proxy.id
  http_method = aws_api_gateway_method.proxy.http_method
  
  integration_http_method = "ANY"
  type                    = "HTTP_PROXY"
  uri                     = "${var.proxy_service_url}/{proxy}"
  connection_type         = "INTERNET"

  timeout_milliseconds = 29000

  request_parameters = {
    "integration.request.path.proxy" = "method.request.path.proxy"
  }
}

resource "aws_api_gateway_integration" "proxy_options" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  resource_id = aws_api_gateway_resource.proxy_proxy.id
  http_method = aws_api_gateway_method.proxy_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "proxy_options" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  resource_id = aws_api_gateway_resource.proxy_proxy.id
  http_method = aws_api_gateway_method.proxy_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "proxy_options" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  resource_id = aws_api_gateway_resource.proxy_proxy.id
  http_method = aws_api_gateway_method.proxy_options.http_method
  status_code = aws_api_gateway_method_response.proxy_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Authorization,Content-Type,X-Requested-With'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'https://gamificator.click'"
  }
}

# ============================================
# HEALTH CHECK ROUTES
# ============================================

resource "aws_api_gateway_method" "health" {
  rest_api_id   = aws_api_gateway_rest_api.cathouse_api.id
  resource_id   = aws_api_gateway_resource.health.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "health" {
  rest_api_id = aws_api_gateway_rest_api.cathouse_api.id
  resource_id = aws_api_gateway_resource.health.id
  http_method = aws_api_gateway_method.health.http_method
  
  integration_http_method = "GET"
  type                    = "HTTP_PROXY"
  uri                     = "${var.health_aggregator_url}/health"
  connection_type         = "INTERNET"

  timeout_milliseconds = 10000
}
