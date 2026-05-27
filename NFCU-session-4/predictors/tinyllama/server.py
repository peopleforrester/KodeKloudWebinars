#!/usr/bin/env python3
# ABOUTME: Custom KServe predictor serving TinyLlama 1.1B on CPU via transformers.
# ABOUTME: Input {"prompt", "max_tokens"} -> {"completion", "model", "tokens_generated"}.
"""KServe Model implementation for the Session 4 LLM lab.

A custom predictor (not KServe's vLLM-backed HuggingFace runtime, which is GPU-only) so
the input/output schema matches the attendee-guide curl examples exactly and the image
stays small and CPU-friendly. The same file backs the distilGPT-2 fallback image — only
the MODEL_ID env var differs.
"""

from __future__ import annotations

import logging
import os
from typing import Dict, Union

import torch
from kserve import InferRequest, Model, ModelServer
from transformers import AutoModelForCausalLM, AutoTokenizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger("tinyllama-predictor")

# Overridable so the same code serves distilGPT-2 (fallback image sets MODEL_ID/MODEL_LABEL).
MODEL_ID = os.environ.get("MODEL_ID", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
MODEL_LABEL = os.environ.get("MODEL_LABEL", "tinyllama-1.1b")
DEFAULT_MAX_TOKENS = 50
MAX_TOKENS_CAP = 256


class TinyLlamaModel(Model):
    """Serves greedy text completions from a small causal-LM on CPU."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.name = name
        self.tokenizer = None
        self.model = None
        self.ready = False
        self.load()

    def load(self) -> bool:
        """Load tokenizer and weights into memory. Sets self.ready when done.

        Weights are baked into the image at build time, so this reads from local disk
        and does not hit Hugging Face at runtime.

        Returns:
            True once the model is ready to serve.
        """
        logger.info("Loading model '%s' on CPU...", MODEL_ID)
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        self.model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype=torch.float32)
        self.model.eval()
        self.ready = True
        logger.info("Model '%s' loaded; ready to serve.", MODEL_LABEL)
        return self.ready

    def _extract_request(self, payload: Union[Dict, InferRequest]) -> Dict:
        """Normalize v1 (`{"prompt": ...}` or `{"instances": [...]}`) request bodies."""
        if isinstance(payload, dict):
            if "instances" in payload and payload["instances"]:
                return payload["instances"][0]
            return payload
        # InferRequest (v2) — pull the first input's data as the prompt.
        raise ValueError("This predictor expects the v1 protocol with a JSON 'prompt'.")

    def predict(
        self, payload: Union[Dict, InferRequest], headers: Dict[str, str] = None
    ) -> Dict:
        """Generate a completion for the prompt.

        Args:
            payload: v1 request body containing 'prompt' and optional 'max_tokens'.
            headers: Request headers (unused).

        Returns:
            ``{"completion": str, "model": str, "tokens_generated": int}``.

        Raises:
            ValueError: If 'prompt' is missing.
        """
        request = self._extract_request(payload)
        prompt = request.get("prompt")
        if not prompt:
            raise ValueError("Request must include a non-empty 'prompt'.")
        max_tokens = min(int(request.get("max_tokens", DEFAULT_MAX_TOKENS)), MAX_TOKENS_CAP)

        inputs = self.tokenizer(prompt, return_tensors="pt")
        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=False,  # greedy => deterministic, so the guide's examples stay valid
                pad_token_id=self.tokenizer.eos_token_id,
            )
        generated = output[0][inputs["input_ids"].shape[1]:]
        completion = self.tokenizer.decode(generated, skip_special_tokens=True)

        return {
            "completion": completion,
            "model": MODEL_LABEL,
            "tokens_generated": int(generated.shape[0]),
        }


if __name__ == "__main__":
    model = TinyLlamaModel(os.environ.get("MODEL_NAME", "tinyllama-completion"))
    ModelServer().start([model])
