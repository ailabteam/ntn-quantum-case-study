# main.py (phiên bản cuối cùng cho 2 thuật toán)

import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta
from ntn_environment import NTNEnvironment
from handover_strategies import GreedyStrategy, QAOAStrategy # Import QAOAStrategy

# --- Cấu hình Mô phỏng ---
SIM_DURATION_SECONDS = 30 # Giảm thời gian để chạy QAOA nhanh hơn
TIME_STEP_SECONDS = 1
UE_START_LAT = 16.0544
UE_START_LON = 108.2022
UE_VELOCITY_KMH = 60.0
SNR_OUTAGE_THRESHOLD_DB = 5.0

# --- Cấu hình QAOA ---
LAMBDA_HO = 15.0  # Trọng số handover, cần được tinh chỉnh
PENALTY_P = 50.0 # Trọng số constraint, cần đủ lớn

def analyze_results(df, strategy_name):
    """Phân tích và in ra các chỉ số hiệu năng."""
    print(f"\n--- Analysis for {strategy_name} ---")
    
    avg_snr = df['snr'].mean()
    total_handovers = df['handover'].sum()
    outage_time = df[df['snr'] < SNR_OUTAGE_THRESHOLD_DB]['time_step'].count()
    outage_probability = (outage_time / len(df)) * 100
    
    print(f"Average SNR: {avg_snr:.2f} dB")
    print(f"Total Handovers: {total_handovers}")
    print(f"Outage Probability: {outage_probability:.2f}%")
    
    return {
        'Strategy': strategy_name,
        'Average SNR (dB)': avg_snr,
        'Total Handovers': total_handovers,
        'Outage Probability (%)': outage_probability
    }

if __name__ == '__main__':
    # 1. Khởi tạo môi trường
    env = NTNEnvironment(tle_file='starlink.tle')
    
    # --- Giai đoạn 1: Thu thập dữ liệu môi trường ---
    print("\n--- Phase 1: Collecting environmental data for all timesteps ---")
    all_steps_data = []
    start_time = env.ts.now()
    for t_step in range(0, SIM_DURATION_SECONDS, TIME_STEP_SECONDS):
        current_dt = start_time.utc_datetime() + timedelta(seconds=t_step)
        current_time = env.ts.from_datetime(current_dt)
        ue_location = env.get_ue_location(UE_START_LAT, UE_START_LON, t_step, UE_VELOCITY_KMH)
        visible_sats = env.get_simulation_step_data(ue_location, current_time)
        all_steps_data.append(visible_sats)
    print("Environmental data collected.")

    # --- Giai đoạn 2: Chạy các chiến lược ---
    
    # --- 2.1: Thuật toán Greedy ---
    print("\n--- Phase 2.1: Running Greedy Strategy ---")
    greedy_results = []
    previous_sat_name_greedy = None
    for t_step, step_data in enumerate(all_steps_data):
        chosen_sat = step_data[0] if step_data else None # Greedy luôn chọn cái đầu tiên (SNR cao nhất)
        handover = 0
        if chosen_sat:
            if previous_sat_name_greedy is not None and chosen_sat['name'] != previous_sat_name_greedy:
                handover = 1
            greedy_results.append({'time_step': t_step, 'serving_sat': chosen_sat['name'], 'snr': chosen_sat['snr'], 'handover': handover})
            previous_sat_name_greedy = chosen_sat['name']
        else:
            greedy_results.append({'time_step': t_step, 'serving_sat': None, 'snr': -10, 'handover': 0})
            previous_sat_name_greedy = None
    greedy_results_df = pd.DataFrame(greedy_results)


    # --- 2.2: Thuật toán QAOA ---
    print("\n--- Phase 2.2: Running QAOA Strategy ---")
    qaoa_strategy = QAOAStrategy(lambda_ho=LAMBDA_HO, penalty_p=PENALTY_P)
    qaoa_strategy.solve_qubo(all_steps_data)
    
    qaoa_results = []
    previous_sat_name_qaoa = None
    for t_step, step_data in enumerate(all_steps_data):
        chosen_sat_name = qaoa_strategy.decide(t_step)
        chosen_sat_info = next((sat for sat in step_data if sat['name'] == chosen_sat_name), None)
        handover = 0
        if chosen_sat_info:
            if previous_sat_name_qaoa is not None and chosen_sat_name != previous_sat_name_qaoa:
                handover = 1
            qaoa_results.append({'time_step': t_step, 'serving_sat': chosen_sat_name, 'snr': chosen_sat_info['snr'], 'handover': handover})
            previous_sat_name_qaoa = chosen_sat_name
        else:
            qaoa_results.append({'time_step': t_step, 'serving_sat': None, 'snr': -10, 'handover': 0})
            previous_sat_name_qaoa = None
    qaoa_results_df = pd.DataFrame(qaoa_results)

    # --- Giai đoạn 3: Phân tích và So sánh ---
    greedy_analysis = analyze_results(greedy_results_df, "Greedy")
    qaoa_analysis = analyze_results(qaoa_results_df, "QAOA")

    summary_df = pd.DataFrame([greedy_analysis, qaoa_analysis])
    print("\n\n--- Final Summary ---")
    print(summary_df.to_string())

    # --- Giai đoạn 4: Vẽ đồ thị so sánh ---
    plt.figure(figsize=(12, 6))
    plt.plot(greedy_results_df['time_step'], greedy_results_df['snr'], label='Greedy SNR', color='blue', alpha=0.7)
    plt.plot(qaoa_results_df['time_step'], qaoa_results_df['snr'], label='QAOA SNR', color='green', linewidth=2)
    
    ho_points_greedy = greedy_results_df[greedy_results_df['handover'] == 1]
    plt.scatter(ho_points_greedy['time_step'], ho_points_greedy['snr'], color='red', marker='x', s=100, label='Greedy Handover')
    
    ho_points_qaoa = qaoa_results_df[qaoa_results_df['handover'] == 1]
    plt.scatter(ho_points_qaoa['time_step'], ho_points_qaoa['snr'], color='purple', marker='o', s=100, label='QAOA Handover', facecolors='none', edgecolors='purple', linewidths=2)

    plt.title('Performance Comparison: Greedy vs. QAOA')
    plt.xlabel('Time (seconds)')
    plt.ylabel('SNR (dB)')
    plt.grid(True)
    plt.legend()
    plt.savefig('comparison_plot.png', dpi=600)
    print("\nComparison plot saved to comparison_plot.png (DPI=600)")
