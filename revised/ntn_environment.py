# ntn_environment.py

import numpy as np
from skyfield.api import load, Topos
import math
import os

class RainCell:
    """Mô phỏng vùng nhiễu loạn khí quyển di động."""
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
        angular_distance = math.sqrt((delta_az * math.cos(math.radians((sat_el + self.el)/2)))**2 + (sat_el - self.el)**2)
        if angular_distance < self.radius:
            return self.penalty_db
        return 0

class NTNEnvironment:
    def __init__(self, min_elevation_deg=25.0):
        print("Initializing NTN Environment with Mixed-Orbits (LEO+MEO) & Dynamic Attenuation...")
        self.ts = load.timescale()
        self.eph = load('de421.bsp')
        self.min_elevation_deg = min_elevation_deg
        
        # Tự động tải TLE nếu chưa có (Reviewer 1 yêu cầu LEO + MEO)
        starlink_url = 'https://celestrak.org/NORAD/elements/supplemental/sup-gp.php?FILE=starlink&FORMAT=tle'
        o3b_url = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=ses&FORMAT=tle' # MEO satellites
        
        self.satellites = load.tle_file(starlink_url, filename='starlink.tle')
        meo_sats = load.tle_file(o3b_url, filename='o3b.tle')
        
        # Chỉ lọc lấy vệ tinh O3b (MEO) từ file SES
        self.satellites += [sat for sat in meo_sats if 'O3B' in sat.name.upper()]
        
        print(f"Loaded {len(self.satellites)} satellites (Starlink LEO + O3b MEO).")

        self.satellite_eirp = 45
        self.ue_gt = 1
        self.frequency_hz = 12e9
        self.boltzmann_k = -228.6
        
        self.rain_cells = [
            RainCell(start_az=45, start_el=40, radius=15, penalty_db=-15.0, speed_az_per_sec=0.5),
            RainCell(start_az=200, start_el=50, radius=12, penalty_db=-10.0, speed_az_per_sec=-0.3)
        ]

    def update_rain_cells(self, time_step_sec):
        for cell in self.rain_cells:
            cell.update_position(time_step_sec)
    
    def get_ue_location(self, base_lat, base_lon, time_step_sec, velocity_kmh, heading_deg=90):
        # Tính toán di chuyển dựa trên vận tốc và hướng (Heading)
        deg_per_km_lat = 1 / 111.32
        deg_per_km_lon = 1 / (111.32 * np.cos(np.deg2rad(base_lat)))
        
        distance_km = (velocity_kmh / 3600) * time_step_sec
        new_lat = base_lat + (distance_km * math.cos(math.radians(heading_deg)) * deg_per_km_lat)
        new_lon = base_lon + (distance_km * math.sin(math.radians(heading_deg)) * deg_per_km_lon)
        
        return Topos(latitude_degrees=new_lat, longitude_degrees=new_lon)

    def calculate_snr(self, distance_km, sat_az, sat_el, sat_name):
        # MEO xa hơn LEO, suy hao đường truyền (FSPL) lớn hơn
        fspl_db = 20 * np.log10(distance_km * 1000) + 20 * np.log10(self.frequency_hz) - 147.55
        
        # Bù trừ EIRP cho MEO để công bằng (vệ tinh MEO thường phát công suất lớn hơn)
        eirp = self.satellite_eirp + 10 if 'O3B' in sat_name.upper() else self.satellite_eirp
        
        received_power_dbw = eirp - fspl_db + self.ue_gt
        bandwidth_dbhz = 10 * np.log10(20e6)
        noise_power_dbw = self.boltzmann_k + bandwidth_dbhz
        snr_db = received_power_dbw - noise_power_dbw
        
        for cell in self.rain_cells:
            snr_db += cell.get_attenuation(sat_az, sat_el)
            
        snr_db += np.random.normal(0, 0.5) # Nhiễu Gaussian
        return snr_db

    def get_simulation_step_data(self, ue_location, current_time):
        step_data = []
        for sat in self.satellites:
            difference = sat - ue_location
            topocentric = difference.at(current_time)
            alt, az, distance = topocentric.altaz()
            
            if alt.degrees > self.min_elevation_deg:
                snr = self.calculate_snr(distance.km, az.degrees, alt.degrees, sat.name)
                step_data.append({'name': sat.name, 'elevation': alt.degrees, 'distance': distance.km, 'snr': snr})
        
        step_data.sort(key=lambda x: x['snr'], reverse=True)
        # Tối ưu: Chỉ giữ lại top 10 vệ tinh tốt nhất để giảm tải ma trận QUBO
        return step_data[:10]
