import numpy as np
import random
import math
import copy
from collections import namedtuple

# ==============================================================================
# 1. CÁC THAM SỐ CẤU HÌNH MÔ PHỎNG
# ==============================================================================

# --- Tham số vật lý và mô phỏng ---
SIMULATION_TIME = 100       
NUM_SATELLITES = 10         
USER_POSITION = np.array([0, 0]) 
ALTITUDE = 550              
BASE_SNR_AT_ZENITH = 40     
# <<< THAY ĐỔI QUAN TRỌNG: Thêm góc nâng tối thiểu
MIN_ELEVATION_ANGLE = 25    # Góc nâng tối thiểu để có kết nối (độ)

# --- Tham số cho Hàm Mục Tiêu ---
PREDICTION_WINDOW = 10      
W_SNR = 1.0                 
# <<< THAY ĐỔI QUAN TRỌNG: Giảm phạt để khuyến khích handover khi cần
W_HANDOVER = 15.0           # Phạt 15 điểm SNR cho 1 handover

Satellite = namedtuple('Satellite', ['id', 'radius', 'initial_angle', 'speed_rad_per_sec'])

# ==============================================================================
# 2. MÔ HÌNH MÔI TRƯỜNG VÀ VẬT LÝ
# ==============================================================================

def initialize_satellites(num_sats, altitude):
    sats = []
    for i in range(num_sats):
        radius = altitude + random.uniform(-20, 20)
        initial_angle = random.uniform(0, 2 * math.pi)
        # <<< THAY ĐỔI QUAN TRỌNG: Tăng tốc độ vệ tinh để kịch bản diễn ra nhanh hơn
        speed = math.sqrt(9.81 * (6371 + altitude)) / radius * 0.08 + random.uniform(-0.001, 0.001)
        sats.append(Satellite(id=i, radius=radius, initial_angle=initial_angle, speed_rad_per_sec=speed))
    return sats

def get_satellite_position(satellite, time):
    angle = satellite.initial_angle + satellite.speed_rad_per_sec * time
    x = satellite.radius * math.cos(angle)
    y = satellite.radius * math.sin(angle)
    return np.array([x, y])

# <<< THAY ĐỔI QUAN TRỌNG: Hàm mới để tính góc nâng
def get_elevation_angle(sat_pos):
    """Tính góc nâng của vệ tinh (độ). 0 là chân trời, 90 là đỉnh đầu."""
    # Trong mô hình 2D, chúng ta giả định người dùng ở (0, -R_earth) và Trái Đất là một vòng tròn
    # Để đơn giản hóa, chúng ta sẽ định nghĩa góc nâng dựa trên vị trí y của vệ tinh
    # Vệ tinh ở y cao nhất có góc nâng 90, ở y=0 (chân trời) có góc nâng 0
    if sat_pos[1] < 0: # Vệ tinh ở dưới đường chân trời
        return -1
    angle_from_zenith = math.atan2(abs(sat_pos[0]), sat_pos[1]) # Góc so với đỉnh đầu
    elevation_angle = 90 - math.degrees(angle_from_zenith)
    return elevation_angle

# <<< THAY ĐỔI QUAN TRỌNG: Hàm get_visible_satellites giờ đã thực tế hơn
def get_visible_satellites(satellites, time):
    """Lấy danh sách các vệ tinh có thể kết nối DỰA TRÊN GÓC NÂNG."""
    visible = []
    for sat in satellites:
        pos = get_satellite_position(sat, time)
        elevation = get_elevation_angle(pos)
        if elevation >= MIN_ELEVATION_ANGLE:
            visible.append(sat.id)
    return visible

# <<< THAY ĐỔI QUAN TRỌNG: Hàm SNR giờ phụ thuộc vào góc nâng
def calculate_snr(sat_pos):
    """Tính SNR dựa trên góc nâng, mô phỏng tín hiệu mạnh hơn khi ở trên cao."""
    elevation = get_elevation_angle(sat_pos)
    if elevation < MIN_ELEVATION_ANGLE:
        return 0 # Không có tín hiệu
    
    # SNR giảm dần khi góc nâng giảm
    snr_factor = math.sin(math.radians(elevation)) # Yếu tố sin(góc) là mô hình phổ biến
    snr = BASE_SNR_AT_ZENITH * snr_factor
    return max(5, snr + random.uniform(-0.5, 0.5))

