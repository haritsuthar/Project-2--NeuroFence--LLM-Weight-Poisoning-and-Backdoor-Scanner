"""
MainWindow — NeuroFence desktop UI (PyQt6).

All heavy work (model loading, scanning) runs in QThread workers so
the GUI never freezes.

Compatible with: Python 3.13, PyQt6, transformers >= 5.x, pandas >= 3.x
"""

import logging
import os
from typing import List, Optional

import pandas as pd
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from neurofence.detector import ForensicDetector
from neurofence.fuzzer import generate_prompts
from neurofence.reporter import generate_pdf
from neurofence.sandbox import ModelSandbox
from neurofence.tracker import ActivationTracker
from neurofence.utils import ensure_dir, load_json, save_json, sha256_file
from ui.heatmap import save_heatmap
from ui.models import PandasTableModel

logger = logging.getLogger(__name__)

OUTPUT_DIR = "output"
BASELINE_PATH = os.path.join("data", "baseline.json")


# ---------------------------------------------------------------------------
# Background workers
# ---------------------------------------------------------------------------

class LoadWorker(QThread):
    """Load a model in a background thread."""

    finished = pyqtSignal(object, str)   # (ModelSandbox, info_string)
    error = pyqtSignal(str)

    def __init__(self, model_path: str) -> None:
        super().__init__()
        self.model_path = model_path

    def run(self) -> None:
        try:
            sandbox = ModelSandbox(self.model_path).load()
            info = sandbox.model_info()
            n = info.get("num_parameters", 0)
            msg = (
                f"Model: {info.get('model_type', '?')}  |  "
                f"Params: {n:,}  |  "
                f"Device: {info.get('device', '?')}"
            )
            self.finished.emit(sandbox, msg)
        except Exception as exc:
            self.error.emit(str(exc))


