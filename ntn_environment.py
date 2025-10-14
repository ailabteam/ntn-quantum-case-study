# ntn_environment.py

import numpy as np
from skyfield.api import load, EarthSatellite, Topos
from datetime import timedelta

class NTNEnvironment:
    """
    Class để quản lý và mô phỏng môi trường NTN.
    Bao gồm vị trí vệ tinh, chuyển động của UE, và tính toán kênh truyền.
    """
    def __init__(self, tle_file, min_elevation_deg=25.0):
        print("Initializing NTN Environment...")
        self.ts = load.timescale()
        self.eph = load('de421.bsp')
        self.earth = self.eph['earth']
        self.satellites = load.tle_file(tle_file)
        self.min_elevation_deg = min_elevation_deg
        print(f"Loaded {len(self.satellites)} satellites.")

        # --- Các tham số cho mô hình kênh truyền (ví dụ) ---
        self.satellite_eirp = 45  # dBW (Effective Isotropic Radiated Power)
        self.ue_gt = 1           # dB/K (G/T ratio of User Equipment)
        self.frequency_hz = 12e9 # Ku-band frequency (12 GHz)
        self.boltzmann_k = -228.6 # dBW/K/Hz

    def get_ue_location(self, base_lat, base_lon, time_step_sec, velocity_kmh):
        """
        Tính toán vị trí mới của UE dựa trên chuyển động.
        Giả định UE di chuyển về phía Đông.
        """
        # Chuyển đổi vận tốc từ km/h sang độ kinh tuyến/giây
        # 1 độ kinh tuyến ở xích đạo ~ 111.32 km
        # Ở vĩ độ lat, 1 độ kinh tuyến ~ 111.32 * cos(lat)
        deg_per_km = 1 / (111.32 * np.cos(np.deg2rad(base_lat)))
        velocity_deg_per_sec = (velocity_kmh / 3600) * deg_per_km
        
        new_lon = base_lon + time_step_sec * velocity_deg_per_sec
        return Topos(latitude_degrees=base_lat, longitude_degrees=new_lon)

    def calculate_snr(self, distance_km):
        """
        Tính toán SNR dựa trên mô hình Free-Space Path Loss (FSPL).
        """
        # 1. Tính Free-Space Path Loss (FSPL) in dB
        # FSPL (dB) = 20*log10(d) + 20*log10(f) + 20*log10(4*pi/c)
        lambda_m = 3e8 / self.frequency_hz # bước sóng
        fspl_db = 20 * np.log10(distance_km * 1000) + 20 * np.log10(self.frequency_hz) - 147.55
        
        # 2. Tính công suất tín hiệu thu được (Received Power) in dBW
        received_power_dbw = self.satellite_eirp - fspl_db + self.ue_gt
        
        # 3. Giả định một băng thông, ví dụ: 20 MHz = 73 dBHz
        bandwidth_dbhz = 10 * np.log10(20e6)
        
        # 4. Tính nhiễu nền (Noise Power) in dBW
        noise_power_dbw = self.boltzmann_k + bandwidth_dbhz
        
        # 5. Tính SNR in dB
        snr_db = received_power_dbw - noise_power_dbw
        
        # Thêm một chút nhiễu ngẫu nhiên để mô phỏng fading
        snr_db += np.random.normal(0, 1.5)
        
        return snr_db

    def get_simulation_step_data(self, ue_location, current_time):
        """
        Tại một bước thời gian, lấy thông tin về các vệ tinh nhìn thấy được và SNR của chúng.
        """
        step_data = []
        for sat in self.satellites:
            difference = sat - ue_location
            topocentric = difference.at(current_time)
            alt, az, distance = topocentric.altaz()
            
            if alt.degrees > self.min_elevation_deg:
                snr = self.calculate_snr(distance.km)
                step_data.append({
                    'sat_obj': sat,
                    'name': sat.name,
                    'elevation': alt.degrees,
                    'distance': distance.km,
                    'snr': snr
                })
        
        # Sắp xếp danh sách theo SNR giảm dần để tiện xử lý
        step_data.sort(key=lambda x: x['snr'], reverse=True)
        return step_data
