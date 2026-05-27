# ABOUTME: Input variables for the shared audit_trail module.
# ABOUTME: attendee_id scopes the bucket name; tags carry cost-attribution metadata.
# SPDX-License-Identifier: Apache-2.0

variable "attendee_id" {
  description = "Per-attendee identifier; scopes the audit bucket name."
  type        = string
}

variable "tags" {
  description = "Tags applied to the audit bucket for cost attribution and teardown."
  type        = map(string)
  default     = {}
}
