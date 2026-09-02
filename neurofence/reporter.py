"""
reporter.py — PDF forensic report generation for NeuroFence.
Compatible with reportlab >= 4.x / 5.x.
"""

import logging
import os
from typing import Dict, List, Optional

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

_BRAND_DARK = colors.HexColor("#0D1117")
_BRAND_ACCENT = colors.HexColor("#F78166")
_ROW_ALT = colors.HexColor("#F3F4F6")
_FLAG_BG = colors.HexColor("#FECDD3")


def generate_pdf(
    path: str,
    model_info: Dict,
    summary_df: pd.DataFrame,
    prompts: List[str],
    overall_score: float,
    heatmap_path: Optional[str] = None,
) -> None:
    """Build and save a forensic PDF report to *path*."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "NF_Title",
        parent=styles["Title"],
        fontSize=22,
        textColor=_BRAND_DARK,
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "NF_H2",
        parent=styles["Heading2"],
        textColor=_BRAND_DARK,
        fontSize=13,
        spaceBefore=12,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "NF_Body",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
    )
    code_style = ParagraphStyle(
        "NF_Code",
        parent=styles["Code"],
        fontSize=8,
        leading=11,
        backColor=colors.HexColor("#F6F8FA"),
    )

    story = []

    # ── Title ──────────────────────────────────────────────────────────
    story.append(Paragraph("NeuroFence Forensic Report", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=_BRAND_ACCENT))
    story.append(Spacer(1, 10))

    # ── Model metadata ─────────────────────────────────────────────────
    story.append(Paragraph("Model Information", h2_style))
    story.append(Paragraph(f"<b>Path:</b> {_esc(str(model_info.get('path', 'n/a')))}", body_style))
    story.append(Paragraph(f"<b>SHA-256:</b> {model_info.get('sha256', 'n/a')}", body_style))
    story.append(Paragraph(f"<b>Model Type:</b> {model_info.get('model_type', 'n/a')}", body_style))
    n_params = model_info.get("num_parameters")
    params_str = f"{n_params:,}" if isinstance(n_params, int) else str(n_params or "n/a")
    story.append(Paragraph(f"<b>Parameters:</b> {params_str}", body_style))
    story.append(Spacer(1, 8))

    # ── Risk banner ─────────────────────────────────────────────────────
    label = _risk_label(overall_score)
    risk_style = ParagraphStyle(
        "NF_Risk",
        parent=styles["BodyText"],
        fontSize=14,
        textColor=colors.white,
        backColor=_risk_colour(overall_score),
        borderPadding=(6, 10, 6, 10),
        spaceAfter=12,
    )
    story.append(
        Paragraph(f"Overall Risk Score: {overall_score:.4f} — {label}", risk_style)
    )

    # ── Heatmap ─────────────────────────────────────────────────────────
    if heatmap_path and os.path.exists(heatmap_path):
        story.append(Paragraph("Activation Heatmap", h2_style))
        story.append(
            Image(heatmap_path, width=15 * cm, height=8 * cm, kind="proportional")
        )
        story.append(Spacer(1, 8))

    # ── Tested prompts ──────────────────────────────────────────────────
    story.append(Paragraph("Tested Prompts (first 20)", h2_style))
    for i, p in enumerate(prompts[:20], 1):
        story.append(Paragraph(f"{i}. {_esc(str(p))}", code_style))
    story.append(Spacer(1, 8))

    # ── Layer summary table ─────────────────────────────────────────────
    story.append(Paragraph("Layer Anomaly Summary", h2_style))

    if summary_df is not None and not summary_df.empty:
        display_cols = [
            c for c in
            ["layer", "mean", "std", "max", "energy", "spike_score", "anomaly_score", "flagged"]
            if c in summary_df.columns
        ]
        df_disp = summary_df[display_cols].copy()
        for col in df_disp.select_dtypes(include="number").columns:
            df_disp[col] = df_disp[col].round(4)

        header = [c.replace("_", " ").title() for c in display_cols]
        rows = [header] + df_disp.astype(str).values.tolist()

        col_widths = _col_widths(display_cols)
        tbl = Table(rows, colWidths=col_widths, repeatRows=1)

        style_cmds = [
            ("BACKGROUND",   (0, 0), (-1, 0), _BRAND_DARK),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, -1), 7),
            ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ROW_ALT]),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]

        if "flagged" in display_cols:
            fi = display_cols.index("flagged")
            for ri, rv in enumerate(rows[1:], start=1):
                if str(rv[fi]).lower() == "true":
                    style_cmds.append(("BACKGROUND", (0, ri), (-1, ri), _FLAG_BG))

        tbl.setStyle(TableStyle(style_cmds))
        story.append(tbl)
    else:
        story.append(Paragraph("No layer data available.", body_style))

    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            "<i>NeuroFence — offline forensic LLM scanner. "
            "A high score is an indicator only; manual review is required "
            "before drawing conclusions about backdoor presence.</i>",
            body_style,
        )
    )

    doc.build(story)
    logger.info("PDF report saved to %s", path)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _risk_label(score: float) -> str:
    if score < 1.0:
        return "LOW"
    if score < 3.0:
        return "MEDIUM"
    if score < 6.0:
        return "HIGH"
    return "CRITICAL"


def _risk_colour(score: float) -> colors.Color:
    if score < 1.0:
        return colors.HexColor("#16A34A")
    if score < 3.0:
        return colors.HexColor("#CA8A04")
    if score < 6.0:
        return colors.HexColor("#EA580C")
    return colors.HexColor("#DC2626")


def _esc(text: str) -> str:
    """Escape XML special chars for ReportLab Paragraph."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _col_widths(cols: List[str]) -> List[float]:
    total = 490.0
    if "layer" in cols:
        lw = total * 0.30
        ow = (total - lw) / max(len(cols) - 1, 1)
        return [lw if c == "layer" else ow for c in cols]
    per = total / len(cols)
    return [per] * len(cols)
