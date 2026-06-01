import os
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta

# 1. Define Coordinates and File Name
centroid_lat, centroid_lon = -2.792159, 104.600073
file_name = "South_Sumatra_Seasonal_Forecast.met"

# Automatically determine dates (using timezone-aware UTC)
today = datetime.now(timezone.utc).date()
yesterday = today - timedelta(days=1)
end_forecast = "2026-12-31"

# --- STEP 0: INCREMENTAL UPDATE LOGIC ---
df_existing_solid = pd.DataFrame()
start_history = "2021-01-01" # Default start if no file exists

if os.path.exists(file_name):
    print(f"Found existing '{file_name}'. Parsing previous data...")
    try:
        with open(file_name, 'r') as f:
            lines = f.readlines()
        
        # Find where the data actually starts
        data_start = 0
        for i, line in enumerate(lines):
            if line.startswith("year day"):
                data_start = i + 2
                break
        
        if data_start > 0:
            # Read the existing .met file into Pandas
            df_existing = pd.read_csv(file_name, skiprows=data_start, sep=r'\s+', header=None, names=["year", "day", "radn", "maxt", "mint", "rain"])
            df_existing['date'] = pd.to_datetime(df_existing['year'].astype(str) + df_existing['day'].astype(str), format='%Y%j')
            
            # Keep history up to 5 days ago. This drops the old forecast and any recent, un-finalized history.
            solid_end_date = yesterday - timedelta(days=5)
            df_existing_solid = df_existing[df_existing['date'] <= pd.to_datetime(solid_end_date)].copy()
            
            if not df_existing_solid.empty:
                # Update the API start date to only fetch the missing recent gap
                start_history = (solid_end_date + timedelta(days=1)).strftime("%Y-%m-%d")
                print(f"Successfully loaded history. Incrementally updating from {start_history}...")
    except Exception as e:
        print(f"Could not parse existing file cleanly. Defaulting to full download: {e}")
        df_existing_solid = pd.DataFrame()
        start_history = "2021-01-01"
else:
    print(f"No existing file found. Downloading full history from {start_history}...")

print("Stitching Data: History -> 16-Day Forecast -> Seasonal Forecast")

# --- STEP 1: FETCH HISTORICAL DATA (Only the missing gap if incremental) ---
url_history = "https://archive-api.open-meteo.com/v1/archive"
params_history = {
    "latitude": centroid_lat, "longitude": centroid_lon,
    "start_date": start_history, "end_date": yesterday.strftime("%Y-%m-%d"),
    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,shortwave_radiation_sum",
    "timezone": "UTC"
}
data_hist = requests.get(url_history, params=params_history).json()
df_hist = pd.DataFrame({
    "date": pd.to_datetime(data_hist["daily"]["time"]),
    "maxt": data_hist["daily"]["temperature_2m_max"],
    "mint": data_hist["daily"]["temperature_2m_min"],
    "rain": data_hist["daily"]["precipitation_sum"],
    "radn": data_hist["daily"]["shortwave_radiation_sum"] 
})

# Combine existing solid history with the newly fetched historical gap
df_hist_full = pd.concat([df_existing_solid, df_hist]).drop_duplicates(subset=['date'], keep='last').reset_index(drop=True)

# --- STEP 2: FETCH SHORT-TERM FORECAST (Next 16 days) ---
url_forecast = "https://api.open-meteo.com/v1/forecast"
params_forecast = {
    "latitude": centroid_lat, "longitude": centroid_lon,
    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,shortwave_radiation_sum",
    "timezone": "UTC",
    "forecast_days": 16
}
data_cast = requests.get(url_forecast, params=params_forecast).json()
df_cast = pd.DataFrame({
    "date": pd.to_datetime(data_cast["daily"]["time"]),
    "maxt": data_cast["daily"]["temperature_2m_max"],
    "mint": data_cast["daily"]["temperature_2m_min"],
    "rain": data_cast["daily"]["precipitation_sum"],
    "radn": data_cast["daily"]["shortwave_radiation_sum"] 
})

