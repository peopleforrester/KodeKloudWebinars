# Module: `networking`

Creates a VPC with two private subnets across two availability zones and the four
interface VPC endpoints the inference stack needs, so SageMaker and ECR traffic
stays on the AWS network fabric and never traverses the public internet.

## Inputs

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | string | yes | — | Name prefix for all resources. |
| `aws_region` | string | no | `us-east-1` | Region used to build endpoint service names. |
| `vpc_cidr` | string | no | `10.0.0.0/16` | VPC CIDR block. |
| `private_subnet_cidrs` | list(string) | no | `["10.0.1.0/24","10.0.2.0/24"]` | Exactly two subnet CIDRs. |
| `availability_zones` | list(string) | no | `["us-east-1a","us-east-1b"]` | Exactly two AZs. |

## Outputs

| Name | Description |
|---|---|
| `vpc_id` | ID of the created VPC. |
| `private_subnet_ids` | IDs of the two private subnets. |
| `endpoint_security_group_id` | SG attached to the VPC endpoints; reusable for the SageMaker ENIs. |

## Interface VPC endpoints created

- `com.amazonaws.<region>.sagemaker.api`
- `com.amazonaws.<region>.sagemaker.runtime`
- `com.amazonaws.<region>.ecr.api`
- `com.amazonaws.<region>.ecr.dkr`

All four are attached to the same private subnets the SageMaker endpoint runs in,
with `private_dns_enabled = true` so the standard service hostnames resolve to
private IPs.
