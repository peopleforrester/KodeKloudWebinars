# MANUAL APPLY ONLY. Do not run from CI.
# This Terraform provisions the demo sandbox; the workshop pipeline workflows assume these resources exist.
# ABOUTME: Input variables for the lab sandbox; defaults target the canonical demo repo.

variable "github_org" {
  description = "GitHub org/owner allowed to assume the workflow role. Attendees set their own fork owner."
  type        = string
  default     = "peopleforrester"
}

variable "github_repo" {
  description = "GitHub repository name allowed to assume the workflow role."
  type        = string
  default     = "KodeKloudWebinars"
}

variable "aws_region" {
  description = "AWS region for all sandbox resources."
  type        = string
  default     = "us-east-1"
}

variable "name" {
  description = "Name prefix for all sandbox resources."
  type        = string
  default     = "nfcu-session-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the sandbox VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for the two private subnets (one per AZ)."
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "availability_zones" {
  description = "Two availability zones for the private subnets."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}
