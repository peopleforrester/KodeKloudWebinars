# ABOUTME: Provisions a VPC-isolated, KMS-encrypted SageMaker real-time endpoint from a
# ABOUTME: digest-pinned container and a caller-supplied execution role.

# The model. Its execution role is an INPUT, by design: this module never creates
# or assumes a shared "default" role. Least-privilege is owned by the caller
# (lab-platform-iac provisions a dedicated, scoped SageMaker execution role), so a
# permissions mistake here cannot silently widen blast radius across deployments.
resource "aws_sagemaker_model" "this" {
  name               = "${var.name}-model"
  execution_role_arn = var.execution_role_arn

  primary_container {
    image          = var.container_image_uri
    model_data_url = var.model_data_url
  }

  # Always run inside the supplied private subnets. There is no configuration path
  # in this module that exposes the model to inbound public traffic.
  vpc_config {
    subnets            = var.vpc_subnet_ids
    security_group_ids = var.vpc_security_group_ids
  }
}

# Endpoint configuration. kms_key_arn encrypts the storage volume attached to the
# hosting instance. Decryption of the (KMS-encrypted) ModelDataUrl artifact in S3 is
# authorized through the execution role's kms:Decrypt grant on this same key — see
# lab-platform-iac, where the SageMaker execution role is scoped to this key ARN.
resource "aws_sagemaker_endpoint_configuration" "this" {
  name        = "${var.name}-config"
  kms_key_arn = var.kms_key_arn

  production_variants {
    variant_name           = "primary"
    model_name             = aws_sagemaker_model.this.name
    initial_instance_count = var.instance_count
    instance_type          = var.instance_type
  }
}

# The endpoint. The rolling update policy bounds how a new endpoint configuration is
# rolled out. Automatic rollback on a failed update is handled by SageMaker's managed
# deployment guardrails (auto_rollback_configuration / CloudWatch alarms); for this
# lab the rolling policy with a finite execution timeout is the rollback boundary —
# an update that does not converge within MaximumExecutionTimeoutInSeconds is rolled
# back rather than left half-applied.
resource "aws_sagemaker_endpoint" "this" {
  name                 = var.name
  endpoint_config_name = aws_sagemaker_endpoint_configuration.this.name

  deployment_config {
    rolling_update_policy {
      maximum_batch_size {
        type  = "CAPACITY_PERCENT"
        value = 100
      }
      wait_interval_in_seconds             = 60
      maximum_execution_timeout_in_seconds = 3600
    }
  }
}
