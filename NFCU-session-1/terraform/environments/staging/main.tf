# ABOUTME: Staging environment composition: wires the networking and sagemaker-endpoint
# ABOUTME: modules together with dev-scoped inputs.

provider "aws" {
  region = var.aws_region
}

module "networking" {
  source     = "../../modules/networking"
  name       = var.name
  aws_region = var.aws_region
}

module "endpoint" {
  source = "../../modules/sagemaker-endpoint"

  name                   = var.name
  model_data_url         = var.model_data_url
  container_image_uri    = var.container_image_uri
  execution_role_arn     = var.execution_role_arn
  vpc_subnet_ids         = module.networking.private_subnet_ids
  vpc_security_group_ids = [module.networking.endpoint_security_group_id]
  kms_key_arn            = var.kms_key_arn
  instance_type          = var.instance_type
}
