# main.py

import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta
from ntn_environment import NTNEnvironment
from handover_strategies import GreedyStrategy, RandomStrategy, QIOStrategy
import numpy as np # Thêm import numpy

# --- Cấu hình Mô phỏng ---
NUM_SIMULATION_RUNS = 10     # SỐ LẦN CHẠY MÔ PHỎNG
SIM_DURATION_SECONDS = 120
# ... (các cấu hình khác giữ nguyên) ...
HORIZON_SECONDS = 10
LAMBDA_HO = 20.0
PENALTY_P = 100.0

# ... (hàm analyze_results và các hàm run_simulation giữ nguyên) ...

if __name__ == '__main__':
    
    all_runs_results = []

    for run in range(NUM_SIMULATION_RUNS):
        print(f"\n\n{'='*30} STARTING SIMULATION RUN {run + 1}/{NUM_SIMULATION_RUNS} {'='*30}")
        
        # 1. Khởi tạo môi trường MỚI cho mỗi lần chạy để có tính ngẫu nhiên
        env = NTNEnvironment(tle_file='starlink.tle')
        
        # 2. Thu thập dữ liệu môi trường cho lần chạy này
        print(f"\n--- [Run {run+1}] Phase 1: Collecting environmental data... ---")
        all_steps_data = []
        start_time = env.ts.now()
        for t_step in range(SIM_DURATION_SECONDS):
            current_dt = start_time.utc_datetime() + timedelta(seconds=t_step)
            current_time = env.ts.from_datetime(current_dt)
            ue_location = env.get_ue_location(16.0544, 108.2022, t_step, 60.0)
            env.update_rain_cells(1)
            all_steps_data.append(env.get_simulation_step_data(ue_location, current_time))
        print("Environmental data collected.")
        
        # 3. Chạy các chiến lược
        greedy_results_df = run_stateless_simulation(all_steps_data, GreedyStrategy)
        random_results_df = run_stateless_simulation(all_steps_data, RandomStrategy)
        qio_params = {'lambda_ho': LAMBDA_HO, 'penalty_p': PENALTY_P, 'snr_outage_threshold': 5.0}
        qio_results_df = run_qio_simulation(all_steps_data, qio_params)

        # 4. Phân tích và lưu kết quả của lần chạy này
        analyses = [
            analyze_results(greedy_results_df, "Greedy"),
            analyze_results(random_results_df, "Random"),
            analyze_results(qio_results_df, "Quantum-Inspired")
        ]
        all_runs_results.extend(analyses)

    # --- TÍNH TOÁN KẾT QUẢ TRUNG BÌNH CUỐI CÙNG ---
    summary_df = pd.DataFrame(all_runs_results)
    final_avg_results = summary_df.groupby('Strategy').mean().reset_index()
    
    # Sắp xếp lại thứ tự cột cho đẹp
    final_avg_results = final_avg_results[['Strategy', 'Average SNR (dB)', 'Total Handovers', 'Outage Probability (%)']]
    
    print("\n\n" + "="*35 + " FINAL AVERAGED RESULTS " + "="*35)
    print(f"(Averaged over {NUM_SIMULATION_RUNS} runs)")
    print(final_avg_results.to_string(index=False))

    # --- Vẽ đồ thị của LẦN CHẠY CUỐI CÙNG để minh họa ---
    print("\nGenerating plot for the last simulation run...")
    # ... (phần code vẽ đồ thị giữ nguyên y hệt như cũ, nó sẽ tự động dùng kết quả của lần chạy cuối) ...
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
