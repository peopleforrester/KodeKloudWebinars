# ABOUTME: Inputs for the shadow_log_buckets module.
# ABOUTME: attendee_id scopes bucket names; tags carry cost-attribution metadata.
# SPDX-License-Identifier: Apache-2.0

variable "attendee_id" {
  description = "Per-attendee identifier; scopes the bucket names."
  type        = string
}

variable "tags" {
  description = "Tags applied to both buckets."
  type        = map(string)
  default     = {}
}
