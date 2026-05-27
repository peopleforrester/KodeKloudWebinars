# ABOUTME: Outputs for the traffic_generator_lambda module.
# ABOUTME: Exposes the function name for manual invocation.
# SPDX-License-Identifier: Apache-2.0

output "function_name" {
  description = "Name of the traffic-generator Lambda function."
  value       = aws_lambda_function.this.function_name
}
