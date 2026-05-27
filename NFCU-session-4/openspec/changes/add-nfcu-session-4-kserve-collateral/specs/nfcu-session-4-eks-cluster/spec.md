# nfcu-session-4-eks-cluster

## ADDED Requirements

### Requirement: Terraform module provisions a working EKS cluster

`cluster/eks/terraform/` SHALL contain a Terraform module that provisions an EKS cluster suitable for running labs 1–4 with one `terraform apply`.

#### Scenario: Speaker provisions cluster from cold
- **GIVEN** an AWS account with appropriate IAM permissions, Terraform ≥1.10 installed, and the example tfvars copied to `terraform.tfvars`
- **WHEN** the speaker runs `cd cluster/eks && bash up.sh`
- **THEN** within 25 minutes the EKS cluster reports ACTIVE
- **AND** the node group is `Active` with desired capacity
- **AND** `outputs.tf` produces a working `aws eks update-kubeconfig` command

### Requirement: Cluster sizing is appropriate for the demo

The default node group SHALL run `m5.xlarge` instances with `desired_size=2` and `max_size=5`.

#### Scenario: Default sizing supports labs 1–4
- **GIVEN** the cluster is provisioned with default tfvars
- **WHEN** all four lab manifests are applied and traffic is generated
- **THEN** the cluster autoscaler scales node count as needed
- **AND** no pod is stuck Pending due to resource pressure for more than 5 minutes

### Requirement: IRSA roles support KServe storage and AWS Load Balancer Controller

Terraform SHALL provision IAM-roles-for-service-accounts (IRSA) for the KServe storage initializer (reading model artifacts from S3), the AWS Load Balancer Controller, and the Cluster Autoscaler.

#### Scenario: KServe pulls models from S3 without static credentials
- **GIVEN** an InferenceService with a `s3://` storageUri pointing at the Terraform-managed bucket
- **WHEN** the InferenceService is applied
- **THEN** the storage initializer succeeds without any AWS access keys in the cluster
- **AND** the model is downloaded to the predictor pod

### Requirement: S3 bucket for model artifacts is created

Terraform SHALL provision an S3 bucket whose name is exposed via outputs, intended to hold the v1.0.0 and v1.0.1 XGBoost model artifacts.

#### Scenario: Models are uploaded to S3 from terraform output
- **GIVEN** the cluster is provisioned
- **WHEN** the speaker runs `bash manifests/model-artifacts/upload-to-s3.sh`
- **THEN** the script reads the bucket name from `terraform output -raw model_artifacts_bucket_name`
- **AND** both model versions are uploaded to the expected S3 keys

### Requirement: Teardown is destructive and safety-gated

`cluster/eks/down.sh` SHALL fully destroy the cluster but require the user to type the cluster name as confirmation.

#### Scenario: Accidental teardown is prevented
- **GIVEN** the user runs `bash cluster/eks/down.sh`
- **WHEN** they do not type the exact cluster name
- **THEN** the script exits without invoking `terraform destroy`

#### Scenario: Confirmed teardown completes cleanly
- **GIVEN** the user runs `bash cluster/eks/down.sh` and types the cluster name correctly
- **WHEN** Terraform destroy completes
- **THEN** no AWS resources from the module remain
- **AND** the next `aws eks list-clusters` does not list the cluster

### Requirement: Cost estimate is anchored in the runbook

`runbook/speaker-aws-spend.md` SHALL document the expected cost of an 8-hour rehearsal-plus-session window with default sizing.

#### Scenario: Speaker knows what to expect on the AWS bill
- **GIVEN** the speaker reads the spend doc before provisioning
- **WHEN** they finish reading
- **THEN** they have a concrete dollar range and the line-item breakdown (EKS control plane, node hours, NLB, EBS, NAT gateway)
