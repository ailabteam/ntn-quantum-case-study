# main.py

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import timedelta
import concurrent.futures
from ntn_environment import NTNEnvironment
from handover_strategies import GreedyStrategy, RandomStrategy, QIOStrategy

# --- CẤU HÌNH MỚI THEO YÊU CẦU REVIEWER 1 ---
SIM_DURATION_SECONDS = 600  # Tăng lên 600s
NUM_UES = 50                # 50 UEs
TIME_STEP_SECONDS = 1
BASE_LAT, BASE_LON = 16.0544, 108.2022
SNR_OUTAGE_THRESHOLD_DB = 5.0

# QUBO Params
HORIZON_SECONDS = 10
LAMBDA_HO = 20.0
PENALTY_P = 100.0

def generate_ue_profiles():
    """Tạo 50 UEs với 3 nhóm vận tốc khác nhau (Static, Vehicular, Airborne)"""
    profiles = []
    for i in range(NUM_UES):
        if i < 15: v = 0.0          # IoT / Static
        elif i < 40: v = 80.0       # Vehicular (Ô tô chạy 80km/h)
        else: v = 900.0             # Airborne (Máy bay 900km/h)
        profiles.append({'id': i, 'velocity': v, 'heading': np.random.uniform(0, 360)})
    return profiles

def simulate_single_ue(ue_profile, env_data, strategy_class, qio_params=None):
    """Hàm chạy độc lập cho 1 UE (để có thể chạy song song đa luồng)"""
    ue_id = ue_profile['id']
    if strategy_class == QIOStrategy:
        strategy = QIOStrategy(**qio_params)
    else:
        strategy = strategy_class()
        
    results, previous_sat = [], None
    for t_step in range(SIM_DURATION_SECONDS):
        if strategy.name == "Quantum-Inspired":
            horizon_end = min(t_step + HORIZON_SECONDS, SIM_DURATION_SECONDS)
            horizon_data = env_data[ue_id][t_step:horizon_end]
            chosen_sat_name = strategy.solve_and_decide(horizon_data, previous_sat)
            chosen_sat_info = next((s for s in env_data[ue_id][t_step] if s['name'] == chosen_sat_name), None)
        else:
            chosen_sat_info = strategy.decide(env_data[ue_id][t_step])
            
        handover, current_sat, snr = 0, None, -10.0
        if chosen_sat_info:
            current_sat, snr = chosen_sat_info['name'], chosen_sat_info['snr']
            if previous_sat is not None and current_sat != previous_sat:
                handover = 1
                
        results.append({'ue_id': ue_id, 'time_step': t_step, 'snr': snr, 'handover': handover})
        previous_sat = current_sat
    return pd.DataFrame(results)

def run_sensitivity_analysis(env_data, ue_profiles):
    """Chạy phân tích độ nhạy của Lambda_HO (Reviewer 1)"""
    print("\n--- Running Sensitivity Analysis for Lambda_HO ---")
    lambda_values = [5, 10, 20, 30, 50]
    avg_snrs, total_hos = [], []
    
    # Chỉ test trên 5 UEs đại diện để tiết kiệm thời gian
    test_ues = ue_profiles[:5] 
    
    for l_ho in lambda_values:
        print(f"Testing Lambda_HO = {l_ho}...")
        qio_params = {'lambda_ho': l_ho, 'penalty_p': PENALTY_P, 'snr_outage_threshold': SNR_OUTAGE_THRESHOLD_DB}
        
        results_list = []
        for ue in test_ues:
            res = simulate_single_ue(ue, env_data, QIOStrategy, qio_params)
            results_list.append(res)
            
        df = pd.concat(results_list)
        avg_snrs.append(df['snr'].mean())
        total_hos.append(df['handover'].sum() / len(test_ues)) # Handover trung bình mỗi UE
        
    # Plot Sensitivity
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax2 = ax1.twinx()
    ax1.plot(lambda_values, avg_snrs, 'g-o', label='Average SNR (dB)', linewidth=2)
    ax2.plot(lambda_values, total_hos, 'm-s', label='Avg Handovers per UE', linewidth=2)
    
    ax1.set_xlabel(r'Handover Penalty ($\lambda_{HO}$)', fontsize=12)
    ax1.set_ylabel('Average SNR (dB)', color='g', fontsize=12)
    ax2.set_ylabel('Average Handovers', color='m', fontsize=12)
    plt.title(r'Sensitivity Analysis of QUBO Penalty Parameter $\lambda_{HO}$', fontsize=14)
    fig.tight_layout()
    plt.savefig('sensitivity_analysis.png', dpi=600)
    print("Sensitivity Plot saved to sensitivity_analysis.png")

