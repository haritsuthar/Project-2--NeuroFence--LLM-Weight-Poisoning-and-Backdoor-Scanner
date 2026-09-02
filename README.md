# NeuroFence

## Offline LLM Weight Poisoning and Backdoor Scanner

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-Transformers-FFD21E?logo=huggingface&logoColor=black)](https://huggingface.co/docs/transformers)
[![PyQt6](https://img.shields.io/badge/Desktop%20UI-PyQt6-41CD52?logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Project Status](https://img.shields.io/badge/Status-Internship%20Project-orange)](#project-status)

> An offline AI security and model-forensics application for detecting suspicious activation behavior in locally stored Large Language Models.

NeuroFence is an offline forensic scanner that analyzes local Large Language Models for activation anomalies that may indicate model poisoning, trigger-based backdoors, or sleeper-agent behavior.

The application loads a model from a local directory, generates adversarial prompts, monitors internal Transformer activations, calculates anomaly scores, displays results through a PyQt6 desktop interface, and generates a PDF security report.

> **Important:** NeuroFence is a forensic triage tool. An anomaly score alone does not prove that a model contains a backdoor.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Problem Statement](#problem-statement)
- [Objectives](#objectives)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Detection Workflow](#detection-workflow)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Offline Configuration](#offline-configuration)
- [Usage](#usage)
- [Output Files](#output-files)
- [Risk Scoring](#risk-scoring)
- [Testing Strategy](#testing-strategy)
- [Development Roadmap](#development-roadmap)
- [Security and Privacy](#security-and-privacy)
- [Limitations](#limitations)
- [Future Enhancements](#future-enhancements)
- [Internship Relevance](#internship-relevance)
- [Contributing](#contributing)
- [License](#license)
- [Disclaimer](#disclaimer)

---

## Project Overview

Organizations increasingly download and deploy open-source Large Language Models on local infrastructure. This creates a model supply-chain risk because attackers may modify model weights and embed hidden behaviors that activate only when a specific trigger phrase, token sequence, or unusual input pattern is provided.

NeuroFence provides an additional inspection layer before deployment. It analyzes the relationship between model inputs and internal activations to help identify suspicious behavior that may not be visible through ordinary output testing.

### Intended use cases

- Pre-deployment model screening.
- Offline LLM supply-chain analysis.
- AI security research.
- Model behavior comparison.
- Activation anomaly investigation.
- Academic and internship demonstrations.
- Air-gapped and restricted environments.

---

## Problem Statement

A poisoned LLM may behave normally during standard testing while containing a dormant behavior that activates under a hidden trigger.

For example, a model may produce safe responses during ordinary testing but behave differently when it receives a phrase such as:

```text
DEPLOY_OVERRIDE
```

Traditional file scanning and output-based testing may not reveal this type of behavior. NeuroFence addresses the problem by combining:

- Local model inspection.
- Adversarial prompt fuzzing.
- Hidden-layer activation tracking.
- Statistical anomaly detection.
- Visual forensic analysis.
- Automated security reporting.

---

## Objectives

NeuroFence is designed to:

1. Load local LLM files without requiring internet access.
2. Inspect model metadata and tensor structures.
3. Calculate cryptographic hashes for model identification.
4. Generate normal, random, edge-case, and trigger-like prompts.
5. Capture activations from selected Transformer layers.
6. Establish baseline activation behavior.
7. Identify unusual neuron and layer-level responses.
8. Display findings through a native desktop application.
9. Export reproducible JSON, CSV, image, and PDF evidence.
10. Support security analysis on isolated or air-gapped systems.

---

## Features

### Offline Model Sandbox

- Loads local Hugging Face model directories.
- Supports local tokenizer and configuration files.
- Uses `local_files_only=True`.
- Does not require cloud APIs during scanning.
- Supports CPU inference and optional GPU acceleration.
- Computes SHA-256 hashes for model identification.

### Safetensors Inspection

NeuroFence supports models stored in the `safetensors` format. It can inspect tensor keys and shapes before inference, helping analysts verify the structure of a model without treating arbitrary model files as executable code.

### Adversarial Prompt Fuzzer

The fuzzer generates:

- Normal baseline prompts.
- Random text mutations.
- Casing variations.
- Punctuation variations.
- Repeated-token prompts.
- Trigger-word candidates.
- Random noise combinations.
- Edge-case instruction patterns.

### Activation Tracker

The activation tracker uses PyTorch forward hooks to collect layer-level statistics during inference:

- Mean activation.
- Activation standard deviation.
- Maximum activation.
- Activation energy.
- Activation shape.
- Layer name.
- Prompt association.

### Detection Engine

The detection engine calculates:

- Layer anomaly scores.
- Activation spike scores.
- Baseline deviation.
- Suspicious layer rankings.
- Overall scan risk score.

### Forensic Desktop Application

The PyQt6 interface provides:

- Local model selection.
- Model metadata display.
- Scan controls.
- Layer statistics table.
- Activation heatmap.
- Scan log.
- PDF report export.

### Automated Security Reports

The report generator creates PDF reports containing:

- Model path.
- Model SHA-256 hash.
- Scan configuration.
- Tested prompts.
- Layer-level statistics.
- Flagged layers.
- Overall risk score.
- Analyst-oriented interpretation.

---

## System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    NeuroFence Desktop UI                   │
│  Model Selection | Scan Control | Heatmap | Report Export   │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Scan Orchestrator                       │
│ Coordinates sandbox, fuzzing, tracking, scoring and export  │
└───────────────┬─────────────────────────┬───────────────────┘
                │                         │
                ▼                         ▼
┌────────────────────────┐      ┌─────────────────────────────┐
│     Model Sandbox      │      │      Adversarial Fuzzer      │
│ Local model loading    │      │ Prompt generation            │
│ Tensor inspection      │      │ Prompt mutation               │
│ Hash verification      │      │ Trigger-like inputs          │
└────────────┬───────────┘      └──────────────┬──────────────┘
             │                                 │
             └────────────────┬────────────────┘
                              ▼
                 ┌─────────────────────────────┐
                 │      Activation Tracker     │
                 │   PyTorch forward hooks     │
                 │ Hidden-layer measurements   │
                 └──────────────┬──────────────┘
                                ▼
                 ┌─────────────────────────────┐
                 │       Detection Engine       │
                 │ Baseline comparison          │
                 │ Spike analysis                │
                 │ Anomaly scoring               │
                 └──────────────┬──────────────┘
                                ▼
                 ┌─────────────────────────────┐
                 │       Forensic Evidence      │
                 │ JSON | CSV | Heatmap | PDF   │
                 └─────────────────────────────┘
```

---

## Detection Workflow

### 1. Model identification

The analyst selects a local model directory. NeuroFence records:

- Model path.
- Available configuration files.
- Tensor files.
- Model architecture information.
- SHA-256 hash.

### 2. Secure local loading

The tokenizer and model are loaded using local-only settings. No internet connection is required during the scan.

### 3. Baseline generation

Normal prompts are executed to establish expected activation behavior across monitored layers.

### 4. Adversarial fuzzing

The fuzzer generates modified and trigger-like prompts. Each input is sent through the model and associated with the corresponding activation records.

### 5. Activation measurement

For an activation vector \(x\), NeuroFence calculates activation energy:

\[
E(x) = \frac{1}{n}\sum_{i=1}^{n}x_i^2
\]

where:

- \(E(x)\) is the activation energy.
- \(x_i\) is an individual activation value.
- \(n\) is the number of activation values.

A simplified spike score is:

\[
S(x) = \frac{\max(x)}{\sigma(x)+\epsilon}
\]

where:

- \(S(x)\) is the spike score.
- \(\sigma(x)\) is the activation standard deviation.
- \(\epsilon\) prevents division by zero.

### 6. Anomaly scoring

The detector compares activation statistics across prompt categories and identifies layers with unusually high or concentrated responses.

### 7. Analyst review

Flagged results are displayed in the desktop interface. The analyst can inspect the evidence and determine whether additional testing is necessary.

### 8. Report generation

All relevant evidence is exported to structured files and a PDF report.

---

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python 3.10+ |
| Deep-learning framework | PyTorch |
| Model library | Hugging Face Transformers |
| Tensor format | safetensors |
| Fuzzing engine | Python randomization and mutation |
| Instrumentation | PyTorch forward hooks |
| Data processing | NumPy and Pandas |
| Desktop interface | PyQt6 |
| Heatmap generation | Matplotlib |
| PDF reports | ReportLab |
| Deployment model | Local and offline |

---

## Project Structure

```text
NeuroFence/
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
│
├── neurofence/
│   ├── __init__.py
│   ├── sandbox.py
│   ├── fuzzer.py
│   ├── tracker.py
│   ├── detector.py
│   ├── reporter.py
│   └── utils.py
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── models.py
│   └── heatmap.py
│
├── data/
│   └── baseline.json
│
├── assets/
│   ├── logo.png
│   └── architecture.png
│
└── output/
    ├── records.json
    ├── summary.csv
    ├── heatmap.png
    └── neurofence_report.pdf
```

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `sandbox.py` | Local model loading, inference, and tensor inspection |
| `fuzzer.py` | Prompt generation and mutation |
| `tracker.py` | PyTorch hook registration and activation capture |
| `detector.py` | Baseline analysis and anomaly scoring |
| `reporter.py` | PDF security report generation |
| `utils.py` | Hashing, JSON storage, and common utilities |
| `main_window.py` | Main PyQt6 application window |
| `models.py` | Data model for displaying tabular results |
| `heatmap.py` | Activation anomaly heatmap creation |
| `app.py` | Application entry point |

---

## System Requirements

### Minimum requirements

- Python 3.10 or newer.
- 8 GB RAM.
- 10 GB free disk space.
- CPU inference support.
- Windows, Linux, or macOS.

### Recommended requirements

- Python 3.11.
- 16 GB or more RAM.
- NVIDIA GPU with CUDA support.
- 20 GB or more free disk space.
- A small local Transformer model for development.

For an internship demonstration, begin with a small model or a controlled test model before scanning larger models.

---

## Installation

### Clone the repository

```bash
git clone https://github.com/<your-username>/NeuroFence.git
cd NeuroFence
```

Replace `<your-username>` with your GitHub username.

### Create a virtual environment

#### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

#### Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Example `requirements.txt`

```txt
torch>=2.1
transformers>=4.40
safetensors>=0.4
numpy>=1.24
pandas>=2.0
matplotlib>=3.7
PyQt6>=6.5
reportlab>=4.0
```

---

## Offline Configuration

NeuroFence is designed to operate without internet access after all dependencies and model files have been prepared.

### Linux or macOS

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
python app.py
```

### Windows PowerShell

```powershell
$env:HF_HUB_OFFLINE="1"
$env:TRANSFORMERS_OFFLINE="1"
$env:HF_DATASETS_OFFLINE="1"
python app.py
```

### Preparing an air-gapped machine

1. Install all Python dependencies before disconnecting the system.
2. Copy the complete local model directory.
3. Verify that tokenizer and configuration files are available.
4. Record and verify the model hash.
5. Test the application with network access disabled.
6. Store dependency versions in a requirements or lock file.

### Example model directory

```text
local-model/
├── config.json
├── tokenizer.json
├── tokenizer_config.json
├── special_tokens_map.json
├── generation_config.json
└── model.safetensors
```

Sharded models may contain multiple files:

```text
model-00001-of-00003.safetensors
model-00002-of-00003.safetensors
model-00003-of-00003.safetensors
model.safetensors.index.json
```

For sharded models, all model shards should be hashed and inspected.

---

## Usage

### Launch the application

```bash
python app.py
```

### Scan procedure

1. Open NeuroFence.
2. Click **Load Model**.
3. Select a local Hugging Face model directory.
4. Confirm the model metadata and hash.
5. Start the forensic scan.
6. Review the layer statistics table.
7. Inspect the activation heatmap.
8. Export the PDF report.

### Example verification command

```bash
python -m compileall neurofence ui app.py
```

### Example console output

```text
Model loaded successfully.
Prompts generated: 200
Prompts evaluated: 40
Activation records collected: 1,280
Flagged layers: 3
Overall risk score: 0.7421
Report generated successfully.
```

---

## Output Files

After a scan, NeuroFence creates the following files:

| File | Description |
|---|---|
| `records.json` | Raw activation measurements |
| `summary.csv` | Aggregated layer-level statistics |
| `heatmap.png` | Visual representation of anomaly scores |
| `neurofence_report.pdf` | Human-readable forensic report |

### Example activation record

```json
{
  "layer": "model.layers.3",
  "mean": 0.0214,
  "std": 0.1432,
  "max": 3.9821,
  "energy": 0.0247,
  "shape": [2048][1][32]
}
```

### Example summary columns

```text
layer
mean
std
max
energy
spike_score
anomaly_score
flagged
```

---

## Risk Scoring

The prototype uses statistical indicators to rank potentially suspicious layers.

| Score range | Interpretation |
|---|---|
| 0.00–0.25 | Low observed activation anomaly |
| 0.25–0.50 | Mild anomaly; additional testing recommended |
| 0.50–0.75 | Elevated anomaly; analyst review recommended |
| 0.75–1.00 | High anomaly; isolate model pending investigation |

These ranges are demonstration thresholds and should be calibrated using representative clean and intentionally modified models.

A high score may be caused by:

- An unusual but legitimate model architecture.
- A prompt distribution that differs from the training distribution.
- Numerical instability.
- A poorly selected baseline.
- A genuinely suspicious trigger-related response.

The score should be interpreted together with the tested prompts, flagged layers, model hash, and model output behavior.

---

## Testing Strategy

### Unit testing

Test the following components independently:

- Prompt generation.
- Prompt mutation.
- SHA-256 hashing.
- JSON serialization.
- Activation energy calculation.
- Spike score calculation.
- Detector threshold behavior.
- PDF report creation.

### Integration testing

Validate the complete workflow:

1. Load a small local model.
2. Attach activation hooks.
3. Run a small prompt batch.
4. Collect activation records.
5. Generate a summary.
6. Render a heatmap.
7. Export a PDF report.

### Safety testing

Use a controlled synthetic test model or mock activation source to simulate a trigger-like spike. Do not use real malicious payloads or unauthorized models for testing.

### Memory testing

Confirm that:

- Hooks are removed after scanning.
- Activation tensors are detached from the computation graph.
- CPU copies are used for stored records.
- The application does not continuously retain full model outputs.
- Repeated scans do not cause unbounded memory growth.

---

## Development Roadmap

### Week 1 — Sandbox and Application Setup

#### AI forensics

- Implement local model loading.
- Inspect model metadata.
- Add SHA-256 hashing.
- Attach initial PyTorch hooks.
- Validate a small local model.

#### Desktop application

- Create the PyQt6 application.
- Add model folder selection.
- Display basic metadata.
- Add scan and report buttons.

### Week 2 — Fuzzing and Visualization

#### AI forensics

- Implement prompt generation.
- Add random and edge-case mutations.
- Create the baseline activation dataset.
- Store activation records in JSON.

#### Desktop application

- Add activation table.
- Add layer-level heatmap.
- Display scan progress and logs.
- Test large result payloads.

### Week 3 — Detection and Validation

#### AI forensics

- Implement anomaly scoring.
- Build a controlled synthetic trigger test.
- Compare baseline and trigger-like activation distributions.
- Validate hook cleanup and memory behavior.

#### Desktop application

- Add flagged-layer indicators.
- Add detailed layer inspection.
- Display score explanations.
- Improve error handling.

### Week 4 — Reporting and Finalization

#### AI forensics

- Generate PDF reports.
- Include model hash and scan configuration.
- Add reproducibility metadata.
- Document limitations and false positives.

#### Desktop application

- Improve layout and responsiveness.
- Add final visual polish.
- Package the application if required.
- Prepare screenshots and demonstration material.

---

## Security and Privacy

NeuroFence follows an offline-first design:

- No cloud inference.
- No external API calls.
- No prompt uploads.
- No telemetry.
- No remote model downloads during scans.
- Local storage of scan results.
- Hash-based model identification.
- Suitable for restricted environments after dependency preparation.

### Operational precautions

- Run unknown model files in a dedicated local environment.
- Use a non-administrator operating-system account.
- Keep the model directory read-only where possible.
- Do not execute repository-provided model code.
- Verify model hashes before and after transfer.
- Do not treat a scan result as a replacement for complete supply-chain review.
- Do not use production secrets as scan prompts.

---

## Limitations

- Activation anomalies do not prove the existence of a backdoor.
- Detection quality depends on baseline prompt coverage.
- The prototype may require architecture-specific hook selection.
- Large models may exceed available memory.
- A dormant backdoor may not activate during the tested prompt set.
- Legitimate rare behavior may produce a false positive.
- The current scoring system is statistical rather than formally verified.
- Full neuron-level localization requires additional model-specific analysis.
- Sharded model hashing requires additional aggregation logic.
- The current prototype may not support every Hugging Face model architecture.

---

## Future Enhancements

- Add support for more Transformer architectures.
- Implement configurable layer-selection rules.
- Add neuron-level activation localization.
- Use clustering for activation-pattern comparison.
- Add autoencoder-based anomaly detection.
- Support batch comparison of multiple models.
- Add semantic-preserving prompt mutation.
- Add model signature verification.
- Add signed evidence bundles.
- Add scan reproducibility manifests.
- Add CUDA memory optimization.
- Add multiprocessing for independent prompt batches.
- Add a command-line interface.
- Add automated regression tests.
- Package the application with PyInstaller.
- Add analyst annotations to forensic reports.

---

## Internship Relevance

NeuroFence demonstrates practical knowledge in:

- Artificial intelligence security.
- LLM supply-chain security.
- Neural-network interpretability.
- Model forensics.
- Adversarial testing.
- Python application development.
- PyTorch instrumentation.
- Desktop software engineering.
- Secure offline system design.
- Automated technical reporting.

### Suggested project description

> Developed NeuroFence, an offline LLM forensic scanner that analyzes locally stored model weights and hidden-layer activations for potential trigger-based backdoor behavior. Implemented adversarial prompt fuzzing, PyTorch activation hooks, statistical anomaly scoring, PyQt6 visualization, SHA-256 model identification, and automated PDF security reporting for air-gapped AI security environments.

### Suggested resume bullet

> Built an offline AI-security tool using PyTorch, Hugging Face Transformers, safetensors, adversarial fuzzing, forward hooks, PyQt6, and automated PDF reporting to identify anomalous LLM activation behavior associated with potential model poisoning.

---

## Contributing

Contributions are welcome for authorized defensive security research, education, and controlled model evaluation.

### Contribution workflow

1. Fork the repository.
2. Create a feature branch.

```bash
git checkout -b feature/improved-detector
```

3. Make and test your changes.
4. Commit with a descriptive message.

```bash
git commit -m "Improve layer anomaly scoring"
```

5. Push the branch.

```bash
git push origin feature/improved-detector
```

6. Open a pull request.

### Contribution guidelines

- Keep the tool offline-first.
- Do not add telemetry or hidden network requests.
- Do not include malicious payloads.
- Add tests for new functionality.
- Document model-architecture assumptions.
- Do not commit model weights or private scan results.

---

## License

This project is distributed under the MIT License. See the [LICENSE](LICENSE) file for details.

If your internship institution requires a different license, replace this section with the approved license before publishing the repository.

---

## Disclaimer

NeuroFence is intended for authorized defensive security research, academic work, and controlled model evaluation.

The project does not guarantee detection of every form of model poisoning or neural-network backdoor. Results must be reviewed by a qualified analyst and combined with additional controls, including:

- Model provenance verification.
- Hash and signature validation.
- Dependency auditing.
- Sandboxed execution.
- Output-based testing.
- Human security review.

Do not scan models that you do not own or do not have permission to analyze.

---

## Project Status

**Status:** Internship prototype / research implementation

**Project name:** NeuroFence

**Domain:** AI Security, SecOps, and Model Forensics

**Deployment model:** Offline and air-gapped compatible

**Interface:** Native PyQt6 desktop application

**Repository:** Add your GitHub repository URL here after publishing the project.
