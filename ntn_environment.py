# ntn_environment.py

import numpy as np
from skyfield.api import load, Topos
import math

class RainCell:
    """Mô phỏng một vùng nhiễu loạn khí quyển di động."""
    def __init__(self, start_az, start_el, radius, penalty_db, speed_az_per_sec):
        self.az = start_az
        self.el = start_el
        self.radius = radius
        self.penalty_db = penalty_db
        self.speed = speed_az_per_sec

    def update_position(self, time_step_sec):
        self.az = (self.az + self.speed * time_step_sec) % 360

    def get_attenuation(self, sat_az, sat_el):
        delta_az = abs(sat_az - self.az)
        if delta_az > 180: delta_az = 360 - delta_az
        
        # Công thức tính khoảng cách góc trên mặt cầu (Haversine-like, đơn giản hóa)
        angular_distance = math.sqrt((delta_az * math.cos(math.radians((sat_el + self.el)/2)))**2 + (sat_el - self.el)**2)
        
        if angular_distance < self.radius:
            return self.penalty_db
        return 0

class NTNEnvironment:
    def __init__(self, tle_file, min_elevation_deg=25.0):
        print("Initializing NTN Environment with DYNAMIC ATTENUATION...")
        self.ts = load.timescale()
        self.eph = load('de421.bsp')
        self.satellites = load.tle_file(tle_file)
        self.min_elevation_deg = min_elevation_deg
        
        # Tham số kênh truyền
        self.satellite_eirp = 45
        self.ue_gt = 1
        self.frequency_hz = 12e9
        self.boltzmann_k = -228.6
        
        # Khởi tạo các vùng nhiễu
        self.rain_cells = [
            RainCell(start_az=45, start_el=40, radius=15, penalty_db=-12.0, speed_az_per_sec=0.5),
            RainCell(start_az=200, start_el=50, radius=10, penalty_db=-8.0, speed_az_per_sec=-0.3)
        ]

    def update_rain_cells(self, time_step_sec):
        for cell in self.rain_cells:
            cell.update_position(time_step_sec)
    
    def get_ue_location(self, base_lat, base_lon, time_step_sec, velocity_kmh):
        deg_per_km = 1 / (111.32 * np.cos(np.deg2rad(base_lat)))
        velocity_deg_per_sec = (velocity_kmh / 3600) * deg_per_km
        new_lon = base_lon + time_step_sec * velocity_deg_per_sec
        return Topos(latitude_degrees=base_lat, longitude_degrees=new_lon)

    def calculate_snr(self, distance_km, sat_az, sat_el):
        fspl_db = 20 * np.log10(distance_km * 1000) + 20 * np.log10(self.frequency_hz) - 147.55
        received_power_dbw = self.satellite_eirp - fspl_db + self.ue_gt
        bandwidth_dbhz = 10 * np.log10(20e6)
        noise_power_dbw = self.boltzmann_k + bandwidth_dbhz
        snr_db = received_power_dbw - noise_power_dbw
        
        # Áp dụng suy hao từ các vùng nhiễu
        for cell in self.rain_cells:
            snr_db += cell.get_attenuation(sat_az, sat_el)
            
        snr_db += np.random.normal(0, 0.5)
        return snr_db

    def get_simulation_step_data(self, ue_location, current_time):
        step_data = []
        for sat in self.satellites:
            difference = sat - ue_location
            topocentric = difference.at(current_time)
            alt, az, distance = topocentric.altaz()
            
            if alt.degrees > self.min_elevation_deg:
                snr = self.calculate_snr(distance.km, az.degrees, alt.degrees)
                step_data.append({'sat_obj': sat, 'name': sat.name, 'elevation': alt.degrees, 'distance': distance.km, 'snr': snr, 'azimuth': az.degrees})
        
        step_data.sort(key=lambda x: x['snr'], reverse=True)
        return step_data
