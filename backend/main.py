"""
NeuroFence Web Backend — FastAPI

Compatible with: Python 3.13, transformers >= 5.x, pandas >= 3.x

Endpoints
---------
POST /api/scan/start              Start a background scan job
GET  /api/scan/{job_id}           Poll status / results
GET  /api/scan/{job_id}/heatmap   Serve heatmap PNG
GET  /api/scan/{job_id}/report    Download PDF report
POST /api/baseline/save           Save scan records as baseline
GET  /api/health                  Health check
"""

import logging
import os
import sys
import threading
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Ensure the project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neurofence.detector import ForensicDetector
from neurofence.fuzzer import generate_prompts
from neurofence.reporter import generate_pdf
from neurofence.sandbox import ModelSandbox
from neurofence.tracker import ActivationTracker
from neurofence.utils import ensure_dir, load_json, save_json, sha256_file
from ui.heatmap import save_heatmap

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(_ROOT, "output")
DATA_DIR = os.path.join(_ROOT, "data")
BASELINE_PATH = os.path.join(DATA_DIR, "baseline.json")

ensure_dir(OUTPUT_DIR)
ensure_dir(DATA_DIR)

# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="NeuroFence API",
    description="LLM Weight Poisoning & Backdoor Scanner — REST API",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# In-memory job store
# ---------------------------------------------------------------------------

class JobStatus(str, Enum):
    PENDING  = "pending"
    LOADING  = "loading"
    SCANNING = "scanning"
    DONE     = "done"
    ERROR    = "error"


class Job:
    def __init__(
        self,
        job_id: str,
        model_path: str,
        num_prompts: int,
        scan_limit: int,
    ) -> None:
        self.job_id = job_id
        self.model_path = model_path
        self.num_prompts = num_prompts
        self.scan_limit = scan_limit
        self.status = JobStatus.PENDING
        self.progress: int = 0
        self.log: List[str] = []
        self.records: List[dict] = []
        self.summary: List[dict] = []
        self.overall_score: float = 0.0
        self.model_info: dict = {}
        self.prompts: List[str] = []
        self.error_msg: str = ""
        self.pdf_path: str = ""
        self.heatmap_path: str = ""


_jobs: Dict[str, Job] = {}
_jobs_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ScanRequest(BaseModel):
    model_path: str = Field(..., description="Absolute path to local HF model folder")
    num_prompts: int = Field(200, ge=10, le=2000)
    scan_limit: int = Field(60, ge=5, le=500)


class JobResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    log: List[str]
    overall_score: float
    model_info: Dict[str, Any]
    summary: List[Dict[str, Any]]
    error: str
    heatmap_available: bool
    pdf_available: bool


# ---------------------------------------------------------------------------
# Background scan
# ---------------------------------------------------------------------------