# ==============================================================================
# 3. HÀM MỤC TIÊU VÀ CÁC CHIẾN LƯỢC
# ==============================================================================

def predict_future_snrs(satellites, current_time, window_size):
    predictions = {sat.id: [] for sat in satellites}
    for t_offset in range(window_size):
        future_time = current_time + t_offset
        for sat in satellites:
            future_pos = get_satellite_position(sat, future_time)
            future_snr = calculate_snr(future_pos)
            predictions[sat.id].append(future_snr)
    return predictions

# ... (Hàm calculate_utility và các hàm chiến lược giữ nguyên như cũ) ...
def calculate_utility(decision_sequence, predicted_snrs, current_sat_id):
    full_sequence = [current_sat_id] + decision_sequence
    total_snr_score = sum(
        predicted_snrs[sat_id][t]
        for t, sat_id in enumerate(decision_sequence)
        if sat_id in predicted_snrs and t < len(predicted_snrs[sat_id])
    )
    handover_count = sum(1 for t in range(1, len(full_sequence)) if full_sequence[t] != full_sequence[t-1])
    total_utility = (W_SNR * total_snr_score) - (W_HANDOVER * handover_count)
    return total_utility, total_snr_score, handover_count

def random_strategy(visible_satellites, **kwargs):
    return random.choice(visible_satellites) if visible_satellites else None

def greedy_strategy_with_logging(current_sat_id, visible_satellites, predicted_snrs, **kwargs):
    best_satellite_id = current_sat_id
    best_utility = -np.inf
    
    print("\n" + "="*25 + " SUY NGHĨ CỦA GREEDY " + "="*25)
    print(f"Đang kết nối với: Sat_{current_sat_id}. Các lựa chọn khả thi: {visible_satellites}")

    if not visible_satellites:
        print("Không có vệ tinh nào khả thi.")
        return None
    
    # Trường hợp đặc biệt: Vệ tinh hiện tại sắp mất kết nối
    if current_sat_id not in visible_satellites:
        print("!!! CẢNH BÁO: Vệ tinh hiện tại không còn nhìn thấy. Buộc phải handover.")
        # Đặt utility của việc giữ vệ tinh hiện tại là vô cùng thấp để buộc thay đổi
        best_utility = -np.inf 
    else:
        # Nếu vệ tinh hiện tại vẫn tốt, tính utility của việc giữ nó
        hypothetical_plan = [current_sat_id] * PREDICTION_WINDOW
        utility, _, _ = calculate_utility(hypothetical_plan, predicted_snrs, current_sat_id)
        best_utility = utility
        print(f"  * Giữ nguyên Sat_{current_sat_id} có utility: {utility:.2f}")


    # Duyệt qua các lựa chọn khác để xem có cái nào tốt hơn không
    for candidate_sat_id in visible_satellites:
        if candidate_sat_id == current_sat_id:
            continue # Đã tính ở trên

        hypothetical_plan = [candidate_sat_id] * PREDICTION_WINDOW
        utility, snr_score, ho_count = calculate_utility(hypothetical_plan, predicted_snrs, current_sat_id)

        print(f"  * Thử chuyển sang Sat_{candidate_sat_id}:")
        print(f"    - Utility = ({W_SNR:.1f} * {snr_score:.2f}) - ({W_HANDOVER:.1f} * {ho_count}) = {utility:.2f}")

        if utility > best_utility:
            best_utility = utility
            best_satellite_id = candidate_sat_id
            
    print(f"==> Quyết định của Greedy: Chọn Sat_{best_satellite_id} (Utility: {best_utility:.2f})")
    print("="*72 + "\n")
    
    return best_satellite_id

# ==============================================================================
# 4. VÒNG LẶP MÔ PHỎNG CHÍNH
# ==============================================================================

