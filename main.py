# main.py

import numpy as np
from skyfield.api import load, EarthSatellite, Topos
from datetime import timedelta

# --- Configuration ---
TLE_FILE = 'starlink.tle'
GROUND_STATION_LAT = 16.0544  # Da Nang, Vietnam
GROUND_STATION_LON = 108.2022
MIN_ELEVATION_DEG = 25.0

def setup_simulation_environment():
    """Tải các dữ liệu cần thiết cho skyfield."""
    print("Setting up simulation environment...")
    ts = load.timescale()
    eph = load('de421.bsp')
    earth = eph['earth']
    satellites = load.tle_file(TLE_FILE)
    print(f"Loaded {len(satellites)} satellites from {TLE_FILE}.")
    return ts, earth, satellites

def get_visible_satellites(ts, earth, satellites, ground_station, current_time):
    """Tìm các vệ tinh nhìn thấy được từ một trạm mặt đất tại một thời điểm."""
    visible_sats = []
    for sat in satellites:
        difference = sat - ground_station
        topocentric = difference.at(current_time)
        alt, az, distance = topocentric.altaz()
        
        if alt.degrees > MIN_ELEVATION_DEG:
            visible_sats.append({
                'sat': sat,
                'name': sat.name,
                'elevation': alt.degrees,
                'azimuth': az.degrees,
                'distance': distance.km
            })
    return visible_sats

if __name__ == '__main__':
    # 1. Thiết lập môi trường
    timescale, earth, all_sats = setup_simulation_environment()
    
    # 2. Định nghĩa trạm mặt đất (UE)
    ue_location = Topos(latitude_degrees=GROUND_STATION_LAT, longitude_degrees=GROUND_STATION_LON)

    # 3. Lấy thời gian hiện tại để kiểm tra
    start_time = timescale.now()
    
    print(f"\n--- Checking visibility at {start_time.utc_strftime('%Y-%m-%d %H:%M:%S UTC')} ---")

    # 4. Tìm các vệ tinh nhìn thấy được tại thời điểm hiện tại
    visible_now = get_visible_satellites(timescale, earth, all_sats, ue_location, start_time)
    
    if visible_now:
        print(f"Found {len(visible_now)} visible satellites (elevation > {MIN_ELEVATION_DEG}°):")
        for sat_info in visible_now:
            print(f"  - {sat_info['name']}: Elevation = {sat_info['elevation']:.2f}°, Distance = {sat_info['distance']:.2f} km")
    else:
        print(f"No satellites visible above {MIN_ELEVATION_DEG}° at this time.")

    # 5. Kiểm tra 10 phút sau
    future_time = timescale.from_datetime(start_time.utc_datetime() + timedelta(minutes=10))
    print(f"\n--- Checking visibility at {future_time.utc_strftime('%Y-%m-%d %H:%M:%S UTC')} ---")

    visible_future = get_visible_satellites(timescale, earth, all_sats, ue_location, future_time)
    
    if visible_future:
        print(f"Found {len(visible_future)} visible satellites (elevation > {MIN_ELEVATION_DEG}°):")
        for sat_info in visible_future:
            print(f"  - {sat_info['name']}: Elevation = {sat_info['elevation']:.2f}°, Distance = {sat_info['distance']:.2f} km")
    else:
        print(f"No satellites visible above {MIN_ELEVATION_DEG}° at this time.")
