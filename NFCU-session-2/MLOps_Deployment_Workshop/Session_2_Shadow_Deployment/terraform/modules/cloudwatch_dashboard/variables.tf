# ABOUTME: Inputs for the cloudwatch_dashboard module.
# ABOUTME: attendee_id names the dashboard; aws_region scopes the metric widgets.
# SPDX-License-Identifier: Apache-2.0

variable "attendee_id" {
  description = "Per-attendee identifier; names the dashboard."
  type        = string
}

variable "aws_region" {
  description = "AWS region the metrics are published in."
  type        = string
}
