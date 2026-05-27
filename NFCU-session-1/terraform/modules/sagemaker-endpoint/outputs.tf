# ABOUTME: Outputs for the sagemaker-endpoint module, consumed by environment
# ABOUTME: compositions and the production audit trail.

output "endpoint_name" {
  description = "Name of the deployed SageMaker endpoint."
  value       = aws_sagemaker_endpoint.this.name
}

output "endpoint_arn" {
  description = "ARN of the deployed SageMaker endpoint (recorded in the audit trail)."
  value       = aws_sagemaker_endpoint.this.arn
}

output "model_name" {
  description = "Name of the SageMaker model resource."
  value       = aws_sagemaker_model.this.name
}

output "endpoint_config_name" {
  description = "Name of the SageMaker endpoint configuration."
  value       = aws_sagemaker_endpoint_configuration.this.name
}
