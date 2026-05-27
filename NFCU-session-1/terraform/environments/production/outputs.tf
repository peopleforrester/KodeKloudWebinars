# ABOUTME: Dev environment outputs, surfaced to the deploy workflow and audit trail.

output "endpoint_name" {
  description = "Name of the deployed production endpoint."
  value       = module.endpoint.endpoint_name
}

output "endpoint_arn" {
  description = "ARN of the deployed production endpoint."
  value       = module.endpoint.endpoint_arn
}

output "vpc_id" {
  description = "ID of the production VPC."
  value       = module.networking.vpc_id
}
