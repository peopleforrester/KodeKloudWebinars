# ABOUTME: Dev environment outputs, surfaced to the deploy workflow and audit trail.

output "endpoint_name" {
  description = "Name of the deployed dev endpoint."
  value       = module.endpoint.endpoint_name
}

output "endpoint_arn" {
  description = "ARN of the deployed dev endpoint."
  value       = module.endpoint.endpoint_arn
}

output "vpc_id" {
  description = "ID of the dev VPC."
  value       = module.networking.vpc_id
}
