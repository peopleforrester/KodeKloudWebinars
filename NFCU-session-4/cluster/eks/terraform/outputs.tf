# ABOUTME: Outputs the speaker needs after apply — kubeconfig command, bucket name,
# ABOUTME: and the three IRSA role ARNs the add-ons bootstrap annotates onto ServiceAccounts.

output "cluster_name" {
  description = "EKS cluster name."
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS API server endpoint."
  value       = module.eks.cluster_endpoint
}

output "region" {
  description = "AWS region the cluster runs in."
  value       = var.region
}

output "update_kubeconfig_command" {
  description = "Run this to point kubectl at the new cluster."
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}

output "model_artifacts_bucket_name" {
  description = "S3 bucket holding the XGBoost model artifacts. Consumed by upload-to-s3.sh."
  value       = aws_s3_bucket.model_artifacts.bucket
}

output "kserve_s3_role_arn" {
  description = "Pod Identity role ARN for the KServe storage initializer. The lab platform creates one pod-identity association per attendee namespace using this role."
  value       = module.pod_identity_kserve_s3.iam_role_arn
}

output "alb_controller_role_arn" {
  description = "Pod Identity role ARN for the AWS Load Balancer Controller (kube-system:aws-load-balancer-controller)."
  value       = module.pod_identity_alb_controller.iam_role_arn
}

output "cluster_autoscaler_role_arn" {
  description = "Pod Identity role ARN for the Cluster Autoscaler (kube-system:cluster-autoscaler)."
  value       = module.pod_identity_cluster_autoscaler.iam_role_arn
}