def run_simulation(strategy_func, satellites, verbose=False):
    # Khởi tạo kết nối ban đầu
    initial_visible_sats = get_visible_satellites(satellites, 0)
    if not initial_visible_sats:
        print("Lỗi: Không có vệ tinh nào khi bắt đầu mô phỏng.")
        return {"avg_snr": 0, "total_handovers": 0, "outage_prob": 100}
    
    initial_snrs = {sat_id: calculate_snr(get_satellite_position(satellites[sat_id], 0)) for sat_id in initial_visible_sats}
    current_sat_id = max(initial_snrs, key=initial_snrs.get)
    
    history = []
    total_handovers = 0
    outage_duration = 0

    for t in range(SIMULATION_TIME):
        visible_satellites = get_visible_satellites(satellites, t)
        
        if not visible_satellites or (current_sat_id is not None and current_sat_id not in visible_satellites):
            if not visible_satellites:
                 outage_duration += 1
                 current_sat_id = None
                 history.append(0)
                 if verbose: print(f"t={t:03d} | MẤT KẾT NỐI!")
                 continue
            # Nếu vệ tinh hiện tại mất kết nối, phải tìm vệ tinh mới ngay lập tức
            # và đây cũng được tính là handover
            if current_sat_id is not None:
                total_handovers += 1

        predicted_snrs = predict_future_snrs(satellites, t, PREDICTION_WINDOW)
        
        strategy_kwargs = {'current_sat_id': current_sat_id, 'visible_satellites': visible_satellites, 'predicted_snrs': predicted_snrs}
        chosen_sat_id = strategy_func(**strategy_kwargs)
        
        if chosen_sat_id is not None and chosen_sat_id != current_sat_id:
            total_handovers += 1
        
        current_sat_id = chosen_sat_id
        
        if current_sat_id is None:
            outage_duration += 1
            history.append(0)
            if verbose: print(f"t={t:03d} | MẤT KẾT NỐI!")
            continue

        current_pos = get_satellite_position(satellites[current_sat_id], t)
        actual_snr = calculate_snr(current_pos)
        history.append(actual_snr)

        if verbose:
            print(f"t={t:03d} | Connected to: Sat_{current_sat_id} | Actual SNR: {actual_snr:.2f} dB")
    
    avg_snr = np.mean(history)
    outage_prob = (outage_duration / SIMULATION_TIME) * 100
    return {"avg_snr": avg_snr, "total_handovers": total_handovers, "outage_prob": outage_prob}


# ==============================================================================
# 5. CHẠY VÀ SO SÁNH
# ==============================================================================

if __name__ == "__main__":
    initial_satellites = initialize_satellites(NUM_SATELLITES, ALTITUDE)
    
    print("\n" + "#"*25 + " BẮT ĐẦU MÔ PHỎNG VỚI GREEDY (Môi trường mới) " + "#"*25)
    greedy_results = run_simulation(greedy_strategy_with_logging, copy.deepcopy(initial_satellites), verbose=False)
    
    print("\n" + "#"*25 + " BẮT ĐẦU MÔ PHỎNG VỚI RANDOM (Môi trường mới) " + "#"*25)
    random_results = run_simulation(random_strategy, copy.deepcopy(initial_satellites), verbose=False)
    
    print("\n\n" + "="*35 + " KẾT QUẢ CUỐI CÙNG " + "="*35)
    print(f"{'Chiến lược':<20} | {'SNR Trung bình (dB)':<25} | {'Tổng số Handover':<20} | {'Xác suất Mất mạng (%)':<25}")
    print("-" * 100)
    
    gr = greedy_results
    print(f"{'Greedy':<20} | {gr['avg_snr']:<25.2f} | {gr['total_handovers']:<20} | {gr['outage_prob']:<25.2f}")
    
    rr = random_results
    print(f"{'Random':<20} | {rr['avg_snr']:<25.2f} | {rr['total_handovers']:<20} | {rr['outage_prob']:<25.2f}")
    print("="*92)
