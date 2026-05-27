# ABOUTME: Packages the UCI Adult income model on top of the SageMaker XGBoost serving
# ABOUTME: image; pinned by digest so the deployed bytes are immutable and verifiable.

# Base image is the AWS-managed SageMaker XGBoost 1.7-1 serving container. It is
# pinned by SHA256 digest, not tag, so the image content is immutable. The "1.7-1"
# tag below is a human-readable comment only — never the resolved reference.
#
# Resolve the current digest for your region before building, e.g.:
#   aws ecr get-login-password --region us-east-1 \
#     | docker login --username AWS --password-stdin 683313688378.dkr.ecr.us-east-1.amazonaws.com
#   docker manifest inspect \
#     683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1 \
#     | jq -r '.config.digest'
# Then replace the placeholder digest below.
FROM 683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost@sha256:0000000000000000000000000000000000000000000000000000000000000000
# 1.7-1

# Path to the extracted model artifact contents, supplied by the build context.
# build-container.sh extracts model-v1.0.0.tar.gz into ./model-build/ before build.
ARG MODEL_DIR=model-build

# The SageMaker XGBoost container serves any model placed in /opt/ml/model and runs
# the script named by SAGEMAKER_PROGRAM from that directory. Copy the artifact's
# contents (model.xgb, inference.py, signature.json, metadata.json, model_card.md).
COPY ${MODEL_DIR}/ /opt/ml/model/

# Tell the SageMaker serving stack which inference handler to load.
ENV SAGEMAKER_PROGRAM=inference.py \
    SAGEMAKER_SUBMIT_DIRECTORY=/opt/ml/model

# The base image already exposes the model server (responds 200 OK on GET /ping and
# serves GET/POST /invocations on port 8080). Its ENTRYPOINT/CMD provide `serve`; we
# do not override it. Run locally with:  docker run -p 8080:8080 <image> serve
EXPOSE 8080
