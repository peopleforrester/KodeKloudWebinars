#!/usr/bin/env bash
# ABOUTME: Tear down one attendee's Session 2 lab, PRESERVING the audit bucket.
# ABOUTME: Destroys every tracked resource except the shared audit_trail module.
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

attendee="${1:?usage: teardown-attendee.sh <attendee-id>}"
cd "$(dirname "$0")/../terraform"

terraform init -input=false

# Destroy everything except the audit_trail module so promotion/rollback
# evidence survives teardown (see specs/audit-trail: "Audit Bucket Survives
# Teardown"). Targets are enumerated dynamically so this stays name-agnostic.
mapfile -t targets < <(terraform state list | grep -v 'module.audit_trail' || true)

if [[ ${#targets[@]} -eq 0 ]]; then
  echo "Nothing to tear down for ${attendee} (audit bucket, if any, is preserved)."
  exit 0
fi

args=()
for addr in "${targets[@]}"; do
  args+=("-target=${addr}")
done

terraform destroy -auto-approve "${args[@]}" -var="attendee_id=${attendee}"
echo "Teardown complete for ${attendee}. Audit bucket preserved."
