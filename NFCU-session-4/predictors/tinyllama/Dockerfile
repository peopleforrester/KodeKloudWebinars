# ABOUTME: Multi-arch (amd64/arm64) CPU image for the TinyLlama KServe predictor.
# ABOUTME: Weights are baked in at build time; runtime is fully offline (HF_HUB_OFFLINE=1).

# ---- builder: install CPU deps and pre-download weights --------------------
FROM --platform=$TARGETPLATFORM python:3.12-slim AS builder

ARG MODEL_ID="TinyLlama/TinyLlama-1.1B-Chat-v1.0"
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/models

WORKDIR /build
COPY pyproject.toml ./

# Install CPU torch from the PyTorch CPU index, plus the rest from PyPI, into /install.
RUN pip install --target=/install \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        "kserve==0.16.*" "transformers==4.50.*" "torch==2.5.*" \
        "fastapi==0.115.*" "accelerate==1.*" "safetensors==0.4.*"

# Bake the weights into the image so session day never depends on Hugging Face.
RUN PYTHONPATH=/install python -c "\
from transformers import AutoModelForCausalLM, AutoTokenizer; \
m='${MODEL_ID}'; \
AutoTokenizer.from_pretrained(m); \
AutoModelForCausalLM.from_pretrained(m)"

# ---- runtime ---------------------------------------------------------------
FROM --platform=$TARGETPLATFORM python:3.12-slim AS runtime

ARG MODEL_ID="TinyLlama/TinyLlama-1.1B-Chat-v1.0"
ARG MODEL_LABEL="tinyllama-1.1b"
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/install \
    HF_HOME=/models \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    MODEL_ID=${MODEL_ID} \
    MODEL_LABEL=${MODEL_LABEL} \
    MODEL_NAME=tinyllama-completion

# Non-root user.
RUN useradd --create-home --uid 1000 kserve
WORKDIR /app

COPY --from=builder /install /install
COPY --from=builder /models /models
COPY server.py health.py /app/

RUN chown -R kserve:kserve /app /models
USER kserve

EXPOSE 8080
ENTRYPOINT ["python", "server.py"]
