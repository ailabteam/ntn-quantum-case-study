# handover_strategies.py
import pandas as pd
from datetime import timedelta # <--- THÊM DÒNG NÀY

class GreedyStrategy:
    """
    Thuật toán Handover tham lam.
    Luôn chọn vệ tinh có SNR cao nhất tại mỗi thời điểm.
    """
    def __init__(self):
        self.name = "Greedy"
        self.serving_satellite = None

    def decide(self, visible_sats_data):
        """
        Đưa ra quyết định handover.
        Args:
            visible_sats_data (list): Danh sách các vệ tinh nhìn thấy được,
                                      đã được sắp xếp theo SNR giảm dần.
        Returns:
            dict: Thông tin về vệ tinh được chọn.
        """
        if not visible_sats_data:
            self.serving_satellite = None
            return None # Không có vệ tinh nào để kết nối

        best_sat_info = visible_sats_data[0]
        self.serving_satellite = best_sat_info['sat_obj']
        return best_sat_info

def run_simulation_with_strategy(env, strategy, sim_duration_sec, time_step_sec, ue_lat, ue_lon, ue_vel_kmh):
    """
    Một hàm tổng quát để chạy mô phỏng với một chiến lược handover cụ thể.
    """
    print(f"\n--- Running Simulation for Strategy: {strategy.name} ---")

    start_time = env.ts.now()
    results = []

    previous_sat_name = None

    for t_step in range(0, sim_duration_sec, time_step_sec):
        current_dt = start_time.utc_datetime() + timedelta(seconds=t_step)
        current_time = env.ts.from_datetime(current_dt)
        ue_location = env.get_ue_location(ue_lat, ue_lon, t_step, ue_vel_kmh)

        visible_sats = env.get_simulation_step_data(ue_location, current_time)

        # Gọi hàm decide của chiến lược để chọn vệ tinh
        chosen_sat = strategy.decide(visible_sats)

        handover = False
        if chosen_sat:
            current_sat_name = chosen_sat['name']
            if previous_sat_name is not None and current_sat_name != previous_sat_name:
                handover = True

            results.append({
                'time_step': t_step,
                'serving_sat': current_sat_name,
                'snr': chosen_sat['snr'],
                'elevation': chosen_sat['elevation'],
                'distance': chosen_sat['distance'],
                'handover': int(handover) # 1 if handover, 0 otherwise
            })
            previous_sat_name = current_sat_name
        else:
            # Trường hợp không có vệ tinh nào
            results.append({
                'time_step': t_step,
                'serving_sat': None,
                'snr': -10,  # Giá trị tượng trưng cho outage
                'elevation': None,
                'distance': None,
                'handover': 0
            })
            previous_sat_name = None

    print(f"--- Simulation for {strategy.name} Finished ---")
    return pd.DataFrame(results)

# handover_strategies.py (thêm vào cuối file)

from qiskit_optimization.translators import from_docplex_mp
from qiskit_optimization.algorithms import MinimumEigenOptimizer
#from qiskit_aer.primitives import Sampler
from qiskit_aer.primitives import Sampler, SamplerV2 # <--- SỬA LẠI THÀNH DÒNG NÀY

#from qiskit.algorithms.minimum_eigensolvers import QAOA
from docplex.mp.model import Model
from qiskit_algorithms.minimum_eigensolvers import QAOA
from qiskit_algorithms.optimizers import COBYLA # <--- THÊM DÒNG NÀY


class QAOAStrategy:
    """
    Thuật toán Handover dựa trên QAOA.
    Tối ưu hóa quyết định handover trên một cửa sổ thời gian (toàn bộ thời gian mô phỏng).
    """
    def __init__(self, lambda_ho, penalty_p):
        self.name = "QAOA"
        self.lambda_ho = lambda_ho # Trọng số cho handover penalty
        self.penalty_p = penalty_p # Trọng số cho constraint penalty
        self.solution = None

    def solve_qubo(self, all_steps_data):
        """
        Xây dựng và giải bài toán QUBO cho toàn bộ chuỗi thời gian.
        """
        print("\n--- Building and Solving QUBO with QAOA ---")
        T = len(all_steps_data) # Tổng số time steps

        # --- Sử dụng DOcplex để xây dựng mô hình ---
        mdl = Model('HandoverOptimization')

        # Tạo các biến nhị phân x_i,t
        # x_vars[t][i] là biến cho vệ tinh thứ i tại time step t
        x_vars = []
        for t in range(T):
            step_sats = all_steps_data[t]
            # Key là tên vệ tinh, value là biến docplex
            var_dict = {sat['name']: mdl.binary_var(name=f'x_{sat["name"]}_{t}') for sat in step_sats}
            x_vars.append(var_dict)

        # --- Xây dựng hàm mục tiêu ---
        # 1. QoS Cost (minimize -SNR)
        qos_cost = mdl.sum(-all_steps_data[t][i]['snr'] * x_vars[t][all_steps_data[t][i]['name']]
                           for t in range(T) for i in range(len(all_steps_data[t])))

        # 2. Handover Penalty
        ho_penalty = mdl.sum(self.lambda_ho * x_vars[t-1][sat_i['name']] * x_vars[t][sat_j['name']]
                             for t in range(1, T)
                             for sat_i in all_steps_data[t-1]
                             for sat_j in all_steps_data[t]
                             if sat_i['name'] != sat_j['name'] and sat_i['name'] in x_vars[t-1] and sat_j['name'] in x_vars[t])

        # 3. Constraint Term
        constraint_penalty = mdl.sum(self.penalty_p * (1 - mdl.sum(x_vars[t][sat['name']] for sat in all_steps_data[t]))**2
                                     for t in range(T))

        # Hàm mục tiêu tổng
        mdl.minimize(qos_cost + ho_penalty + constraint_penalty)

        # --- Chuyển đổi sang QuadraticProgram của Qiskit ---
        qp = from_docplex_mp(mdl)
        print(f"QUBO problem created with {qp.get_num_vars()} variables.")

        # --- Thiết lập và chạy QAOA ---
        # Sử dụng Sampler của qiskit-aer để chạy giả lập
        sampler = SamplerV2()
        optimizer_classical = COBYLA(maxiter=50) # Giới hạn số vòng lặp để chạy nhanh hơn
        qaoa = QAOA(sampler=sampler, optimizer=optimizer_classical, reps=1)
        optimizer_qubo = MinimumEigenOptimizer(qaoa)
        print("Solving with QAOA... (This may take a while)")
        result = optimizer_qubo.solve(qp) # Sử dụng optimizer_qubo, không phải optimizer
        print("QAOA finished.")

        # Lưu trữ kết quả
        self.solution = result

    def decide(self, t_step):
        """
        Lấy quyết định cho một time step từ kết quả đã được giải trước đó.
        """
        if self.solution is None:
            raise Exception("QUBO problem has not been solved yet.")

        # Tìm xem vệ tinh nào được chọn (biến có giá trị 1) tại t_step
        for i, var in enumerate(self.solution.variables):
            if var.name.endswith(f'_{t_step}') and self.solution.x[i] == 1:
                chosen_sat_name = var.name.split('_')[1]
                return chosen_sat_name
        return None
