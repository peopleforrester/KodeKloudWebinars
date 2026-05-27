# ABOUTME: Drop-in fallback image using distilGPT-2 instead of TinyLlama. Same server.py,
# ABOUTME: same request/response contract — used if Hugging Face rate-limits TinyLlama.
#
# Identical to Dockerfile except the baked-in MODEL_ID/MODEL_LABEL. distilGPT-2 is ~350 MB
# and far less likely to be rate-limited; it produces weaker text but the same schema, which
# is all the cost-attribution exercise needs. Build it the same way:
#   docker buildx build -f distilgpt2-fallback.Dockerfile --platform linux/amd64,linux/arm64 ...

FROM --platform=$TARGETPLATFORM python:3.12-slim AS builder

ARG MODEL_ID="distilbert/distilgpt2"
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/models

WORKDIR /build
COPY pyproject.toml ./

RUN pip install --target=/install \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        "kserve==0.16.*" "transformers==4.50.*" "torch==2.5.*" \
        "fastapi==0.115.*" "accelerate==1.*" "safetensors==0.4.*"

RUN PYTHONPATH=/install python -c "\
from transformers import AutoModelForCausalLM, AutoTokenizer; \
m='${MODEL_ID}'; \
AutoTokenizer.from_pretrained(m); \
AutoModelForCausalLM.from_pretrained(m)"

FROM --platform=$TARGETPLATFORM python:3.12-slim AS runtime

ARG MODEL_ID="distilbert/distilgpt2"
ARG MODEL_LABEL="distilgpt2"
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/install \
    HF_HOME=/models \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    MODEL_ID=${MODEL_ID} \
    MODEL_LABEL=${MODEL_LABEL} \
    MODEL_NAME=tinyllama-completion

RUN useradd --create-home --uid 1000 kserve
WORKDIR /app

COPY --from=builder /install /install
COPY --from=builder /models /models
COPY server.py health.py /app/

RUN chown -R kserve:kserve /app /models
USER kserve

EXPOSE 8080
ENTRYPOINT ["python", "server.py"]
