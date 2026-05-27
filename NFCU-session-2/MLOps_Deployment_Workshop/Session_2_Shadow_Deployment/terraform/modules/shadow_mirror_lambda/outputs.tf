# ABOUTME: Outputs for the shadow_mirror_lambda module.
# ABOUTME: Exposes the POST /predict invoke URL and the function name.
# SPDX-License-Identifier: Apache-2.0

output "invoke_url" {
  description = "Full HTTPS invoke URL for POST /predict."
  value       = "${aws_apigatewayv2_stage.default.invoke_url}/predict"
}

output "function_name" {
  description = "Name of the shadow-mirror Lambda function."
  value       = aws_lambda_function.this.function_name
}
