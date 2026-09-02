"""
ForensicDetector — aggregates activation records and assigns anomaly scores.

Compatible with pandas >= 3.x.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ForensicDetector:
    """Score activation records for anomalous behaviour.

    Parameters
    ----------
    baseline_df:
        Optional pre-computed baseline DataFrame (from :meth:`build_baseline`).
        When present, scores are computed relative to the baseline distribution.
    """

    def __init__(self, baseline_df: Optional[pd.DataFrame] = None) -> None:
        self.baseline_df = baseline_df

    # ------------------------------------------------------------------
    # Baseline
    # ------------------------------------------------------------------

    def build_baseline(self, records: List[Dict]) -> pd.DataFrame:
        """Compute per-layer statistics from *records* and store as baseline."""
        if not records:
            logger.warning("build_baseline: empty records — baseline not updated")
            return pd.DataFrame()

        df = pd.DataFrame(records)
        grp = (
            df.groupby("layer")[["mean", "std", "max", "energy"]]
            .agg(["mean", "std"])
            .reset_index()
        )

        # Flatten MultiIndex columns: ('mean','mean') → 'mean_mean'
        # pandas 3.x: columns are still tuples but ('layer', '') needs special handling
        new_cols = []
        for col in grp.columns:
            if isinstance(col, tuple):
                parts = [p for p in col if p]   # drop empty strings
                new_cols.append("_".join(parts) if parts else col[0])
            else:
                new_cols.append(col)
        grp.columns = new_cols

        self.baseline_df = grp
        logger.info("Baseline built for %d layers", len(grp))
        return grp

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def score(
        self, records: List[Dict]
    ) -> Tuple[pd.DataFrame, float]:
        """Compute per-layer anomaly scores from *records*.

        Returns
        -------
        summary : pd.DataFrame
            One row per layer, sorted by anomaly_score descending.
        overall_score : float
            Mean anomaly score (overall risk indicator).
        """
        if not records:
            return pd.DataFrame(), 0.0

        df = pd.DataFrame(records)
        summary = (
            df.groupby("layer")[["mean", "std", "max", "energy"]]
            .mean()
            .reset_index()
        )

        # Spike score: ratio of peak absolute activation to layer variability.
        summary["spike_score"] = (
            summary["max"] / (summary["std"] + 1e-6)
        ).clip(upper=1e6)

        if self.baseline_df is not None and not self.baseline_df.empty:
            summary = self._baseline_score(summary)
        else:
            summary["anomaly_score"] = self._raw_anomaly(summary)

        # Flag layers more than 1 std-dev above the mean anomaly score.
        mu = summary["anomaly_score"].mean()
        sigma = summary["anomaly_score"].std()
        summary["flagged"] = summary["anomaly_score"] > (mu + sigma)

        overall = float(summary["anomaly_score"].mean())
        result = summary.sort_values("anomaly_score", ascending=False).reset_index(drop=True)

        logger.info(
            "Scored %d layers — risk: %.4f — flagged: %d",
            len(result),
            overall,
            int(result["flagged"].sum()),
        )
        return result, overall

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _raw_anomaly(summary: pd.DataFrame) -> pd.Series:
        """Composite anomaly score when no baseline is available."""
        return (
            summary["mean"].abs()
            + summary["std"]
            + summary["energy"].abs() * 0.1
            + summary["spike_score"] * 0.01
        )

    def _baseline_score(self, summary: pd.DataFrame) -> pd.DataFrame:
        """z-score deviation from baseline per layer."""
        needed = ["layer", "mean_mean", "mean_std", "energy_mean", "energy_std"]
        avail = [c for c in needed if c in self.baseline_df.columns]

        if len(avail) < 3:
            # Baseline columns are missing — fall back to raw scoring
            logger.warning("Baseline schema mismatch — using raw scoring fallback")
            summary["anomaly_score"] = self._raw_anomaly(summary)
            return summary

        merged = summary.merge(
            self.baseline_df[avail],
            on="layer",
            how="left",
        )

        def _z(val: pd.Series, mu: pd.Series, sigma: pd.Series) -> pd.Series:
            return (val - mu).abs() / (sigma + 1e-6)

        merged["anomaly_score"] = (
            _z(merged["mean"], merged["mean_mean"], merged["mean_std"])
            + _z(merged["energy"], merged["energy_mean"], merged["energy_std"])
            + merged["spike_score"] * 0.01
        )

        # Layers not in baseline get raw-score fallback
        mask = merged["anomaly_score"].isna()
        if mask.any():
            merged.loc[mask, "anomaly_score"] = self._raw_anomaly(merged[mask])

        # Drop merged baseline columns from output
        drop_cols = [c for c in merged.columns if c.endswith(("_mean", "_std"))]
        merged = merged.drop(columns=drop_cols, errors="ignore")
        return merged
