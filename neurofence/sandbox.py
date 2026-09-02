"""
ModelSandbox — safe offline loading and inference wrapper for local HF models.

Compatible with: transformers >= 5.x  (uses `dtype=` not deprecated `torch_dtype=`)
"""

import logging
import os
from typing import Optional

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig

logger = logging.getLogger(__name__)

_MAX_LENGTH = 256


class ModelSandbox:
    """Load a local Hugging Face model directory and expose safe inference.

    Supports any causal-LM architecture (LLaMA, Qwen2, Mistral, GPT-2, …).
    """

    def __init__(self, model_path: str, device: Optional[str] = None) -> None:
        self.model_path = model_path
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForCausalLM] = None
        self._config = None

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(self) -> "ModelSandbox":
        """Load tokeniser and model weights from *model_path*.

        Raises
        ------
        FileNotFoundError
            If *model_path* does not exist.
        RuntimeError
            If weights cannot be loaded.
        """
        if not os.path.isdir(self.model_path):
            raise FileNotFoundError(
                f"Model directory not found: {self.model_path}"
            )

        logger.info("Loading config from %s", self.model_path)
        self._config = AutoConfig.from_pretrained(
            self.model_path, local_files_only=True
        )

        logger.info("Loading tokeniser from %s", self.model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            local_files_only=True,
        )

        # Many decoder-only models (GPT-2, some LLaMA variants) ship without
        # a pad token — assign eos_token so batched tokenisation doesn't warn.
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        logger.info(
            "Loading model weights from %s (device=%s)", self.model_path, self.device
        )
        # transformers >= 5.x uses `dtype=` instead of `torch_dtype=`
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            local_files_only=True,
            dtype=torch.float32,
            device_map=None,
            low_cpu_mem_usage=True,
        )
        self.model.to(self.device)
        self.model.eval()

        n_params = sum(p.numel() for p in self.model.parameters())
        logger.info("Model loaded — %d parameters", n_params)
        return self

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def tokenize(self, text: str) -> dict:
        """Tokenise *text* and return tensors on the model device."""
        return self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=_MAX_LENGTH,
            padding=True,
        ).to(self.device)

    @torch.no_grad()
    def forward(self, text: str):
        """Single forward pass; returns the model output mapping."""
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded — call .load() first.")
        batch = self.tokenize(text)
        return self.model(**batch, output_hidden_states=True, return_dict=True)

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def model_info(self) -> dict:
        """Return lightweight metadata dict about the loaded model."""
        if self.model is None:
            return {}
        cfg = self._config
        n_params = sum(p.numel() for p in self.model.parameters())
        return {
            "path": self.model_path,
            "device": self.device,
            "num_parameters": n_params,
            "model_type": getattr(cfg, "model_type", "unknown") if cfg else "unknown",
            "hidden_size": getattr(cfg, "hidden_size", None) if cfg else None,
            "num_layers": getattr(cfg, "num_hidden_layers", None) if cfg else None,
        }

    def inspect_safetensors(self, safetensors_path: str) -> dict:
        """Return keys and shapes from a .safetensors file (zero-copy)."""
        from safetensors import safe_open

        info: dict = {"keys": [], "shapes": []}
        with safe_open(safetensors_path, framework="pt", device="cpu") as f:
            for k in f.keys():
                info["keys"].append(k)
                info["shapes"].append(list(f.get_tensor(k).shape))
        return info
