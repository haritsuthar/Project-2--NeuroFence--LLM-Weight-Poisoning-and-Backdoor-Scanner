"""
Heatmap rendering helper for NeuroFence.
Uses the non-interactive Agg backend — never opens a GUI window.
"""

import logging
import os
from typing import Optional

import matplotlib
matplotlib.use("Agg")          # must be set before importing pyplot
import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger(__name__)


def save_heatmap(df: Optional[pd.DataFrame], path: str) -> bool:
    """Render an activation-anomaly heatmap and save it to *path*.

    Returns True on success, False otherwise.
    """
    if df is None or df.empty or "anomaly_score" not in df.columns:
        logger.warning("save_heatmap: empty/invalid DataFrame — skipped")
        return False

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    try:
        piv = (
            df.pivot_table(index="layer", values="anomaly_score", aggfunc="mean")
            .sort_values("anomaly_score", ascending=False)
        )

        fig, ax = plt.subplots(figsize=(10, max(4, len(piv) * 0.35)))
        im = ax.imshow(piv.values, aspect="auto", cmap="inferno", vmin=0)
        ax.set_yticks(range(len(piv.index)))
        ax.set_yticklabels(piv.index, fontsize=6)
        ax.set_xticks([0])
        ax.set_xticklabels(["Anomaly Score"], fontsize=8)
        ax.set_title("NeuroFence — Layer Anomaly Heatmap", fontsize=10, pad=8)

        cbar = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.04)
        cbar.ax.tick_params(labelsize=7)

        fig.tight_layout()
        fig.savefig(path, dpi=200)
        plt.close(fig)
        logger.info("Heatmap saved to %s", path)
        return True

    except Exception as exc:
        logger.error("save_heatmap failed: %s", exc)
        plt.close("all")
        return False
