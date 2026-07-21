import os
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone, timedelta

# 1. Define Bounding Box & Grid Size
MIN_LON = 105.257254
MAX_LON = 105.264640
MIN_LAT = -2.806480
MAX_LAT = -2.797323
GRID_SIZE = 10 # 10x10 grid = 100 points

OUTPUT_DIR = "gridded_met_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Generate Grid
lons = np.linspace(MIN_LON, MAX_LON, GRID_SIZE)
lats = np.linspace(MIN_LAT, MAX_LAT, GRID_SIZE)

today = datetime.now(timezone.utc).date()
yesterday = today - timedelta(days=1)
start_history = "2021-01-01"

print("Generating 10x10 grid over Bounding Box...")
count = 1
for i, lon in enumerate(lons):
    for j, lat in enumerate(lats):
        file_name = os.path.join(OUTPUT_DIR, f"Point_{j}_{i}.met")
        print(f"Processing point {count}/100: Lat {lat:.5f}, Lon {lon:.5f} -> {file_name}")
        
        try:
            # History
            url_history = "https://archive-api.open-meteo.com/v1/archive"
            params_history = {
                "latitude": lat, "longitude": lon,
                "start_date": start_history, "end_date": yesterday.strftime("%Y-%m-%d"),
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,shortwave_radiation_sum",
                "timezone": "UTC"
            }
            res_hist = requests.get(url_history, params=params_history)
            res_hist.raise_for_status()
            data_hist = res_hist.json()
            
            df_hist = pd.DataFrame({
                "date": pd.to_datetime(data_hist["daily"]["time"]),
                "maxt": data_hist["daily"]["temperature_2m_max"],
                "mint": data_hist["daily"]["temperature_2m_min"],
                "rain": data_hist["daily"]["precipitation_sum"],
                "radn": data_hist["daily"]["shortwave_radiation_sum"] 
            })

            # Forecast
            url_forecast = "https://api.open-meteo.com/v1/forecast"
            params_forecast = {
                "latitude": lat, "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,shortwave_radiation_sum",
                "timezone": "UTC",
                "forecast_days": 16
            }
            res_cast = requests.get(url_forecast, params=params_forecast)
            res_cast.raise_for_status()
            data_cast = res_cast.json()
            
            df_cast = pd.DataFrame({
                "date": pd.to_datetime(data_cast["daily"]["time"]),
                "maxt": data_cast["daily"]["temperature_2m_max"],
                "mint": data_cast["daily"]["temperature_2m_min"],
                "rain": data_cast["daily"]["precipitation_sum"],
                "radn": data_cast["daily"]["shortwave_radiation_sum"] 
            })

            # Stitch
            df_stitched = pd.concat([df_hist, df_cast]).drop_duplicates(subset=['date'], keep='first').reset_index(drop=True)
            df_stitched["year"] = df_stitched["date"].dt.year
            df_stitched["day"] = df_stitched["date"].dt.dayofyear
            df_stitched['tavg'] = (df_stitched['maxt'] + df_stitched['mint']) / 2
            tav = df_stitched['tavg'].mean()
            df_stitched['month'] = df_stitched["date"].dt.month
            monthly_avg_temp = df_stitched.groupby('month')['tavg'].mean()
            amp = monthly_avg_temp.max() - monthly_avg_temp.min()
            
            df_stitched = df_stitched[["year", "day", "radn", "maxt", "mint", "rain"]].dropna()

            # Write file
            with open(file_name, "w") as f:
                f.write("[weather.met.weather]\n")
                f.write("! Data: Open-Meteo Historical + 16-Day Forecast (Gridded)\n")
                f.write(f"latitude = {lat:.6f} (DECIMAL DEGREES)\n")
                f.write(f"longitude = {lon:.6f} (DECIMAL DEGREES)\n")
                f.write(f"tav = {tav:.2f} (oC)\namp = {amp:.2f} (oC)\n\n")
                f.write("year day radn maxt mint rain\n() () (MJ/m^2) (oC) (oC) (mm)\n")
                
                for _, row in df_stitched.iterrows():
                    f.write(f"{int(row['year'])} {int(row['day']):3d} {row['radn']:6.2f} {row['maxt']:6.2f} {row['mint']:6.2f} {row['rain']:6.2f}\n")
            
        except Exception as e:
            print(f"Failed to process point Lat {lat:.5f}, Lon {lon:.5f}: {e}")
            
        count += 1
        time.sleep(0.5) # Polite delay to avoid hitting strict rate limits

print(f"Completed! {count-1} points processed.")
