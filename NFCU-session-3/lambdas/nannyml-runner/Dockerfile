# ABOUTME: Container image for the nannyml-runner Lambda (CBPE performance estimation).
# ABOUTME: Based on the AWS Lambda Python 3.11 base image; 1024 MB at deploy time.
FROM public.ecr.aws/lambda/python:3.11

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY handler.py ${LAMBDA_TASK_ROOT}/

CMD [ "handler.handler" ]
