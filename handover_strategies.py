# handover_strategies.py

import pandas as pd
from datetime import timedelta
import random
from pyqubo import Array, Constraint
import neal

class GreedyStrategy:
    def __init__(self): self.name = "Greedy"
    def decide(self, visible_sats_data):
        return visible_sats_data[0] if visible_sats_data else None

class RandomStrategy:
    def __init__(self): self.name = "Random"
    def decide(self, visible_sats_data):
        return random.choice(visible_sats_data) if visible_sats_data else None

class QIOStrategy:
    def __init__(self, lambda_ho, penalty_p, snr_outage_threshold):
        self.name = "Quantum-Inspired"
        self.lambda_ho = lambda_ho
        self.penalty_p = penalty_p
        self.snr_outage_threshold = snr_outage_threshold

    def solve_and_decide(self, horizon_data, previous_serving_sat_name):
        filtered_horizon_data = []
        for step_sats in horizon_data:
            candidates = [s for s in step_sats if s['snr'] >= self.snr_outage_threshold]
            filtered_horizon_data.append(candidates)

        if not filtered_horizon_data[0]: return None

        T = len(filtered_horizon_data)
        all_sat_names = sorted(list(set(sat['name'] for step in filtered_horizon_data for sat in step)))
        if not all_sat_names: return None
            
        sat_to_idx = {name: i for i, name in enumerate(all_sat_names)}
        num_sats = len(all_sat_names)
        x = Array.create('x', shape=(T, num_sats), vartype='BINARY')
        
        H_qos, H_ho, H_constraint, H_initial_ho = 0, 0, 0, 0

        if previous_serving_sat_name and previous_serving_sat_name in sat_to_idx:
            previous_idx = sat_to_idx[previous_serving_sat_name]
            H_initial_ho = self.lambda_ho * (1 - x[0, previous_idx])

        for t in range(T):
            visible_sats_at_t = {s['name'] for s in filtered_horizon_data[t]}
            for i in range(num_sats):
                sat_name = all_sat_names[i]
                if sat_name in visible_sats_at_t:
                    sat_info = next(s for s in filtered_horizon_data[t] if s['name'] == sat_name)
                    H_qos -= sat_info['snr'] * x[t, i]
                else:
                    H_qos += self.penalty_p * 10 * x[t, i]
            
            H_constraint += self.penalty_p * Constraint((sum(x[t, i] for i in range(num_sats)) - 1)**2, label=f'constraint_t{t}')

        # --- CÔNG THỨC H_ho MỚI VÀ "SẠCH" HƠN ---
        for t in range(1, T):
            # Phạt nếu vệ tinh được chọn ở t khác với ở t-1.
            # (1 - dot_product) sẽ bằng 1 nếu handover, 0 nếu không.
            dot_product = sum(x[t - 1, i] * x[t, i] for i in range(num_sats))
            H_ho += self.lambda_ho * (1 - dot_product)

        H = H_qos + H_ho + H_constraint + H_initial_ho
        
        model = H.compile()
        bqm = model.to_bqm()
        
        sampler = neal.SimulatedAnnealingSampler()
        # Tăng số lần đọc để tìm kiếm tốt hơn
        response = sampler.sample(bqm, num_reads=5, num_sweeps=2000)
        
        decoded_sample = model.decode_sample(response.first.sample, vartype='BINARY')
        
        for var_name, val in decoded_sample.sample.items():
            if val == 1 and var_name.startswith('x[0]['):
                try:
                    i_str = var_name.split('][')[1][:-1]
                    i = int(i_str)
                    return all_sat_names[i]
                except (ValueError, IndexError): continue
        
        return filtered_horizon_data[0][0]['name'] if filtered_horizon_data[0] else None
