# Module: `sagemaker-endpoint`

Provisions a single VPC-isolated, KMS-encrypted SageMaker real-time inference
endpoint from a digest-pinned container image and a caller-supplied execution role.

## Inputs

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | string | yes | — | Base name for the model, endpoint config, and endpoint. |
| `model_data_url` | string | yes | — | S3 URI of the model artifact tarball. |
| `container_image_uri` | string | yes | — | Inference image, **digest-referenced** (`…@sha256:<64 hex>`). Validated. |
| `execution_role_arn` | string | yes | — | IAM role SageMaker assumes. |
| `vpc_subnet_ids` | list(string) | yes | — | Private subnet IDs the endpoint runs in. |
| `vpc_security_group_ids` | list(string) | yes | — | Security groups for the endpoint ENIs. |
| `kms_key_arn` | string | yes | — | KMS key for volume encryption and model-data decryption. |
| `instance_type` | string | no | `ml.t3.medium` | Hosting instance type. |
| `instance_count` | number | no | `1` | Production-variant instance count. |

## Outputs

| Name | Description |
|---|---|
| `endpoint_name` | Name of the deployed endpoint. |
| `endpoint_arn` | ARN of the deployed endpoint (recorded in the audit trail). |
| `model_name` | Name of the SageMaker model resource. |
| `endpoint_config_name` | Name of the endpoint configuration. |

## Security guarantees

These are enforced in code, not left to the caller's documentation discipline:

- **No public ingress.** `VpcConfig.Subnets` is always set from the supplied private
  subnet IDs. The module exposes no argument that places the endpoint on a public
  network.
- **Encryption at rest.** `kms_key_arn` is set on the endpoint configuration, encrypting
  the hosting instance's storage volume.
- **Encrypted model data.** Decryption of the KMS-encrypted `ModelDataUrl` artifact is
  authorized through the execution role's `kms:Decrypt` grant on the same key ARN
  (granted in `lab-platform-iac`); the model never travels or rests unencrypted.
- **Immutable image.** `container_image_uri` is validated to be digest-referenced; a
  tag-referenced (mutable) image is rejected at plan time.
- **No shared role.** `execution_role_arn` is a required input. The module never creates
  or assumes a shared "default" role, so least-privilege is owned per deployment.
- **Bounded rollout.** `DeploymentConfig.RollingUpdatePolicy` sets
  `WaitIntervalInSeconds = 60` and `MaximumExecutionTimeoutInSeconds = 3600`; an update
  that does not converge in time is rolled back rather than left half-applied.