class ScanWorker(QThread):
    """Run adversarial fuzzing + activation scanning in a background thread."""

    progress = pyqtSignal(int, int)                           # (current, total)
    log_msg = pyqtSignal(str)
    finished = pyqtSignal(object, object, float, object)      # (records, df, score, prompts)
    error = pyqtSignal(str)

    def __init__(
        self,
        sandbox: ModelSandbox,
        num_prompts: int = 200,
        scan_limit: int = 60,
    ) -> None:
        super().__init__()
        self.sandbox = sandbox
        self.num_prompts = num_prompts
        self.scan_limit = scan_limit

    def run(self) -> None:
        try:
            prompts = generate_prompts(self.num_prompts)
            records: List[dict] = []
            scan_prompts = prompts[: self.scan_limit]

            tracker = ActivationTracker(self.sandbox.model).attach()
            self.log_msg.emit(f"Hooks attached. Scanning {len(scan_prompts)} prompts…")

            for i, prompt in enumerate(scan_prompts, 1):
                try:
                    tracker.clear()
                    self.sandbox.forward(prompt)
                    records.extend(tracker.get_records())
                    self.progress.emit(i, len(scan_prompts))
                    if i % 10 == 0:
                        self.log_msg.emit(f"  [{i}/{len(scan_prompts)}] prompts done")
                except Exception as exc:
                    self.log_msg.emit(f"  Warning: skipped prompt — {exc}")

            tracker.detach()
            self.log_msg.emit(f"Collected {len(records)} activation records.")

            detector = ForensicDetector()
            baseline_data = load_json(BASELINE_PATH, default=[])
            if baseline_data:
                detector.build_baseline(baseline_data)
                self.log_msg.emit("Baseline loaded — computing relative scores.")

            summary_df, overall_score = detector.score(records)
            self.finished.emit(records, summary_df, overall_score, prompts)

        except Exception as exc:
            self.error.emit(str(exc))


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QWidget):
    """NeuroFence main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NeuroFence — LLM Backdoor Scanner")
        self.resize(1280, 820)
        self._apply_style()

        # State
        self.model_path: Optional[str] = None
        self.sandbox: Optional[ModelSandbox] = None
        self.records: List[dict] = []
        self.summary_df: pd.DataFrame = pd.DataFrame()
        self.prompts: List[str] = []
        self.overall_score: float = 0.0

        # Workers (held as attrs to prevent GC while running)
        self._load_worker: Optional[LoadWorker] = None
        self._scan_worker: Optional[ScanWorker] = None

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QLabel("⬡ NeuroFence")
        header.setObjectName("header")
        root.addWidget(header)

        # Meta info
        self.meta_label = QLabel("Model: not loaded")
        self.meta_label.setObjectName("metaLabel")
        root.addWidget(self.meta_label)

        # Toolbar
        toolbar = QHBoxLayout()
        self.btn_load = QPushButton("📂  Load Model")
        self.btn_run = QPushButton("▶  Run Scan")
        self.btn_baseline = QPushButton("📐  Save Baseline")
        self.btn_report = QPushButton("📄  Export PDF")
        self.btn_run.setEnabled(False)
        self.btn_baseline.setEnabled(False)
        self.btn_report.setEnabled(False)
        for btn in (self.btn_load, self.btn_run, self.btn_baseline, self.btn_report):
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            toolbar.addWidget(btn)
        root.addLayout(toolbar)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        root.addWidget(self.progress)

        # Risk banner
        self.risk_label = QLabel("Risk Score: —")
        self.risk_label.setObjectName("riskLabel")
        self.risk_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.risk_label)

        # Splitter: table on top, heatmap + log on bottom
        splitter = QSplitter(Qt.Orientation.Vertical)

        self.table = QTableView()
        self.table_model = PandasTableModel()
        self.table.setModel(self.table_model)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        splitter.addWidget(self.table)

        bottom = QSplitter(Qt.Orientation.Horizontal)

        self.heatmap_label = QLabel("Heatmap will appear here after scan.")
        self.heatmap_label.setObjectName("heatmapLabel")
        self.heatmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.heatmap_label.setMinimumHeight(240)
        bottom.addWidget(self.heatmap_label)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setObjectName("logBox")
        self.log.setMaximumWidth(420)
        bottom.addWidget(self.log)
        bottom.setSizes([760, 420])

        splitter.addWidget(bottom)
        splitter.setSizes([440, 280])
        root.addWidget(splitter, 1)

        # Signals
        self.btn_load.clicked.connect(self._on_load)
        self.btn_run.clicked.connect(self._on_run)
        self.btn_baseline.clicked.connect(self._on_save_baseline)
        self.btn_report.clicked.connect(self._on_export)

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def _on_load(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Select local Hugging Face model folder"
        )
        if not path:
            return
        self.model_path = path
        self._log(f"Loading model from: {path} …")
        self.btn_load.setEnabled(False)
        self.btn_run.setEnabled(False)

        self._load_worker = LoadWorker(path)
        self._load_worker.finished.connect(self._on_load_done)
        self._load_worker.error.connect(self._on_load_error)
        self._load_worker.start()

    def _on_load_done(self, sandbox: ModelSandbox, info_msg: str) -> None:
        self.sandbox = sandbox
        self.meta_label.setText(info_msg)
        st_path = os.path.join(self.model_path, "model.safetensors")
        sha = sha256_file(st_path)
        self._log(f"Model loaded. SHA-256: {sha}")
        self.btn_load.setEnabled(True)
        self.btn_run.setEnabled(True)

    def _on_load_error(self, err: str) -> None:
        QMessageBox.critical(self, "Load Error", err)
        self._log(f"ERROR: {err}")
        self.btn_load.setEnabled(True)

    def _on_run(self) -> None:
        if not self.sandbox:
            QMessageBox.warning(self, "No Model", "Load a model first.")
            return
        self.btn_run.setEnabled(False)
        self.btn_baseline.setEnabled(False)
        self.btn_report.setEnabled(False)
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self._log("Starting scan …")

        self._scan_worker = ScanWorker(self.sandbox, num_prompts=200, scan_limit=60)
        self._scan_worker.progress.connect(self._on_scan_progress)
        self._scan_worker.log_msg.connect(self._log)
        self._scan_worker.finished.connect(self._on_scan_done)
        self._scan_worker.error.connect(self._on_scan_error)
        self._scan_worker.start()

    def _on_scan_progress(self, current: int, total: int) -> None:
        self.progress.setValue(int(current / total * 100))

    def _on_scan_done(
        self,
        records: List[dict],
        summary_df: pd.DataFrame,
        overall_score: float,
        prompts: List[str],
    ) -> None:
        self.records = records
        self.summary_df = summary_df
        self.overall_score = overall_score
        self.prompts = prompts

        self.table_model.set_df(summary_df)

        ensure_dir(OUTPUT_DIR)
        save_json(os.path.join(OUTPUT_DIR, "records.json"), records)
        if not summary_df.empty:
            summary_df.to_csv(os.path.join(OUTPUT_DIR, "summary.csv"), index=False)

        hm_path = os.path.join(OUTPUT_DIR, "heatmap.png")
        if save_heatmap(summary_df, hm_path):
            pix = QPixmap(hm_path)
            self.heatmap_label.setPixmap(
                pix.scaledToWidth(720, Qt.TransformationMode.SmoothTransformation)
            )

        self._update_risk_banner(overall_score)
        self._log(f"Scan complete. Overall risk score: {overall_score:.4f}")

        self.progress.setVisible(False)
        self.btn_run.setEnabled(True)
        self.btn_baseline.setEnabled(True)
        self.btn_report.setEnabled(True)

    def _on_scan_error(self, err: str) -> None:
        QMessageBox.critical(self, "Scan Error", err)
        self._log(f"ERROR during scan: {err}")
        self.progress.setVisible(False)
        self.btn_run.setEnabled(True)

    def _on_save_baseline(self) -> None:
        if not self.records:
            QMessageBox.warning(self, "No Data", "Run a scan first.")
            return
        ensure_dir("data")
        save_json(BASELINE_PATH, self.records)
        self._log(f"Baseline saved to {BASELINE_PATH} ({len(self.records)} records).")
        QMessageBox.information(self, "Baseline Saved", f"Saved to {BASELINE_PATH}")

    def _on_export(self) -> None:
        if self.summary_df is None or self.summary_df.empty:
            QMessageBox.warning(self, "No Data", "Run a scan first.")
            return
        ensure_dir(OUTPUT_DIR)
        model_info = {
            "path": self.model_path,
            "sha256": sha256_file(
                os.path.join(self.model_path, "model.safetensors")
            ),
        }
        if self.sandbox:
            model_info.update(self.sandbox.model_info())

        pdf_path = os.path.join(OUTPUT_DIR, "neurofence_report.pdf")
        hm_path = os.path.join(OUTPUT_DIR, "heatmap.png")
        generate_pdf(
            pdf_path,
            model_info,
            self.summary_df,
            self.prompts,
            self.overall_score,
            heatmap_path=hm_path if os.path.exists(hm_path) else None,
        )
        self._log(f"PDF report exported → {pdf_path}")
        QMessageBox.information(self, "Report Exported", f"Saved to:\n{pdf_path}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _log(self, msg: str) -> None:
        self.log.append(msg)
        logger.info(msg)

    def _update_risk_banner(self, score: float) -> None:
        if score < 1.0:
            colour, label = "#16A34A", "LOW"
        elif score < 3.0:
            colour, label = "#CA8A04", "MEDIUM"
        elif score < 6.0:
            colour, label = "#EA580C", "HIGH"
        else:
            colour, label = "#DC2626", "CRITICAL"

        self.risk_label.setText(f"Risk Score: {score:.4f} — {label}")
        self.risk_label.setStyleSheet(
            f"background-color: {colour}; color: white; font-weight: bold; "
            f"font-size: 14px; border-radius: 6px; padding: 6px;"
        )

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QWidget {
                background-color: #0D1117;
                color: #E6EDF3;
                font-family: 'Segoe UI', sans-serif;
                font-size: 10pt;
            }
            QLabel#header {
                font-size: 20px;
                font-weight: bold;
                color: #F78166;
                padding: 4px 0;
            }
            QLabel#metaLabel { color: #8B949E; font-size: 9pt; }
            QLabel#riskLabel {
                background-color: #161B22;
                border-radius: 6px;
                padding: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QLabel#heatmapLabel {
                background-color: #161B22;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton {
                background-color: #21262D;
                color: #E6EDF3;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 7px 14px;
            }
            QPushButton:hover  { background-color: #30363D; border-color: #F78166; }
            QPushButton:pressed { background-color: #F78166; color: #0D1117; }
            QPushButton:disabled { color: #484F58; border-color: #21262D; }
            QTableView {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                gridline-color: #21262D;
                alternate-background-color: #0D1117;
            }
            QHeaderView::section {
                background-color: #21262D;
                color: #E6EDF3;
                border: none;
                padding: 4px;
                font-weight: bold;
            }
            QTextEdit#logBox {
                background-color: #010409;
                border: 1px solid #30363D;
                border-radius: 6px;
                color: #7EE787;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
            QProgressBar {
                border: 1px solid #30363D;
                border-radius: 6px;
                text-align: center;
                background-color: #161B22;
            }
            QProgressBar::chunk { background-color: #F78166; border-radius: 5px; }
            QSplitter::handle   { background-color: #30363D; }
            QScrollBar:vertical { background: #161B22; width: 8px; }
            QScrollBar::handle:vertical { background: #30363D; border-radius: 4px; }
        """)
