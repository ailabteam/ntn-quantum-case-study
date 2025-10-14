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

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
