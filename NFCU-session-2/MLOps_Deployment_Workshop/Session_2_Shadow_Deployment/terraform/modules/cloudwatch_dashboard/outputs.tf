# ABOUTME: Outputs for the cloudwatch_dashboard module.
# ABOUTME: Exposes the dashboard name to composing configurations.
# SPDX-License-Identifier: Apache-2.0

output "dashboard_name" {
  description = "Name of the CloudWatch dashboard."
  value       = aws_cloudwatch_dashboard.this.dashboard_name
}
