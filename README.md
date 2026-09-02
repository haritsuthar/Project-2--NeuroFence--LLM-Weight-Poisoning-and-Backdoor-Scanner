# NeuroFence — LLM Weight Poisoning & Backdoor Scanner

NeuroFence is an offline AI security and model forensics tool that inspects local Large Language Models for suspicious activation patterns that may indicate poisoning, sleeper-agent behavior, or trigger-based backdoors. It loads models in a sandbox, fuzzes them with adversarial prompts, tracks internal activations with PyTorch hooks, and generates a forensic risk report for security analysts [web:11][web:21].

## Overview

Enterprises often deploy downloaded open-source LLMs locally, which creates supply-chain risk if the model weights have been tampered with. NeuroFence is designed to help analysts perform a **pre-deployment inspection** of a model by examining layer activations under normal, edge-case, and trigger-like inputs [web:11][web:27].

The project is intentionally offline-first and avoids web dashboards or cloud APIs. It is built as a native desktop forensic application so it can run in isolated or air-gapped environments.

## Key Features

- **Offline model sandbox** for loading local Hugging Face models safely.
- **Safetensors support** for secure tensor storage and zero-copy loading [web:11][web:32].
- **Adversarial prompt fuzzer** that generates random, edge-case, and trigger-like inputs.
- **Activation tracking** using PyTorch forward hooks for profiling hidden-layer behavior [web:21][web:27].
- **Anomaly scoring engine** that compares activation statistics across prompts.
- **Forensic desktop UI** built with PyQt for local inspection and analysis.
- **PDF report generation** with model hash, tested prompts, flagged layers, and risk score.

## Problem Statement

Large language models downloaded from public repositories can contain hidden malicious behaviors embedded directly in the weights. These backdoors may remain dormant during normal usage and activate only when specific trigger words or unusual prompt patterns are encountered. NeuroFence addresses this by providing an offline forensic scanner that detects activation anomalies before deployment.

## Proposed Approach

NeuroFence follows a simple forensic workflow:

1. Load a local model inside a sandboxed environment.
2. Generate synthetic prompts using a fuzzing engine.
3. Capture hidden-layer outputs through PyTorch hooks.
4. Compute activation statistics such as mean, variance, energy, and spike score.
5. Compare the results to a baseline distribution.
6. Flag suspicious layers and generate a risk report.

This makes the system useful as a triage tool for security teams rather than a one-click verdict engine.

## Architecture

### 1. Model Sandbox
The sandbox loads local model files from disk and inspects tensor metadata without executing unsafe serialization code. The implementation is based on Hugging Face Transformers and the `safetensors` format, which is designed to store tensors safely instead of using pickle-based loading [web:11][web:32].

### 2. Adversarial Fuzzer
The fuzzer creates:
- random prompts,
- punctuation and casing variants,
- repeated-token prompts,
- trigger-word injections,
- noisy synthetic edge cases.

Its goal is to stress the model and expose dormant activation spikes.

### 3. Activation Tracker
The tracker attaches PyTorch forward hooks to relevant Transformer modules. Forward hooks are intended for debugging and profiling, which makes them suitable for monitoring layer outputs during inference [web:21][web:27].

### 4. Detection Engine
The detector aggregates activation records into per-layer statistics and assigns anomaly scores. Layers with unusually high spikes or concentrated activation energy are marked as suspicious.

### 5. Desktop App
The PyQt interface provides:
- model upload,
- scan controls,
- activation summary table,
- heatmap view,
- report export,
- scan log window.

## Folder Structure

```text
NeuroFence/
├─ app.py
├─ requirements.txt
├─ README.md
├─ assets/
├─ data/
│  └─ baseline.json
├─ output/
├─ neurofence/
│  ├─ __init__.py
│  ├─ sandbox.py
│  ├─ fuzzer.py
│  ├─ tracker.py
│  ├─ detector.py
│  ├─ reporter.py
│  └─ utils.py
└─ ui/
   ├─ main_window.py
   ├─ models.py
   └─ heatmap.py
```

## Technology Stack

- **Python**
- **PyTorch**
- **Hugging Face Transformers**
- **safetensors**
- **PyQt6**
- **Pandas**
- **NumPy**
- **Matplotlib**
- **ReportLab**

## Installation

### 1. Clone the project
```bash
git clone <your-repo-url>
cd NeuroFence
```

### 2. Create a virtual environment
```bash
python -m venv .venv
```

### 3. Activate it
```bash
# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

## Usage

### Launch the desktop app
```bash
python app.py
```

### Workflow
1. Click **Load Model** and select a local Hugging Face model folder.
2. Click **Run Scan** to generate adversarial prompts and collect activations.
3. Review the activation summary and heatmap.
4. Click **Export PDF** to generate the forensic report.

## Output Files

Running a scan creates the following files in the `output/` folder:

- `records.json` — raw activation records.
- `summary.csv` — layer-wise anomaly summary.
- `heatmap.png` — visual activation map.
- `neurofence_report.pdf` — formatted forensic report.

## Internship Submission Highlights

This project demonstrates:
- secure offline model inspection,
- AI security and model forensics,
- PyTorch instrumentation,
- adversarial fuzzing,
- desktop application development,
- automated reporting.

It is especially suitable for an internship submission because it combines security engineering, machine learning, and practical software design in one complete system.

## Limitations

- A high anomaly score does not automatically prove backdoor presence.
- Results depend on the quality of the baseline prompt set.
- Very large models may require memory optimization or layer selection.
- Some architectures may expose different internal module names, so hook selection may need adjustment.

## Future Improvements

- Add support for more model architectures.
- Improve anomaly detection using clustering or autoencoder-based scoring.
- Add layer-by-layer drill-down visualizations.
- Support batch model comparison.
- Add model signature verification and hash tracking.
- Extend reporting with charts and timeline summaries.

## Screenshots

Add these to your submission:
- main dashboard screenshot,
- heatmap view screenshot,
- PDF report preview,
- sample scan log,
- model metadata panel.

## Academic/Professional Framing

NeuroFence is best described as an **offline forensic analysis tool for detecting suspicious activation behavior in LLMs**. It helps analysts inspect models before deployment and identify abnormal tensor-level patterns that may warrant deeper review.

## Acknowledgment

This project uses:
- Hugging Face tools for model loading and safe tensor storage [web:11][web:32].
- PyTorch hooks for activation monitoring [web:21][web:27].

---
**NeuroFence** is a strong internship project because it is practical, security-focused, and fully offline.