# --- STEP 3: FETCH LONG-TERM SEASONAL FORECAST (Up to Dec 31) ---
url_seasonal = "https://seasonal-api.open-meteo.com/v1/seasonal"
params_seasonal = {
    "latitude": centroid_lat, "longitude": centroid_lon,
    "start_date": today.strftime("%Y-%m-%d"), 
    "end_date": end_forecast,
    "models": "ecmwf_ifs", 
    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,shortwave_radiation_sum",
    "timezone": "UTC"
}
data_seas = requests.get(url_seasonal, params=params_seasonal).json()

if "error" in data_seas:
    raise ValueError(f"Open-Meteo API Error: {data_seas.get('reason')}")

df_clim_raw = pd.DataFrame(data_seas["daily"])

maxt_cols = [c for c in df_clim_raw.columns if "temperature_2m_max" in c]
mint_cols = [c for c in df_clim_raw.columns if "temperature_2m_min" in c]
rain_cols = [c for c in df_clim_raw.columns if "precipitation_sum" in c]
radn_cols = [c for c in df_clim_raw.columns if "shortwave_radiation_sum" in c]

df_clim = pd.DataFrame({
    "date": pd.to_datetime(df_clim_raw["time"]),
    "maxt": df_clim_raw[maxt_cols].mean(axis=1) if maxt_cols else pd.Series(dtype=float),
    "mint": df_clim_raw[mint_cols].mean(axis=1) if mint_cols else pd.Series(dtype=float),
    "rain": df_clim_raw[rain_cols].mean(axis=1) if rain_cols else pd.Series(dtype=float),
    "radn": df_clim_raw[radn_cols].mean(axis=1) if radn_cols else pd.Series(dtype=float)
})

# --- STEP 4: STITCH THEM ALL TOGETHER ---
for col in ['maxt', 'mint', 'rain', 'radn']:
    if col not in df_clim.columns:
        df_clim[col] = float('nan')

# Concatenate: Full History -> Short-term -> Climate. 
df_stitched = pd.concat([df_hist_full, df_cast, df_clim]).drop_duplicates(subset=['date'], keep='first').reset_index(drop=True)

df_stitched["year"] = df_stitched["date"].dt.year
df_stitched["day"] = df_stitched["date"].dt.dayofyear

# --- FILL MISSING SEASONAL RADIATION WITH DOY AVERAGES ---
print("Patching missing seasonal variables with Historical Climatology...")
df_hist_full['day'] = df_hist_full['date'].dt.dayofyear
historical_doy_means = df_hist_full.groupby('day')[['maxt', 'mint', 'rain', 'radn']].mean()

for col in ['maxt', 'mint', 'rain', 'radn']:
    if df_stitched[col].isna().any():
        df_stitched[col] = df_stitched.apply(
            lambda row: historical_doy_means.loc[row['day'], col] if pd.isna(row[col]) else row[col],
            axis=1
        )

# Calculate tav and amp for APSIM based on the total compiled dataset
df_stitched['tavg'] = (df_stitched['maxt'] + df_stitched['mint']) / 2
tav = df_stitched['tavg'].mean()
df_stitched['month'] = df_stitched["date"].dt.month
monthly_avg_temp = df_stitched.groupby('month')['tavg'].mean()
amp = monthly_avg_temp.max() - monthly_avg_temp.min()

df_stitched = df_stitched[["year", "day", "radn", "maxt", "mint", "rain"]].dropna()

# --- STEP 5: WRITE THE MET FILE ---
with open(file_name, "w") as f:
    f.write("[weather.met.weather]\n")
    f.write("! Data: Open-Meteo Historical + 16-Day + Seasonal Forecast (Incrementally Updated)\n")
    f.write(f"latitude = {centroid_lat:.6f} (DECIMAL DEGREES)\n")
    f.write(f"longitude = {centroid_lon:.6f} (DECIMAL DEGREES)\n")
    f.write(f"tav = {tav:.2f} (oC)\namp = {amp:.2f} (oC)\n\n")
    f.write("year day radn maxt mint rain\n() () (MJ/m^2) (oC) (oC) (mm)\n")
    
    for index, row in df_stitched.iterrows():
        f.write(f"{int(row['year'])} {int(row['day']):3d} {row['radn']:6.2f} {row['maxt']:6.2f} {row['mint']:6.2f} {row['rain']:6.2f}\n")

print(f"Pipeline complete! Overwrote {file_name} with freshest forecast data.")
