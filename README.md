# Case Study: Satellite Selection in NTN using QAOA vs. a Greedy Algorithm

This repository contains the source code for the practical case study presented in the survey paper: **"Synergies of AI and Quantum Technologies in Next-Generation Non-Terrestrial Networks: A Comprehensive Survey"**.

This code provides a hands-on implementation demonstrating how a combinatorial optimization problem in Non-Terrestrial Networks (NTN)—specifically satellite selection—can be formulated and solved using both a classical heuristic and a quantum algorithm.

## 📖 About the Case Study

The core objective of this case study is to illustrate the process of tackling a complex optimization problem in NTNs. We focus on selecting an optimal subset of satellites from a large constellation to maximize a given utility function (e.g., coverage, quality of service).

To demonstrate the synergy between classical and quantum approaches, we implement and compare two distinct strategies:

1.  **Greedy Algorithm:** A fast, classical heuristic that serves as a baseline. It makes locally optimal choices at each step to find a quick, though not necessarily globally optimal, solution.
2.  **Quantum Approximate Optimization Algorithm (QAOA):** A leading variational quantum algorithm for optimization problems. The satellite selection problem is first mapped to a **Quadratic Unconstrained Binary Optimization (QUBO)** model, which is then solved using QAOA.

This case study serves as a practical example for the concepts discussed in our survey paper, bridging theory with implementation.

## 🏗️ Repository Structure

```
.
├── ntn_environment/       # Module for the NTN environment simulation
├── strategies/            # Contains the implementation of the algorithms
│   ├── greedy.py
│   └── qaoa.py
├── main.py                # Main script to run the simulation and comparison
├── requirements.txt       # Required Python libraries
└── README.md              # This file
```

## ⚙️ Getting Started

### Prerequisites

*   Python 3.8+
*   `pip` and `venv`

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    # For Linux/macOS
    python3 -m venv ntn_q_env
    source ntn_q_env/bin/activate

    # For Windows
    python -m venv ntn_q_env
    .\ntn_q_env\Scripts\activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: Key libraries include `qiskit`, `numpy`, and others for quantum simulation and numerical computation.*

## 🚀 How to Run the Simulation

Execute the main script from the root directory of the project:

```bash
python main.py
```

### Expected Output

The script will sequentially execute the different phases of the simulation, providing logs for each step. The output will look similar to this:

```
Initializing NTN Environment...
Loaded 8470 satellites.

--- Phase 1: Collecting environmental data for all timesteps ---
Environmental data collected.

--- Phase 2.1: Running Greedy Strategy ---
(Results and metrics for the Greedy strategy will be displayed here)

--- Phase 2.2: Running QAOA Strategy ---

--- Building and Solving QUBO with QAOA ---
QUBO problem created with 1059 variables.
Solving with QAOA... (This may take a while)
(Results and metrics for the QAOA strategy will be displayed here)
```

## 🔬 Methodology Overview

1.  **Environment Simulation:** An NTN environment is initialized, loading a constellation of satellites (`8470` in this example).
2.  **Problem Formulation (QUBO):** The satellite selection task is mathematically formulated as a QUBO problem. Each satellite is represented by a binary variable, $x_i \in \{0, 1\}$, where $x_i = 1$ if the satellite is selected and $0$ otherwise. The objective is to minimize a cost function of the form:
    $$ \min_{x} \sum_{i} Q_{i,i}x_i + \sum_{i<j} Q_{i,j}x_i x_j $$
    The matrix $Q$ encodes both the benefits of selecting individual satellites and the costs/benefits of selecting pairs of satellites.
3.  **Solvers:**
    *   The **Greedy solver** iteratively builds a solution by selecting the best possible satellite at each step until a constraint is met.
    *   The **QAOA solver** maps the QUBO instance to an Ising Hamiltonian and uses the QAOA circuit to find the ground state, which corresponds to the optimal solution.

## 📜 Citation

If you find this code useful in your research, please cite our survey paper:

```bibtex
@article{PHDo_2025_ntn_survey,
  author    = {[Your Names]},
  title     = {Synergies of AI and Quantum Technologies in Next-Generation Non-Terrestrial Networks: A Comprehensive Survey},
  journal   = {[Journal/Conference Name]},
  year      = {2024},
  volume    = {[Volume]},
  pages     = {[Pages]},
  publisher = {[Publisher]}
}
```
*(Please update the BibTeX entry with the final publication details.)*

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
