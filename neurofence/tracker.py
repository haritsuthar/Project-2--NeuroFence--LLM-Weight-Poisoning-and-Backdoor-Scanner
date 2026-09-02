"""
ActivationTracker — attaches PyTorch forward hooks to transformer sub-modules
and accumulates per-layer activation statistics.

Works with any Hugging Face causal-LM (LLaMA, Qwen2, Mistral, GPT-2, …).
"""

import logging
from typing import Any, Dict, List

import numpy as np
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

# ── Hook target selection ──────────────────────────────────────────────────
# We attach hooks only to "leaf-ish" modules that produce meaningful activations
# and whose full dotted name contains at least one digit (a layer index).
# This prevents duplicate records from wrapper containers (ModuleList etc.).
_HOOK_KEYWORDS = (
    "self_attn",       # qwen2, llama, mistral attention
    "attention",       # gpt2, bert attention
    "mlp",             # qwen2, llama, mistral feed-forward
    "feed_forward",    # some architectures use this name
    "block",           # gpt2 transformer blocks
)

# Sub-module types we specifically SKIP even if they match a keyword, because
# they are container modules whose children already get hooked.
_SKIP_TYPES = (nn.ModuleList, nn.Sequential, nn.ModuleDict)


class ActivationTracker:
    """Track per-layer activation statistics via PyTorch forward hooks."""

    def __init__(self, model: nn.Module) -> None:
        self.model = model
        self._handles: List[Any] = []
        self._records: List[Dict] = []
        self.layer_names: List[str] = []

    # ------------------------------------------------------------------
    # Hook management
    # ------------------------------------------------------------------

    def _hook_factory(self, name: str):
        """Return a forward hook closure that records stats for *name*."""

        def hook(module: nn.Module, inputs: Any, output: Any) -> None:  # noqa: ARG001
            # Unwrap tuple/list outputs (attention returns (tensor, cache, …)).
            if isinstance(output, (tuple, list)):
                out = output[0]
            else:
                out = output

            if not torch.is_tensor(out):
                return

            arr: np.ndarray = out.detach().float().cpu().numpy()
            abs_arr = np.abs(arr)

            self._records.append(
                {
                    "layer": name,
                    "mean": float(arr.mean()),
                    "std": float(arr.std()),
                    "max": float(abs_arr.max()),
                    "min": float(arr.min()),
                    "energy": float(np.mean(arr * arr)),
                    "shape": list(arr.shape),
                }
            )

        return hook

    def attach(self) -> "ActivationTracker":
        """Register forward hooks on matching transformer sub-modules.

        Selection criteria:
        - The module's dotted name contains one of _HOOK_KEYWORDS.
        - The name contains at least one digit (identifies a numbered layer).
        - The module type is not a bare container (ModuleList, Sequential).
        """
        count = 0
        for name, module in self.model.named_modules():
            if isinstance(module, _SKIP_TYPES):
                continue
            name_lower = name.lower()
            if not any(kw in name_lower for kw in _HOOK_KEYWORDS):
                continue
            if not any(c.isdigit() for c in name):
                continue

            self.layer_names.append(name)
            handle = module.register_forward_hook(self._hook_factory(name))
            self._handles.append(handle)
            count += 1

        logger.info("ActivationTracker: attached %d hooks", count)
        return self

    def detach(self) -> None:
        """Remove all registered hooks."""
        for handle in self._handles:
            handle.remove()
        self._handles.clear()
        self.layer_names.clear()
        logger.info("ActivationTracker: all hooks removed")

    # ------------------------------------------------------------------
    # Records
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Discard accumulated records (call before each forward pass)."""
        self._records.clear()

    def get_records(self) -> List[Dict]:
        """Return a copy of the accumulated activation records."""
        return list(self._records)
