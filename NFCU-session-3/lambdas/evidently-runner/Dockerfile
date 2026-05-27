# ABOUTME: Container image for the evidently-runner Lambda (Evidently 0.7.x).
# ABOUTME: Based on the AWS Lambda Python 3.11 base image; 1024 MB at deploy time.
FROM public.ecr.aws/lambda/python:3.11

# Dependencies (pinned Evidently per D1 / PIN_VERIFICATION.md).
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Handler source.
COPY handler.py ${LAMBDA_TASK_ROOT}/

# Lambda entry point: <file>.<function>
CMD [ "handler.handler" ]
