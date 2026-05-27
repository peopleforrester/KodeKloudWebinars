# ABOUTME: Input variables for the per-attendee monitoring (alarms + SNS) module.
# ABOUTME: One Terraform workspace per attendee; mirrors infra/variables.tf naming.

variable "attendee_id" {
  description = "Attendee sandbox id, e.g. lab-007."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]{3,40}$", var.attendee_id))
    error_message = "attendee_id must be 3-40 chars of lowercase letters, digits, or hyphens."
  }
}

variable "region" {
  description = "AWS region."
  type        = string
  default     = "us-east-1"
}

variable "alarm_email" {
  description = "Optional email to subscribe to the (non-paging) SNS topic. Empty = no subscription."
  type        = string
  default     = ""
}
