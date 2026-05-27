# ABOUTME: Outputs for the comparison_lambda module.
# ABOUTME: Exposes the function name and the dead-letter queue URL.
# SPDX-License-Identifier: Apache-2.0

output "function_name" {
  description = "Name of the comparison Lambda function."
  value       = aws_lambda_function.this.function_name
}

output "dlq_url" {
  description = "URL of the comparison dead-letter queue."
  value       = aws_sqs_queue.dlq.url
}
