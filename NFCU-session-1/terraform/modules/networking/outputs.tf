# ABOUTME: Outputs for the networking module, consumed by the SageMaker endpoint module.

output "vpc_id" {
  description = "ID of the created VPC."
  value       = aws_vpc.this.id
}

output "private_subnet_ids" {
  description = "IDs of the two private subnets the endpoint runs in."
  value       = aws_subnet.private[*].id
}

output "endpoint_security_group_id" {
  description = "Security group ID attached to the interface VPC endpoints and reusable for the SageMaker ENIs."
  value       = aws_security_group.endpoints.id
}
