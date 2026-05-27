# ABOUTME: Per-attendee CloudWatch alarms (3) + a visible, non-paging SNS topic.
# ABOUTME: Drift-PSI (any feature > 0.25), Latency-P95 (>500ms), ErrorRate (5xx>1%).

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

locals {
  prefix        = "workshop-lab-${var.attendee_id}"
  endpoint_name = "${local.prefix}-production"
  variant_name  = "AllTraffic"
  features = [
    "age", "workclass", "education_num", "marital_status",
    "occupation", "race", "sex", "hours_per_week",
  ]
  common_tags = {
    Project    = "nfcu-session-3"
    Session    = "monitoring"
    AttendeeId = var.attendee_id
    ManagedBy  = "terraform"
  }
}

# ---------------------------------------------------------------------------
# SNS topic — visible in the lab dashboard, NOT wired to external paging.
# ---------------------------------------------------------------------------
resource "aws_sns_topic" "alerts" {
  name = "${local.prefix}-alerts"
  tags = local.common_tags
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alarm_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# ---------------------------------------------------------------------------
# 1) Drift-PSI: ALARM when the MAX PSI across the eight features exceeds 0.25.
#    The drift-detector also force-sets this alarm (workshop shortcut D3) for
#    fast feedback; this metric-math definition makes the alarm meaningful on
#    its own as well.
# ---------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "drift_psi" {
  alarm_name          = "Drift-PSI-${var.attendee_id}"
  alarm_description   = "Any feature PSI > 0.25 for ${var.attendee_id}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = 0.25
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  tags                = local.common_tags

  metric_query {
    id          = "max_psi"
    expression  = "MAX([${join(",", [for i in range(length(local.features)) : "f${i}"])}])"
    label       = "Max feature PSI"
    return_data = true
  }

  dynamic "metric_query" {
    for_each = { for i, f in local.features : "f${i}" => f }
    content {
      id          = metric_query.key
      return_data = false
      metric {
        namespace   = "NFCU/Session3"
        metric_name = "DriftPSI"
        period      = 120
        stat        = "Maximum"
        dimensions = {
          AttendeeId = var.attendee_id
          Feature    = metric_query.value
        }
      }
    }
  }
}

# ---------------------------------------------------------------------------
# 2) Latency-P95: ALARM when p95 ModelLatency > 500ms.
#    SageMaker ModelLatency is reported in MICROSECONDS, so 500ms = 500000.
# ---------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "latency_p95" {
  alarm_name          = "Latency-P95-${var.attendee_id}"
  alarm_description   = "p95 ModelLatency > 500ms for ${var.attendee_id}"
  namespace           = "AWS/SageMaker"
  metric_name         = "ModelLatency"
  extended_statistic  = "p95"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  period              = 60
  threshold           = 500000 # microseconds == 500 ms
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  dimensions = {
    EndpointName = local.endpoint_name
    VariantName  = local.variant_name
  }
  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# 3) ErrorRate: ALARM when 5XX errors exceed 1% of invocations.
# ---------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "error_rate" {
  alarm_name          = "ErrorRate-${var.attendee_id}"
  alarm_description   = "5XX error rate > 1% for ${var.attendee_id}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = 1
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  tags                = local.common_tags

  metric_query {
    id          = "error_pct"
    expression  = "100 * (errors / invocations)"
    label       = "5XX error rate (%)"
    return_data = true
  }
  metric_query {
    id          = "errors"
    return_data = false
    metric {
      namespace   = "AWS/SageMaker"
      metric_name = "Invocation5XXErrors"
      period      = 60
      stat        = "Sum"
      dimensions  = { EndpointName = local.endpoint_name, VariantName = local.variant_name }
    }
  }
  metric_query {
    id          = "invocations"
    return_data = false
    metric {
      namespace   = "AWS/SageMaker"
      metric_name = "Invocations"
      period      = 60
      stat        = "Sum"
      dimensions  = { EndpointName = local.endpoint_name, VariantName = local.variant_name }
    }
  }
}

output "alarm_names" {
  description = "The three per-attendee alarm names."
  value = [
    aws_cloudwatch_metric_alarm.drift_psi.alarm_name,
    aws_cloudwatch_metric_alarm.latency_p95.alarm_name,
    aws_cloudwatch_metric_alarm.error_rate.alarm_name,
  ]
}

output "sns_topic_arn" {
  description = "Visible (non-paging) SNS topic ARN."
  value       = aws_sns_topic.alerts.arn
}
