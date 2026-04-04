# Scalable Quantum-Inspired Handover Optimization in Multi-Layered NTNs

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

This repository contains the source code and experimental framework for the case study presented in the survey paper:

> **"Synergies of AI and Quantum Technologies in Next-Generation Non-Terrestrial Networks: A Comprehensive Survey"**
>
> **Author:** Phuc Hao Do
> 
> **Journal:** Journal of Communications and Information Networks (JCIN)
> **Status:** Revised (April 2026)

---

## 🌟 Overview

Handover management is a critical challenge in Non-Terrestrial Networks (NTNs) due to high orbital velocities and dynamic channel conditions. This project demonstrates a **Quantum-Inspired Optimization (QIO)** approach using **Quadratic Unconstrained Binary Optimization (QUBO)** to find an optimal balance between signal quality (SNR) and connection stability.

### Key Revision Enhancements (v2.0)
The latest version (located in the `/revised` directory) includes a significantly expanded simulation suite to address scalability and realism:
- **Large-Scale Multi-UE Scenario:** Evaluated over **50 heterogeneous UEs** with diverse mobility patterns (Static IoT, 80 km/h Vehicular, and 900 km/h Airborne).
- **Multi-Layered NTN:** Integration of mixed-orbit constellations consisting of **Starlink (LEO)** and **O3b (MEO)** satellites.
- **Extended Duration:** Simulation window increased to **600 seconds** to capture long-term orbital dynamics.
- **Performance:** Achieved an approximately **84% reduction in handovers** compared to the classical Greedy baseline while maintaining a 0% outage rate.
- **Sensitivity Analysis:** Automated evaluation of the handover penalty parameter ($\lambda_{HO}$).

---

## 📂 Project Structure

```text
.
├── revised/                  # PRIMARY: Updated code for the Revised Manuscript
│   ├── main.py               # Main script with Multi-processing support
│   ├── ntn_environment.py    # Mixed LEO/MEO Environment & Radar-sweep filtering
│   ├── handover_strategies.py# QUBO formulation & D-Wave Neal Sampler logic
│   └── sensitivity_analysis.png # Results of the parameter sweep
├── starlink.tle              # LEO orbit data
├── o3b.tle                   # MEO orbit data
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- High-performance CPU (The simulation uses `concurrent.futures` for parallel processing across 50 UEs)

### Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/ailabteam/ntn-quantum-case-study.git
   cd ntn-quantum-case-study
   ```

2. **Set up the environment:**
   ```bash
   conda create -n ntn_quantum python=3.10 -y
   conda activate ntn_quantum
   pip install numpy pandas matplotlib skyfield pyqubo dwave-neal
   ```

3. **Download Required Ephemeris:**
   The code will automatically download `de421.bsp` and TLE files on the first run.

---

## 📊 Running the Simulation

To reproduce the results shown in the revised paper:

```bash
cd revised
python main.py
```

### What happens during execution?
1. **Phase 1 (Environmental Pre-computation):** The system performs a "Radar Sweep" to filter visible satellites from a pool of >10,000 objects and calculates the SNR for all 50 UEs across 600 time steps.
2. **Phase 2 (Parallel Optimization):** The simulator runs the Greedy and QIO strategies. The QIO strategy utilizes the **Simulated Annealing** sampler to solve the QUBO problem for each rolling horizon window.
3. **Phase 3 (Sensitivity Analysis):** The script executes a parameter sweep for $\lambda_{HO} \in \{5, 10, 20, 30, 50\}$ and generates a trade-off plot.

---

## 📈 Results

| Strategy | Avg. SNR (dB) | Avg. Handovers / UE | Outage (%) |
| :--- | :---: | :---: | :---: |
| Greedy | 34.34 | 256.68 | 0.0% |
| **Quantum-Inspired (QIO)** | **33.84** | **42.15** | **0.0%** |

The QIO strategy provides a dramatic improvement in network stability, making it highly suitable for 6G NTN environments where handover signaling overhead must be minimized.

---

## 📝 Citation

If you use this code or the survey in your research, please cite:

```bibtex
@article{do2025synergies,
  title={Synergies of AI and Quantum Technologies in Next-Generation Non-Terrestrial Networks: A Comprehensive Survey},
  author={Do, Phuc Hao},
  journal={Journal of Communications and Information Networks},
  year={2025},
  note={Manuscript under revision}
}
```

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

