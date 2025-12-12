# QuantumResearchPipeline

A multi-agent quantum computing research workspace featuring paper scraping, vision model training, and quantum circuit simulation.

## 🚀 System Specs & Performance

| Component | Specification | Benchmark |
|-----------|---------------|-----------|
| **GPU** | NVIDIA RTX 4070 (12GB VRAM) | Vision training: ~30s |
| **RAM** | 64GB DDR4 | Qiskit sims: <10s |
| **Python** | 3.9.19 | |
| **OS** | Pop!_OS Linux | |

## 📦 Components

### Agent 1: arXivScraper
- Scrapes quantum computing + photonic compression papers from arXiv API
- Downloads top 5 PDFs, extracts metadata to JSON
- **Output**: `papers/metadata.json`, `papers/*.pdf`

### Agent 2: VisionModelTrainer
- Fine-tunes MobileNetV3-Small on RTX 4070
- Binary classification: quantum circuit vs compression visual
- **Performance**: 94% validation accuracy, 90% test accuracy (10 epochs)
- **Output**: `models/mobilenetv3_quantum.pth`

### Agent 3: QuantumSimulator
- Implements Qiskit circuits: Toric Code, Anyon Braiding, Surface Code
- Runs 1000-shot simulations with noise analysis (0-5%)
- Scales qubit count from 2-6 for error rate analysis
- **Output**: `simulations/*.png`, `notebooks/quantum_analysis.ipynb`

### Agent 4: CodeQualityPipeline
- Black formatting (line-length: 100)
- Ruff linting (pycodestyle, pyflakes, bugbear)
- pytest with coverage

### Agent 5: ArtifactPackager
- Docker Compose for reproducible deployment
- Streamlit dashboard for visualization

### Agent 6: LocalDeployer
- JupyterLab on `localhost:8888`
- Streamlit on `localhost:8501`

## 🧪 Test Results

```
=================== 16 passed, 0 failed ===================
Coverage: 26% (core pipeline functions tested)
```

## 🛠️ Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run arXiv scraper
python arxiv_scraper.py

# Train vision model (requires GPU)
python vision_trainer.py

# Run quantum simulations
python quantum_simulator.py

# Run tests
pytest tests/ -v --cov=.
```

## 📊 Outputs

```
QuantumResearchPipeline/
├── papers/
│   ├── metadata.json          # Paper metadata
│   └── *.pdf                  # Downloaded papers
├── models/
│   ├── mobilenetv3_quantum.pth   # Trained model
│   └── training_history.json     # Training metrics
├── simulations/
│   ├── toric_code_circuit.png    # Circuit diagram
│   ├── anyon_braiding_circuit.png
│   ├── surface_code_circuit.png
│   ├── error_rate_scaling.png    # Analysis plot
│   └── simulation_results.json
├── notebooks/
│   └── quantum_analysis.ipynb    # Interactive notebook
└── dashboard/
    └── app.py                    # Streamlit dashboard
```

## 📜 License

MIT License - Research and Educational Use
