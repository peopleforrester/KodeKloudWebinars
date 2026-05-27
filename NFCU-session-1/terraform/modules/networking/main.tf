# ABOUTME: A VPC with two private subnets across two AZs and interface VPC endpoints for
# ABOUTME: SageMaker and ECR, so model traffic never leaves the AWS network fabric.

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.name}-vpc"
  }
}

# Two private subnets, one per AZ. No internet/NAT gateway: egress to AWS services
# is via the interface endpoints below, so nothing traverses the public internet.
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "${var.name}-private-${var.availability_zones[count.index]}"
  }
}

# Security group for the interface endpoints: allow HTTPS from within the VPC only.
resource "aws_security_group" "endpoints" {
  name        = "${var.name}-vpce-sg"
  description = "HTTPS from within the VPC to interface VPC endpoints"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "HTTPS from within the VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "Allow all egress within the VPC fabric"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name}-vpce-sg"
  }
}

# Interface VPC endpoints. The SageMaker endpoint runs in the same private subnets,
# so calls to the SageMaker control/runtime planes and to ECR resolve to private IPs.
locals {
  interface_endpoint_services = [
    "sagemaker.api",
    "sagemaker.runtime",
    "ecr.api",
    "ecr.dkr",
  ]
}

resource "aws_vpc_endpoint" "interface" {
  for_each = toset(local.interface_endpoint_services)

  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.${var.aws_region}.${each.value}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.endpoints.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.name}-vpce-${each.value}"
  }
}
