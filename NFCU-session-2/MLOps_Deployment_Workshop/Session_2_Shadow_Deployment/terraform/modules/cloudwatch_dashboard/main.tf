# ABOUTME: CloudWatch dashboard with three shadow-comparison widgets.
# ABOUTME: Agreement rate (line), latency p95 delta (single value), DI ratio per group.
# SPDX-License-Identifier: Apache-2.0

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  namespace = "Workshop/Session2"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Shadow Agreement Rate"
          view   = "timeSeries"
          region = var.aws_region
          period = 300
          stat   = "Average"
          metrics = [
            [local.namespace, "ShadowAgreementRate"],
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 6
        height = 6
        properties = {
          title  = "Shadow Latency p95 Delta (%)"
          view   = "singleValue"
          region = var.aws_region
          period = 300
          stat   = "Average"
          metrics = [
            [local.namespace, "ShadowLatencyP95Delta"],
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 18
        height = 6
        properties = {
          title  = "Disparate Impact Ratio per Protected Group"
          view   = "timeSeries"
          region = var.aws_region
          period = 300
          stat   = "Average"
          metrics = [
            [{ expression = "SEARCH('{${local.namespace},ProtectedGroup} MetricName=\"ShadowDisparateImpactRatio\"', 'Average', 300)", label = "ratio", id = "e1" }],
          ]
        }
      },
    ]
  })
}

resource "aws_cloudwatch_dashboard" "this" {
  dashboard_name = "workshop-lab-${var.attendee_id}-shadow"
  dashboard_body = local.dashboard_body
}