def _run_scan(job: Job) -> None:
    try:
        job.status = JobStatus.LOADING
        job.log.append(f"Loading model: {job.model_path}")

        sandbox = ModelSandbox(job.model_path).load()
        info = sandbox.model_info()
        info["sha256"] = sha256_file(
            os.path.join(job.model_path, "model.safetensors")
        )
        job.model_info = info
        n = info.get("num_parameters", 0)
        job.log.append(f"Model loaded — {n:,} parameters")

        job.status = JobStatus.SCANNING
        prompts = generate_prompts(job.num_prompts)
        job.prompts = prompts
        scan_prompts = prompts[: job.scan_limit]
        records: List[dict] = []

        tracker = ActivationTracker(sandbox.model).attach()
        job.log.append(f"Scanning {len(scan_prompts)} prompts…")

        for i, prompt in enumerate(scan_prompts, 1):
            try:
                tracker.clear()
                sandbox.forward(prompt)
                records.extend(tracker.get_records())
                job.progress = int(i / len(scan_prompts) * 100)
                if i % 10 == 0:
                    job.log.append(f"  [{i}/{len(scan_prompts)}] prompts scanned")
            except Exception as exc:
                job.log.append(f"  Warning: skipped — {exc}")

        tracker.detach()
        job.log.append(f"Collected {len(records)} activation records")

        detector = ForensicDetector()
        baseline_data = load_json(BASELINE_PATH, default=[])
        if baseline_data:
            detector.build_baseline(baseline_data)
            job.log.append("Baseline applied — computing relative scores")

        summary_df, overall_score = detector.score(records)

        job.records = records
        job.overall_score = overall_score

        # Convert DataFrame to JSON-safe list of dicts
        # pandas 3.x: use fillna(0) then replace np.nan manually
        if not summary_df.empty:
            safe_df = summary_df.copy()
            # Convert bool column to Python bool
            if "flagged" in safe_df.columns:
                safe_df["flagged"] = safe_df["flagged"].astype(bool)
            # Round floats
            for col in safe_df.select_dtypes(include="number").columns:
                if col != "flagged":
                    safe_df[col] = safe_df[col].round(4)
            job.summary = safe_df.where(
                pd.notnull(safe_df), None
            ).to_dict(orient="records")
        else:
            job.summary = []

        # Persist outputs
        job_out = os.path.join(OUTPUT_DIR, job.job_id)
        ensure_dir(job_out)
        save_json(os.path.join(job_out, "records.json"), records)
        if not summary_df.empty:
            summary_df.to_csv(os.path.join(job_out, "summary.csv"), index=False)

        hm_path = os.path.join(job_out, "heatmap.png")
        if save_heatmap(summary_df, hm_path):
            job.heatmap_path = hm_path

        pdf_path = os.path.join(job_out, "neurofence_report.pdf")
        generate_pdf(
            pdf_path,
            job.model_info,
            summary_df,
            prompts,
            overall_score,
            heatmap_path=hm_path if job.heatmap_path else None,
        )
        job.pdf_path = pdf_path
        job.log.append(f"Complete — risk score: {overall_score:.4f}")
        job.status = JobStatus.DONE

    except Exception as exc:
        logger.exception("Scan job %s failed", job.job_id)
        job.error_msg = str(exc)
        job.status = JobStatus.ERROR


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "neurofence-api"}


@app.post("/api/scan/start", response_model=JobResponse)
def start_scan(req: ScanRequest, background_tasks: BackgroundTasks):
    if not os.path.isdir(req.model_path):
        raise HTTPException(400, f"Model directory not found: {req.model_path}")

    job_id = str(uuid.uuid4())
    job = Job(job_id, req.model_path, req.num_prompts, req.scan_limit)
    with _jobs_lock:
        _jobs[job_id] = job

    background_tasks.add_task(_run_scan, job)
    return _to_response(job)


@app.get("/api/scan/{job_id}", response_model=JobResponse)
def get_scan(job_id: str):
    return _to_response(_get_job(job_id))


@app.get("/api/scan/{job_id}/heatmap")
def get_heatmap(job_id: str):
    job = _get_job(job_id)
    if not job.heatmap_path or not os.path.exists(job.heatmap_path):
        raise HTTPException(404, "Heatmap not available yet")
    return FileResponse(job.heatmap_path, media_type="image/png")


@app.get("/api/scan/{job_id}/report")
def get_report(job_id: str):
    job = _get_job(job_id)
    if not job.pdf_path or not os.path.exists(job.pdf_path):
        raise HTTPException(404, "Report not available yet")
    return FileResponse(
        job.pdf_path,
        media_type="application/pdf",
        filename="neurofence_report.pdf",
    )


@app.post("/api/baseline/save")
def save_baseline(job_id: str):
    job = _get_job(job_id)
    if job.status != JobStatus.DONE or not job.records:
        raise HTTPException(400, "Scan must be complete before saving baseline")
    ensure_dir(DATA_DIR)
    save_json(BASELINE_PATH, job.records)
    return {"saved": True, "records": len(job.records), "path": BASELINE_PATH}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_job(job_id: str) -> Job:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(404, f"Job not found: {job_id}")
    return job


def _to_response(job: Job) -> JobResponse:
    return JobResponse(
        job_id=job.job_id,
        status=job.status.value,
        progress=job.progress,
        log=job.log[-50:],
        overall_score=job.overall_score,
        model_info=job.model_info,
        summary=job.summary,
        error=job.error_msg,
        heatmap_available=bool(job.heatmap_path),
        pdf_available=bool(job.pdf_path),
    )
