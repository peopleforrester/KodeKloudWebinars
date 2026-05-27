# ABOUTME: Input variables for the networking module (VPC, private subnets, VPC endpoints).

variable "name" {
  description = "Name prefix applied to all networking resources."
  type        = string
}

variable "aws_region" {
  description = "AWS region; used to construct VPC endpoint service names."
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for the two private subnets (one per AZ)."
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]

  validation {
    condition     = length(var.private_subnet_cidrs) == 2
    error_message = "Exactly two private subnet CIDRs are required (two AZs)."
  }
}

variable "availability_zones" {
  description = "Two availability zones for the private subnets."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]

  validation {
    condition     = length(var.availability_zones) == 2
    error_message = "Exactly two availability zones are required."
  }
}
