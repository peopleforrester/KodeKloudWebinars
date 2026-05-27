#!/usr/bin/env bash
# ABOUTME: Provision one attendee's Session 2 lab environment via Terraform.
# ABOUTME: Idempotent (terraform apply); prints the API Gateway and dashboard URLs.
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

attendee="${1:?usage: provision-attendee.sh <attendee-id>}"
region="${AWS_REGION:-us-east-1}"
cd "$(dirname "$0")/../terraform"

terraform init -input=false
terraform apply -auto-approve -var="attendee_id=${attendee}"

invoke_url=$(terraform output -raw shadow_mirror_invoke_url)
dashboard=$(terraform output -raw dashboard_name)
echo "API Gateway URL : ${invoke_url}"
echo "Dashboard       : https://${region}.console.aws.amazon.com/cloudwatch/home?region=${region}#dashboards:name=${dashboard}"
