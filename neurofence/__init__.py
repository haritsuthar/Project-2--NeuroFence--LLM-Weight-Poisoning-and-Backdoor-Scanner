"""
NeuroFence — LLM Weight Poisoning & Backdoor Scanner
Core package.
"""

from neurofence.sandbox import ModelSandbox
from neurofence.fuzzer import generate_prompts
from neurofence.tracker import ActivationTracker
from neurofence.detector import ForensicDetector
from neurofence.reporter import generate_pdf
from neurofence.utils import (
    sha256_file,
    ensure_dir,
    save_json,
    load_json,
    activation_energy,
)

__all__ = [
    "ModelSandbox",
    "generate_prompts",
    "ActivationTracker",
    "ForensicDetector",
    "generate_pdf",
    "sha256_file",
    "ensure_dir",
    "save_json",
    "load_json",
    "activation_energy",
]
