

# Optimización Escalable de Handover Inspirada en Cuántica en NTNs de Capas Múltiples

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Este repositorio contiene el código fuente y el marco experimental para el caso de estudio presentado en el artículo de revisión:

> **"Sinergias entre la IA y las Tecnologías Cuánticas en Redes No Terrestres de Próxima Generación: Una Revisión Integral"**
>
> **Autor:** Phuc Hao Do
> 
> **Revista:** Journal of Communications and Information Networks (JCIN)
> **Estado:** Revisado (Abril 2026)

---

## 🌟 Descripción General

La gestión de handover es un desafío crítico en las Redes No Terrestres (NTNs) debido a las altas velocidades orbitales y las condiciones dinámicas del canal. Este proyecto demuestra un enfoque de **Optimización Inspirada en Cuántica (QIO)** utilizando **Optimización Cuadrática Binaria sin Restricciones (QUBO)** para encontrar un equilibrio óptimo entre la calidad de la señal (SNR) y la estabilidad de la conexión.

### Mejoras Clave de la Revisión (v2.0)
La última versión (ubicada en el directorio `/revised`) incluye un conjunto de simulaciones ampliamente expandido para abordar la escalabilidad y el realismo:
- **Escenario Multi-UE a Gran Escala:** Evaluado con **50 UEs heterogéneos** con patrones de movilidad diversos (IoT Estático, Vehicular a 80 km/h y Aéreo a 900 km/h).
- **NTN de Capas Múltiples:** Integración de constelaciones de órbitas mixtas compuestas por satélites **Starlink (LEO)** y **O3b (MEO)**.
- **Duración Extendida:** La ventana de simulación se aumentó a **600 segundos** para capturar la dinámica orbital a largo plazo.
- **Rendimiento:** Se logró una **reducción aproximada del 84% en handovers** en comparación con la línea base clásica Greedy, manteniendo una tasa de interrupción del 0%.
- **Análisis de Sensibilidad:** Evaluación automatizada del parámetro de penalización de handover ($\lambda_{HO}$).

---

## 📂 Estructura del Proyecto

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

## 🚀 Primeros Pasos

### Requisitos Previos
- Python 3.10 o superior
- CPU de alto rendimiento (La simulación utiliza `concurrent.futures` para procesamiento paralelo en 50 UEs)

### Instalación
1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/ailabteam/ntn-quantum-case-study.git
   cd ntn-quantum-case-study
   ```

2. **Configurar el entorno:**
   ```bash
   conda create -n ntn_quantum python=3.10 -y
   conda activate ntn_quantum
   pip install numpy pandas matplotlib skyfield pyqubo dwave-neal
   ```

3. **Descargar Efemérides Requeridas:**
   El código descargará automáticamente el archivo `de421.bsp` y los archivos TLE en la primera ejecución.

---

## 📊 Ejecutar la Simulación

Para reproducir los resultados mostrados en el artículo revisado:

```bash
cd revised
python main.py
```

### ¿Qué ocurre durante la ejecución?
1. **Fase 1 (Precómputo Ambiental):** El sistema realiza un "Escaneo Radar" para filtrar satélites visibles de un grupo de >10,000 objetos y calcula el SNR para todos los 50 UEs a lo largo de 600 pasos de tiempo.
2. **Fase 2 (Optimización Paralela):** El simulador ejecuta las estrategias Greedy y QIO. La estrategia QIO utiliza el muestreador de **Temple Simulado (Simulated Annealing)** para resolver el problema QUBO para cada ventana de horizonte rodante.
3. **Fase 3 (Análisis de Sensibilidad):** El script ejecuta un barrido de parámetros para $\lambda_{HO} \in \{5, 10, 20, 30, 50\}$ y genera un gráfico de compensación.

---

## 📈 Resultados

| Estrategia | SNR Prom. (dB) | Handovers Prom. / UE | Interrupción (%) |
| :--- | :---: | :---: | :---: |
| Greedy | 34.34 | 256.68 | 0.0% |
| **Quantum-Inspired (QIO)** | **33.84** | **42.15** | **0.0%** |

La estrategia QIO proporciona una mejora drástica en la estabilidad de la red, lo que la hace altamente adecuada para entornos NTN de 6G donde la sobrecarga de señalización de handover debe minimizarse.

---

## 📝 Citación

Si utiliza este código o la revisión en su investigación, por favor cite:

```bibtex
@article{do2025synergies,
  title={Synergies of AI and Quantum Technologies in Next-Generation Non-Terrestrial Networks: A Comprehensive Survey},
  author={Do, Phuc Hao},
  journal={Journal of Communications and Information Networks},
  year={2025},
  note={Manuscript under revision}
}
```

## 📄 Licencia
Este proyecto está licenciado bajo la Licencia MIT - consulte el archivo LICENSE para más detalles.