if __name__ == '__main__':
    print(f"========== NTN QUANTUM SIMULATION V2 (Multi-UEs, {SIM_DURATION_SECONDS}s) ==========")
    env = NTNEnvironment()
    ue_profiles = generate_ue_profiles()
    
    # 1. Thu thập dữ liệu môi trường (Pre-compute)
    print("\n[Phase 1] Pre-computing environment data for 50 UEs over 600s...")
    env_data = {ue['id']: [] for ue in ue_profiles}
    start_time = env.ts.now()
    
    for t_step in range(SIM_DURATION_SECONDS):
        if t_step % 60 == 0: print(f"Processing time step {t_step}/{SIM_DURATION_SECONDS}...")
        current_dt = start_time.utc_datetime() + timedelta(seconds=t_step)
        current_time = env.ts.from_datetime(current_dt)
        env.update_rain_cells(TIME_STEP_SECONDS)
        
        for ue in ue_profiles:
            loc = env.get_ue_location(BASE_LAT, BASE_LON, t_step, ue['velocity'], ue['heading'])
            env_data[ue['id']].append(env.get_simulation_step_data(loc, current_time))
            
    # 2. Chạy chiến lược song song (Tận dụng sức mạnh CPU)
    print("\n[Phase 2] Running Handover Strategies in Parallel...")
    strategies_to_run = [
        ("Greedy", GreedyStrategy, None),
        ("Quantum-Inspired", QIOStrategy, {'lambda_ho': LAMBDA_HO, 'penalty_p': PENALTY_P, 'snr_outage_threshold': SNR_OUTAGE_THRESHOLD_DB})
    ]
    
    final_summaries = []
    
    for name, strat_class, params in strategies_to_run:
        print(f"Simulating {name} for {NUM_UES} UEs...")
        # Dùng Multiprocessing để chia 50 UEs ra các lõi CPU
        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = [executor.submit(simulate_single_ue, ue, env_data, strat_class, params) for ue in ue_profiles]
            all_ue_results = [f.result() for f in concurrent.futures.as_completed(futures)]
            
        full_df = pd.concat(all_ue_results)
        avg_snr = full_df['snr'].mean()
        total_ho = full_df['handover'].sum()
        avg_ho_per_ue = total_ho / NUM_UES
        outage = (full_df[full_df['snr'] < SNR_OUTAGE_THRESHOLD_DB].shape[0] / len(full_df)) * 100
        
        final_summaries.append({'Strategy': name, 'Avg SNR (dB)': avg_snr, 'Avg HO / UE': avg_ho_per_ue, 'Outage (%)': outage})

    # In kết quả
    summary_df = pd.DataFrame(final_summaries)
    print("\n\n" + "="*40 + " FINAL AVERAGED RESULTS " + "="*40)
    print(f"(Averaged over {NUM_UES} UEs, Duration: {SIM_DURATION_SECONDS}s, Mixed LEO/MEO)")
    print(summary_df.to_string(index=False))

    # 3. Phân tích độ nhạy
    run_sensitivity_analysis(env_data, ue_profiles)
    
    print("\nAll tasks completed successfully!")
