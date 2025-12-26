output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = aws_api_gateway_stage.prod.invoke_url
}

output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = aws_api_gateway_rest_api.cathouse_api.id
}

output "api_gateway_stage" {
  description = "Stage name of the API Gateway"
  value       = aws_api_gateway_stage.prod.stage_name
}

output "api_gateway_arn" {
  description = "ARN of the API Gateway"
  value       = aws_api_gateway_rest_api.cathouse_api.arn
}

output "usage_plan_general_id" {
  description = "ID of the general usage plan"
  value       = aws_api_gateway_usage_plan.general.id
}

output "usage_plan_authenticated_id" {
  description = "ID of the authenticated usage plan"
  value       = aws_api_gateway_usage_plan.authenticated.id
}
