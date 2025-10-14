# Quantum-Assisted Handover Optimization in LEO Satellite Networks

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This repository contains the source code for the proof-of-concept case study presented in the paper:

> **"Synergies of AI and Quantum Technologies in Next-Generation Non-Terrestrial Networks: A Comprehensive Survey"**
>
> *Author: Phuc Hao Do*
>
> *(Link to preprint will be added upon publication)*

## Overview

This project provides a simulation framework to compare different handover strategies for a mobile user equipment (UE) served by a Low Earth Orbit (LEO) satellite constellation. The primary goal is to demonstrate the potential of quantum-assisted optimization algorithms (specifically QAOA) in finding a superior trade-off between maximizing connection quality (SNR) and minimizing service disruptions (handovers) compared to classical and AI-based approaches.

The simulation compares three main strategies:
1.  **Greedy Strategy:** A classical baseline that always connects to the satellite with the highest instantaneous Signal-to-Noise Ratio (SNR).
2.  **Random Strategy:** A baseline that randomly selects a visible satellite at each time step.
3.  **Quantum-Assisted (QAOA) Strategy:** Formulates the handover problem over a time horizon as a Quadratic Unconstrained Binary Optimization (QUBO) problem and solves it using the Quantum Approximate Optimization Algorithm (QAOA) simulated with Qiskit.

## Project Structure

```
.
├── ntn-quantum-case-study/
│   ├── main.py               # Main script to run simulations and generate results
│   ├── ntn_environment.py    # Class for simulating the NTN environment (satellites, UE, channel)
│   ├── handover_strategies.py# Implementation of Greedy, Random, and QAOA strategies
│   ├── starlink.tle          # TLE data file for the satellite constellation
│   ├── requirements.txt      # List of required Python packages
│   └── README.md             # This file
```

## Getting Started

### Prerequisites

- Python 3.9+
- Conda package manager

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ailabteam/ntn-quantum-case-study.git
    cd ntn-quantum-case-study
    ```

2.  **Create and activate the Conda environment:**
    ```bash
    conda create -n ntn_q_env python=3.10 -y
    conda activate ntn_q_env
    ```

3.  **Install the required packages:**
    We recommend creating a `requirements.txt` file for easy installation.
    ```bash
    # (Optional) Create requirements.txt
    # pip freeze > requirements.txt 
    
    # Install from requirements (or install manually as below)
    # pip install -r requirements.txt

    # Manual installation
    conda install -c conda-forge numpy pandas matplotlib skyfield -y
    pip install qiskit qiskit-optimization qiskit-aer qiskit_algorithms
    ```

4.  **Download TLE Data:**
    Download the latest TLE data for the Starlink constellation from [Celestrak](https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle) and save it as `starlink.tle` in the root directory of the project.

## How to Run the Simulation

To run the full simulation comparing the different strategies, execute the main script:

```bash
python main.py
```

The script will perform the following steps:
1.  Initialize the NTN environment.
2.  Collect satellite visibility and SNR data over the configured simulation duration.
3.  Run the **Greedy** strategy.
4.  Run the **Random** strategy (once implemented).
5.  Build and solve the QUBO problem using the **QAOA** strategy. **Note:** This step is computationally intensive and may take a significant amount of time.
6.  Print a final summary table comparing the performance metrics.
7.  Generate a comparative plot (`comparison_plot.png`) showing the SNR evolution and handover events for each strategy.

### Configuration

Key simulation parameters can be adjusted at the top of the `main.py` file, including:
- `SIM_DURATION_SECONDS`: Total simulation time.
- `UE_VELOCITY_KMH`: Speed of the mobile user.
- `LAMBDA_HO`: The handover penalty weight in the QUBO formulation.
- `PENALTY_P`: The constraint penalty weight in the QUBO formulation.

## Citation

If you find this work useful in your research, please consider citing our paper:

```bibtex
@article{do2025synergies,
  title   = {Synergies of AI and Quantum Technologies in Next-Generation Non-Terrestrial Networks: A Comprehensive Survey},
  author  = {Do, Phuc Hao},
  journal = {Journal of Communications and Information Networks},
  year    = {2025},
  % (Volume, pages, etc. to be added upon publication)
}
```

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
