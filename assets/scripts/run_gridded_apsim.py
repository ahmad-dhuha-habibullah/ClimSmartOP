import os
import glob
import json
import sqlite3
import pandas as pd
import subprocess
import shutil

APSIM_EXE = r"C:\Program Files\APSIM2026.4.8030.0\bin\Models.exe"
BASE_APSIMX = r"assets\south_sumatra_oilpalm_daily_forecast.apsimx"
MET_DIR = r"gridded_met_files"
GEOJSON_OUT = r"assets\water_metrics_grid.geojson"

# Grid size for drawing the polygons (half the step size)
# Based on the 10x10 grid in the fetcher script: step is roughly 0.0009 degrees
HALF_STEP = 0.00045 

def create_polygon(lat, lon):
    return [
        [lon - HALF_STEP, lat - HALF_STEP],
        [lon + HALF_STEP, lat - HALF_STEP],
        [lon + HALF_STEP, lat + HALF_STEP],
        [lon - HALF_STEP, lat + HALF_STEP],
        [lon - HALF_STEP, lat - HALF_STEP] # close
    ]

def main():
    if not os.path.exists(MET_DIR):
        print(f"Error: {MET_DIR} not found. Please run the fetcher first to get .met files.")
        return

    met_files = glob.glob(os.path.join(MET_DIR, "*.met"))
    if not met_files:
        print("No .met files found.")
        return

    features = []
    
    # Read base APSIMX content
    with open(BASE_APSIMX, 'r', encoding='utf-8') as f:
        base_apsimx_str = f.read()
        apsimx_base_dict = json.loads(base_apsimx_str)

    # Function to deeply search and replace the weather file
    def replace_weather(node, new_met):
        if isinstance(node, dict):
            if node.get("$type") == "Models.Climate.Weather, Models":
                node["FileName"] = os.path.abspath(new_met)
            for v in node.values():
                replace_weather(v, new_met)
        elif isinstance(node, list):
            for item in node:
                replace_weather(item, new_met)

    print(f"Starting APSIM batch run for {len(met_files)} files...")

    for idx, met_path in enumerate(met_files):
        print(f"Processing {idx+1}/{len(met_files)}: {met_path}")
        
        # 1. Parse Lat/Lon from met file
        lat, lon = 0.0, 0.0
        with open(met_path, 'r') as f:
            for line in f:
                if line.startswith("latitude"):
                    lat = float(line.split("=")[1].split("(")[0].strip())
                if line.startswith("longitude"):
                    lon = float(line.split("=")[1].split("(")[0].strip())
                    break
        
        # 2. Create Temp APSIMX
        temp_apsimx = f"temp_run_{idx}.apsimx"
        temp_db = f"temp_run_{idx}.db"
        
        # Deep copy the dict and replace weather
        import copy
        apsimx_dict = copy.deepcopy(apsimx_base_dict)
        replace_weather(apsimx_dict, met_path)
        
        with open(temp_apsimx, 'w', encoding='utf-8') as f:
            json.dump(apsimx_dict, f)
            
        # 3. Run APSIM
        subprocess.run([APSIM_EXE, temp_apsimx], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 4. Read DB
        if not os.path.exists(temp_db):
            print(f"  -> Failed to run APSIM for {met_path}")
            if os.path.exists(temp_apsimx): os.remove(temp_apsimx)
            continue
            
        conn = sqlite3.connect(temp_db)
        df = pd.read_sql_query("SELECT * FROM DailyOutput", conn)
        conn.close()
        
        # Extract the last 60 days (to have some history + 16d forecast)
        df['Date'] = pd.to_datetime(df['Clock.Today'])
        df = df.tail(60).copy() 
        
        df['Water_Requirement'] = df['Soil.SoilWater.Eo']
        df['AET'] = df['OilPalm.EP'] + df['OilPalm.UnderstoryEP'] + df['Soil.SoilWater.Es']
        df['Water_Deficit'] = (df['Water_Requirement'] - df['AET']).clip(lower=0)
        
        # Convert to lists for JSON
        dates = df['Date'].dt.strftime('%Y-%m-%d').tolist()
        deficits = [round(x, 2) for x in df['Water_Deficit'].tolist()]
        requirements = [round(x, 2) for x in df['Water_Requirement'].tolist()]
        
        # Create GeoJSON Feature
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [create_polygon(lat, lon)]
            },
            "properties": {
                "id": idx,
                "lat": lat,
                "lon": lon,
                "dates": dates,
                "deficit": deficits,
                "requirement": requirements
            }
        }
        features.append(feature)
        
        # Cleanup temp files
        os.remove(temp_apsimx)
        os.remove(temp_db)

    # Save GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(GEOJSON_OUT, 'w', encoding='utf-8') as f:
        json.dump(geojson, f)
        
    print(f"\nSuccessfully created {GEOJSON_OUT} with {len(features)} spatial features.")
    print("This file is ready to be loaded into the web map or converted to PMTiles.")

if __name__ == "__main__":
    main()
