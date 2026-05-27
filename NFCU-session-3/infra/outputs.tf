# ABOUTME: Outputs for the per-attendee NFCU Session 3 infrastructure.
# ABOUTME: Consumed by the lab guide, provisioning workflow, and readiness checks.

output "baseline_bucket" {
  description = "Bucket holding reference.parquet for this attendee."
  value       = aws_s3_bucket.baseline.bucket
}

output "drift_reports_bucket" {
  description = "Bucket receiving Evidently HTML reports."
  value       = aws_s3_bucket.drift_reports.bucket
}

output "drift_detector_function" {
  description = "drift-detector Lambda name."
  value       = aws_lambda_function.drift_detector.function_name
}

output "lambda_functions" {
  description = "All five Session 3 Lambda function names."
  value = [
    aws_lambda_function.drift_detector.function_name,
    aws_lambda_function.drift_simulator.function_name,
    aws_lambda_function.incident_simulator.function_name,
    aws_lambda_function.evidently_runner.function_name,
    aws_lambda_function.nannyml_runner.function_name,
  ]
}

output "drift_detector_schedule" {
  description = "EventBridge schedule expression for the detector."
  value       = aws_cloudwatch_event_rule.drift_detector_schedule.schedule_expression
}

output "attendee_invoke_policy_arn" {
  description = "Policy ARN granting the attendee invoke rights on the five Lambdas."
  value       = aws_iam_policy.attendee_invoke.arn
}
