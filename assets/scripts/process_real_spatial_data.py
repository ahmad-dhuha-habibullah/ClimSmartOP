import os
import json
import datetime
import calendar
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import xarray as xr
import requests

KML_FILE = "Sawit.kml"
NC_FILE = os.path.join("assets", "historical.nc")
GEOJSON_OUT = os.path.join("assets", "water_metrics_grid.geojson")
GRID_STEP = 0.02  # ~2km resolution

def point_in_polygon(x, y, poly):
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def main():
    print("1. Reading KML polygon...")
    tree = ET.parse(KML_FILE)
    root = tree.getroot()
    # Find coordinates tag
    coords_text = ""
    for elem in root.iter():
        if 'coordinates' in elem.tag:
            coords_text = elem.text.strip()
            break
            
    if not coords_text:
        print("Error: Could not find coordinates in KML.")
        return
        
    poly_pts = []
    for pt_str in coords_text.split():
        if pt_str:
            parts = pt_str.split(',')
            poly_pts.append((float(parts[0]), float(parts[1])))
            
    minx = min([p[0] for p in poly_pts])
    maxx = max([p[0] for p in poly_pts])
    miny = min([p[1] for p in poly_pts])
    maxy = max([p[1] for p in poly_pts])
    
    # Simple centroid
    centroid_x = sum([p[0] for p in poly_pts]) / len(poly_pts)
    centroid_y = sum([p[1] for p in poly_pts]) / len(poly_pts)
    
    print(f"   Bounds: {minx:.4f}, {miny:.4f} to {maxx:.4f}, {maxy:.4f}")
    print(f"   Centroid: {centroid_x:.4f}, {centroid_y:.4f}")

    print("2. Fetching Open-Meteo Seasonal Forecast (July - Dec 2026)...")
    url = f"https://seasonal-api.open-meteo.com/v1/seasonal?latitude={centroid_y}&longitude={centroid_x}&start_date=2026-07-01&end_date=2026-12-31&daily=precipitation_sum,et0_fao_evapotranspiration_sum"
    r = requests.get(url)
    if r.status_code != 200:
        print("Error fetching Open-Meteo data:", r.text)
        return
        
    fc_data = r.json()
    fc_dates = pd.to_datetime(fc_data['daily']['time'])
    fc_precip = np.array(fc_data['daily']['precipitation_sum'])
    fc_pet = np.array(fc_data['daily']['et0_fao_evapotranspiration_sum'])
    
    # Fill NAs if any (e.g. et0 sometimes has missing days in some APIs)
    fc_precip = np.nan_to_num(fc_precip, nan=0.0)
    fc_pet = np.nan_to_num(fc_pet, nan=np.nanmean(fc_pet))
    
    df_fc = pd.DataFrame({
        'date': fc_dates,
        'precip': fc_precip,
        'pet': fc_pet
    })
    # Aggregate to monthly
    df_fc.set_index('date', inplace=True)
    df_fc_monthly = df_fc.resample('ME').sum()
    df_fc_monthly['deficit'] = (df_fc_monthly['pet'] - df_fc_monthly['precip']).clip(lower=0)
    
    forecast_dates_str = df_fc_monthly.index.strftime('%Y-%m').tolist()
    forecast_deficit = df_fc_monthly['deficit'].tolist()
    forecast_requirement = df_fc_monthly['pet'].tolist()
    
    print(f"   Fetched {len(forecast_dates_str)} months of forecast data.")

    print("3. Processing Historical NetCDF...")
    ds = xr.open_dataset(NC_FILE)
    
    # Create high-res grid over the bounding box
    lons = np.arange(minx, maxx + GRID_STEP, GRID_STEP)
    lats = np.arange(miny, maxy + GRID_STEP, GRID_STEP)
    print(f"   Generating {len(lons)}x{len(lats)} grid (Nearest Neighbor matching)...")
    
    hist_dates = pd.to_datetime(ds.valid_time.values)
    days_in_month = hist_dates.days_in_month.values
    
    features = []
    pid = 0
    
    print("4. Generating spatial features...")
    # Iterate through the grid
    for lat in lats:
        for lon in lons:
            # Check if point is inside KML polygon
            if not point_in_polygon(lon, lat, poly_pts):
                continue
                
            # Extract time series for this pixel (nearest neighbor)
            pixel_data = ds.sel(latitude=lat, longitude=lon, method="nearest")
            
            # ERA5 tp/pev are often monthly means of daily accumulations in m/day
            # So multiply by 1000 to get mm/day, then by days_in_month to get mm/month
            pixel_tp_m = pixel_data['tp'].values
            pixel_pev_m = pixel_data['pev'].values
            
            # Handle potential NaNs in the interpolated sea pixels
            if np.isnan(pixel_tp_m).all():
                continue
                
            pixel_precip_mm = np.nan_to_num(pixel_tp_m, nan=0.0) * 1000 * days_in_month
            pixel_pet_mm = np.abs(np.nan_to_num(pixel_pev_m, nan=0.0)) * 1000 * days_in_month
            pixel_deficit = np.clip(pixel_pet_mm - pixel_precip_mm, 0, None)
            
            # Combine Historical + Forecast
            full_dates = hist_dates.strftime('%Y-%m').tolist() + forecast_dates_str
            full_deficit = [round(float(x), 2) for x in pixel_deficit] + [round(float(x), 2) for x in forecast_deficit]
            full_req = [round(float(x), 2) for x in pixel_pet_mm] + [round(float(x), 2) for x in forecast_requirement]
            
            poly_geom = [
                [lon - GRID_STEP/2, lat - GRID_STEP/2],
                [lon + GRID_STEP/2, lat - GRID_STEP/2],
                [lon + GRID_STEP/2, lat + GRID_STEP/2],
                [lon - GRID_STEP/2, lat + GRID_STEP/2],
                [lon - GRID_STEP/2, lat - GRID_STEP/2]
            ]
            
            props = {
                "id": pid,
                "lat": round(lat, 5),
                "lon": round(lon, 5),
                "dates": json.dumps(full_dates)
            }
            for i, val in enumerate(full_deficit):
                props[f"def_{i}"] = val
            for i, val in enumerate(full_req):
                props[f"req_{i}"] = val

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [poly_geom]
                },
                "properties": props
            })
            pid += 1

    print(f"5. Saving GeoJSON with {len(features)} valid plantation pixels...")
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(GEOJSON_OUT, 'w', encoding='utf-8') as f:
        json.dump(geojson, f)
        
    print(f"Success! Saved to {GEOJSON_OUT}")

if __name__ == "__main__":
    main()
