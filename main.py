# main.py

import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta
from ntn_environment import NTNEnvironment
from handover_strategies import GreedyStrategy, RandomStrategy, QIOStrategy
import numpy as np

# --- Cấu hình Mô phỏng ---
NUM_SIMULATION_RUNS = 10     # SỐ LẦN CHẠY MÔ PHỎNG
SIM_DURATION_SECONDS = 120
TIME_STEP_SECONDS = 1
UE_START_LAT = 16.0544
UE_START_LON = 108.2022
UE_VELOCITY_KMH = 60.0
SNR_OUTAGE_THRESHOLD_DB = 5.0

# --- Cấu hình QIO ---
HORIZON_SECONDS = 10
LAMBDA_HO = 20.0
PENALTY_P = 100.0

def analyze_results(df, strategy_name):
    print(f"\n--- Analysis for {strategy_name} ---")
    avg_snr = df['snr'].mean()
    total_handovers = df['handover'].sum()
    outage_probability = (df[df['snr'] < SNR_OUTAGE_THRESHOLD_DB].shape[0] / len(df)) * 100
    print(f"Average SNR: {avg_snr:.2f} dB")
    print(f"Total Handovers: {total_handovers}")
    print(f"Outage Probability: {outage_probability:.2f}%")
    return {'Strategy': strategy_name, 'Average SNR (dB)': avg_snr, 'Total Handovers': total_handovers, 'Outage Probability (%)': outage_probability}

def run_stateless_simulation(all_steps_data, strategy_class):
    strategy = strategy_class()
    strategy_name = strategy.name
    print(f"\n--- Running Simulation for Strategy: {strategy_name} ---")
    results, previous_sat_name = [], None
    for t_step, step_data in enumerate(all_steps_data):
        chosen_sat_info = strategy.decide(step_data)
        handover, current_sat_name, snr = 0, None, -10.0
        if chosen_sat_info:
            current_sat_name, snr = chosen_sat_info['name'], chosen_sat_info['snr']
            if previous_sat_name is not None and current_sat_name != previous_sat_name:
                handover = 1
        results.append({'time_step': t_step, 'serving_sat': current_sat_name, 'snr': snr, 'handover': handover})
        previous_sat_name = current_sat_name
    print(f"--- Simulation for {strategy_name} Finished ---")
    return pd.DataFrame(results)

def run_qio_simulation(all_steps_data, all_sat_names, qio_params):
    print("\n--- Running Simulation for Strategy: Quantum-Inspired (Rolling Horizon) ---")
    qio_strategy = QIOStrategy(**qio_params)
    results, previous_sat_name = [], None
    for t_step in range(SIM_DURATION_SECONDS):
        horizon_end = min(t_step + HORIZON_SECONDS, SIM_DURATION_SECONDS)
        horizon_data = all_steps_data[t_step:horizon_end]
        
        chosen_sat_name = qio_strategy.solve_and_decide(horizon_data, previous_sat_name)
        
        step_data = all_steps_data[t_step]
        chosen_sat_info = next((s for s in step_data if s['name'] == chosen_sat_name), None)
        handover, current_sat_name, snr = 0, None, -10.0
        if chosen_sat_info:
            current_sat_name, snr = chosen_sat_info['name'], chosen_sat_info['snr']
            if previous_sat_name is not None and current_sat_name != previous_sat_name:
                handover = 1
        
        results.append({'time_step': t_step, 'serving_sat': current_sat_name, 'snr': snr, 'handover': handover})
        previous_sat_name = current_sat_name
        print(f"\rTime: {t_step + 1}/{SIM_DURATION_SECONDS} | Decision: {current_sat_name}", end="")
    print("\n--- Simulation for Quantum-Inspired Finished ---")
    return pd.DataFrame(results)

if __name__ == '__main__':
    all_runs_results = []

    for run in range(NUM_SIMULATION_RUNS):
        print(f"\n\n{'='*30} STARTING SIMULATION RUN {run + 1}/{NUM_SIMULATION_RUNS} {'='*30}")
        
        env = NTNEnvironment(tle_file='starlink.tle')
        
        print(f"\n--- [Run {run+1}] Phase 1: Collecting environmental data... ---")
        all_steps_data = []
        start_time = env.ts.now()
        for t_step in range(SIM_DURATION_SECONDS):
            current_dt = start_time.utc_datetime() + timedelta(seconds=t_step)
            current_time = env.ts.from_datetime(current_dt)
            ue_location = env.get_ue_location(UE_START_LAT, UE_START_LON, t_step, UE_VELOCITY_KMH)
            env.update_rain_cells(TIME_STEP_SECONDS)
            all_steps_data.append(env.get_simulation_step_data(ue_location, current_time))
        print("Environmental data collected.")
        
        all_sat_names = sorted(list(set(sat['name'] for step in all_steps_data for sat in step)))

        greedy_results_df = run_stateless_simulation(all_steps_data, GreedyStrategy)
        random_results_df = run_stateless_simulation(all_steps_data, RandomStrategy)
        
        qio_params = {'lambda_ho': LAMBDA_HO, 'penalty_p': PENALTY_P, 'snr_outage_threshold': SNR_OUTAGE_THRESHOLD_DB}
        qio_results_df = run_qio_simulation(all_steps_data, all_sat_names, qio_params)

        analyses = [
            analyze_results(greedy_results_df, "Greedy"),
            analyze_results(random_results_df, "Random"),
            analyze_results(qio_results_df, "Quantum-Inspired")
        ]
        all_runs_results.extend(analyses)

    summary_df = pd.DataFrame(all_runs_results)
    final_avg_results = summary_df.groupby('Strategy').mean().reset_index()
    final_avg_results = final_avg_results[['Strategy', 'Average SNR (dB)', 'Total Handovers', 'Outage Probability (%)']]
    
    print("\n\n" + "="*35 + " FINAL AVERAGED RESULTS " + "="*35)
    print(f"(Averaged over {NUM_SIMULATION_RUNS} runs)")
    print(final_avg_results.to_string(index=False))

    print("\nGenerating plot for the last simulation run...")
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(15, 7))
    ax.plot(greedy_results_df['time_step'], greedy_results_df['snr'], label='Greedy SNR', color='dodgerblue', alpha=0.7, linestyle='--')
    ax.plot(random_results_df['time_step'], random_results_df['snr'], label='Random SNR', color='silver', alpha=0.8, zorder=1)
    ax.plot(qio_results_df['time_step'], qio_results_df['snr'], label='Quantum-Inspired SNR', color='forestgreen', linewidth=2.5, zorder=3)
    ho_points_qio = qio_results_df[qio_results_df['handover'] == 1]
    ax.scatter(ho_points_qio['time_step'], ho_points_qio['snr'], color='darkviolet', marker='o', s=120, label='QIO Handover', facecolors='none', edgecolors='darkviolet', linewidths=2, zorder=5)
    ho_points_greedy = greedy_results_df[greedy_results_df['handover'] == 1]
    ax.scatter(ho_points_greedy['time_step'], ho_points_greedy['snr'], color='red', marker='x', s=80, label='Greedy Handover', zorder=4)
    ax.set_title(f'Performance Comparison (Sample Run from Monte Carlo Simulation)', fontsize=16)
    ax.set_xlabel('Time (seconds)', fontsize=12)
    ax.set_ylabel('SNR (dB)', fontsize=12)
    ax.legend(fontsize=11)
    fig.tight_layout()
    plt.savefig('comparison_plot_final.png', dpi=600)
    print("\nFinal comparison plot saved to comparison_plot_final.png (DPI=600)")
