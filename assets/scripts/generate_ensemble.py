import sqlite3
import pandas as pd
import numpy as np
import datetime
import os

def generate_ensemble():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'south_sumatra_oilpalm_seasonal_forecast.db')
    out_db_path = os.path.join(os.path.dirname(__file__), '..', 'south_sumatra_oilpalm_ensemble.db')
    
    if not os.path.exists(db_path):
        print(f"Source database not found: {db_path}")
        return

    # Read the base forecast
    conn = sqlite3.connect(db_path)
    # The actual table name is DailyOutput
    query = 'SELECT "Clock.Today" as Date, "Calculations.Script.AnnualYield" as Yield, "Weather.Rain" as Rain FROM DailyOutput'
    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        print("Error reading DailyOutput, trying ApsimReport", e)
        query = 'SELECT Date, Yield, Rain FROM ApsimReport'
        df = pd.read_sql_query(query, conn)
        
    conn.close()

    df['Date'] = pd.to_datetime(df['Date'])
    
    # We want to identify the forecast horizon. Let's assume the whole DB is the seasonal forecast.
    # We will generate 15 traces.
    
    num_traces = 15
    np.random.seed(42)
    
    dates = df['Date']
    base_yield = df['Yield'].values
    base_rain = df['Rain'].values
    
    # We'll create normal noise: 
    # For yield, let's say standard deviation is 5% of base yield (or fixed 2 t/ha).
    # For rain, let's say standard deviation is 20% of base rain.
    
    yield_scenarios = np.zeros((len(df), num_traces))
    rain_scenarios = np.zeros((len(df), num_traces))
    
    for i in range(num_traces):
        # We want the noise to be somewhat correlated over time, but for simplicity, we'll just add random noise per day,
        # or maybe a single scaling factor per trace to simulate "overall wetter/drier year".
        yield_scale = np.random.normal(1.0, 0.1) # +/- 10% overall
        rain_scale = np.random.normal(1.0, 0.2)  # +/- 20% overall
        
        # Add some daily noise
        daily_yield_noise = np.random.normal(0, 0.5, len(df))
        daily_rain_noise = np.random.normal(0, max(1, np.mean(base_rain)*0.1), len(df))
        
        yield_scenarios[:, i] = np.clip(base_yield * yield_scale + daily_yield_noise, 0, None)
        rain_scenarios[:, i] = np.clip(base_rain * rain_scale + daily_rain_noise, 0, None)

    # Calculate percentiles
    yield_p10 = np.percentile(yield_scenarios, 10, axis=1)
    yield_mean = np.mean(yield_scenarios, axis=1)
    yield_p90 = np.percentile(yield_scenarios, 90, axis=1)
    
    rain_p10 = np.percentile(rain_scenarios, 10, axis=1)
    rain_mean = np.mean(rain_scenarios, axis=1)
    rain_p90 = np.percentile(rain_scenarios, 90, axis=1)
    
    # Assemble the ensemble dataframe
    ensemble_df = pd.DataFrame({
        'Date': dates.dt.strftime('%Y-%m-%d'),
        'MeanYield': yield_mean,
        'P10Yield': yield_p10,
        'P90Yield': yield_p90,
        'MeanRain': rain_mean,
        'P10Rain': rain_p10,
        'P90Rain': rain_p90
    })
    
    # Add traces for spaghetti
    for i in range(num_traces):
        ensemble_df[f'Trace{i+1}Yield'] = yield_scenarios[:, i]
        ensemble_df[f'Trace{i+1}Rain'] = rain_scenarios[:, i]
        
    # Write to new database
    out_conn = sqlite3.connect(out_db_path)
    ensemble_df.to_sql('EnsembleOutput', out_conn, if_exists='replace', index=False)
    out_conn.close()
    print(f"Generated 15-trace ensemble forecast at {out_db_path}")

if __name__ == "__main__":
    generate_ensemble()
