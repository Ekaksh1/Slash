# F1 Rust Module - Build Instructions

This module provides high-performance Rust implementations of the scoring engine and data preprocessing functions.

## Prerequisites

1. **Rust Toolchain**
   ```bash
   # Install Rust if not already installed
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   
   # Ensure you have the stable toolchain
   rustup default stable
   
   # Add target for Python extension
   rustup target add x86_64-apple-darwin  # macOS
   rustup target add x86_64-unknown-linux-gnu  # Linux
   rustup target add x86_64-pc-windows-msvc  # Windows
   ```

2. **Python Development Headers**
   - **Linux**: `sudo apt install python3-dev` or `sudo yum install python3-devel`
   - **macOS**: Already included with Python
   - **Windows**: Already included with Python

## Build Instructions

### Option 1: Build and Install (Recommended)

```bash
cd rust_f1

# Build the Rust extension
pip install maturin
maturin build --release

# Install the built wheel
pip install --target ../backend/target/wheels *.whl

# Or install directly
pip install maturin
maturin develop --release
```

### Option 2: Using setuptools

```bash
cd rust_f1

# Build in development mode
pip install -e .
```

### Option 3: Manual Build

```bash
cd rust_f1

# Build the shared library
cargo build --release

# Set Python path to include the compiled module
export PYTHONPATH="${PYTHONPATH}:$(pwd)/target/release"
```

## Verifying the Installation

```python
# Test import
python -c "from backend.rust_scoring import is_using_rust; print(f'Rust enabled: {is_using_rust()}')"

# Test functions
python -c "
from backend.rust_scoring import calculate_driver_score, calculate_team_score

driver_score = calculate_driver_score(
    avg_finish=2.5,
    qualifying_avg=1.8,
    recent_form=0.85,
    dnf_risk=0.1,
    track_affinity=0.75,
    weather_conditions={'rain': False}
)
print(f'Driver Score: {driver_score:.4f}')

team_score = calculate_team_score(0.8, 0.85, 0.9)
print(f'Team Score: {team_score:.4f}')
"
```

## Performance Benchmarking

```bash
# Run benchmark
python -c "
import time
from backend.rust_scoring import (
    calculate_batch_driver_scores, 
    calculate_batch_final_scores,
    is_using_rust
)

print(f'Using Rust: {is_using_rust()}')

# Create test data (20 drivers)
metrics = [
    {
        'avg_finish': 2.5 + i * 0.5,
        'qualifying_avg': 1.8 + i * 0.3,
        'recent_form': 0.85 - i * 0.02,
        'dnf_risk': 0.1 + i * 0.01,
        'track_affinity': 0.75 - i * 0.01
    }
    for i in range(20)
]

team_scores = [0.7 + i * 0.02 for i in range(20)]

# Benchmark
iterations = 1000

start = time.time()
for _ in range(iterations):
    driver_scores = calculate_batch_driver_scores(metrics)
    final_scores = calculate_batch_final_scores(driver_scores, team_scores)
elapsed = time.time() - start

print(f'Processed {iterations} iterations in {elapsed:.3f}s')
print(f'Average time per iteration: {elapsed/iterations*1000:.3f}ms')
"
```

## Architecture

```
┌─────────────────────────────────────────────┐
│           Python Application                 │
│                                             │
│  backend/prediction_generator.py            │
│  backend/scoring_engine.py                  │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│         backend/rust_scoring.py              │
│    (Python wrapper with fallback)           │
└─────────────────┬───────────────────────────┘
                  │
                  ▼ (if installed)
┌─────────────────────────────────────────────┐
│            f1_rust (Rust extension)          │
│                                             │
│  - scoring.rs: Driver/Team scoring          │
│  - preprocessing.rs: Data preprocessing      │
│                                             │
│  Uses: Rayon (parallel), PyO3 (bindings)    │
└─────────────────────────────────────────────┘
```

## Troubleshooting

### "Unable to find Python include files"
```bash
# Ubuntu/Debian
sudo apt install python3-dev

# Fedora/RHEL
sudo yum install python3-devel
```

### "Linker error during compilation"
```bash
# Install build tools
# Ubuntu/Debian
sudo apt install build-essential

# macOS
xcode-select --install
```

### "maturin: command not found"
```bash
pip install maturin
```

## Performance Expectations

| Operation | Python (ms) | Rust (ms) | Speedup |
|-----------|-------------|-----------|---------|
| Batch Score Calc (20 drivers) | ~2.5 | ~0.3 | ~8x |
| Single Driver Score | ~0.1 | ~0.01 | ~10x |
| Data Preprocessing | ~5.0 | ~0.5 | ~10x |

*Note: Actual speedup depends on hardware and data size*
