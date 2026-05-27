# ABOUTME: S3 remote state backend for the dev environment. The bucket is supplied at
# ABOUTME: init time (partial config) so it can be templated per account/CI run.

terraform {
  backend "s3" {
    # Bucket is intentionally omitted here and supplied by CI at init, e.g.:
    #   terraform init -backend-config="bucket=${TF_STATE_BUCKET}"
    key     = "nfcu-session-1/dev/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}
