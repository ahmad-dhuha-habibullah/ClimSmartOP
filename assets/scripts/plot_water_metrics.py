import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

# Note: Adjust paths assuming script is run from ClimSmartOP root directory
DB_PATH = r"assets\south_sumatra_oilpalm_daily_forecast.db"
OUTPUT_PLOT = r"assets\water_metrics_timeseries.png"

def main():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database {DB_PATH} not found.")
        return

    print(f"Connecting to database {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    
    # Check if DailyOutput table exists
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='DailyOutput';")
    if not cursor.fetchone():
        print("Error: Table 'DailyOutput' not found in database.")
        conn.close()
        return

    print("Extracting data...")
    df = pd.read_sql_query("SELECT * FROM DailyOutput", conn)
    conn.close()

    # Determine date column
    date_col = 'Clock.Today'
    if date_col not in df.columns:
        print(f"Error: '{date_col}' not found in columns: {df.columns.tolist()}")
        return

    df['Date'] = pd.to_datetime(df[date_col])

    # Check for required columns
    required_cols = [
        'Soil.SoilWater.Eo',
        'OilPalm.EP',
        'OilPalm.UnderstoryEP',
        'Soil.SoilWater.Es',
        'Weather.Rain'
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"Error: Missing columns in DailyOutput: {missing}")
        return

    print("Calculating metrics...")
    # Water Requirement
    df['Water_Requirement'] = df['Soil.SoilWater.Eo']
    
    # Actual Water Use (AET)
    df['AET'] = df['OilPalm.EP'] + df['OilPalm.UnderstoryEP'] + df['Soil.SoilWater.Es']
    
    # Water Deficit
    df['Water_Deficit'] = df['Water_Requirement'] - df['AET']
    
    # Ensure deficit is not negative (due to minor model artifacts like night transpiration etc.)
    df['Water_Deficit'] = df['Water_Deficit'].clip(lower=0)

    print("Generating plot...")
    fig, ax1 = plt.subplots(figsize=(14, 7))

    # Plot Water Requirement and Deficit
    ax1.plot(df['Date'], df['Water_Requirement'], label='Water Requirement (Eo)', color='darkorange', linewidth=1.0)
    ax1.plot(df['Date'], df['Water_Deficit'], label='Water Deficit', color='red', linewidth=1.0, linestyle='--')
    
    # Fill the area for deficit to make it visually stand out
    ax1.fill_between(df['Date'], 0, df['Water_Deficit'], color='red', alpha=0.3)

    ax1.set_xlabel('Date')
    ax1.set_ylabel('Water / Evapotranspiration (mm/day)', color='black')
    ax1.tick_params(axis='y', labelcolor='black')
    
    # Give a bit of headroom to the primary Y axis
    max_et = df['Water_Requirement'].max()
    if pd.isna(max_et): max_et = 10
    ax1.set_ylim(0, max_et * 1.3)
    
    # Format x-axis dates
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    
    # Secondary axis for Rainfall
    ax2 = ax1.twinx()
    ax2.bar(df['Date'], df['Weather.Rain'], width=1.0, color='blue', alpha=0.5, label='Rainfall')
    ax2.set_ylabel('Rainfall (mm/day)', color='blue')
    ax2.tick_params(axis='y', labelcolor='blue')
    
    # Invert the rainfall axis (put bars at the top)
    max_rain = df['Weather.Rain'].max()
    if pd.isna(max_rain): max_rain = 50
    # Set y-limit so bars only take up the top 30-40% of the graph
    ax2.set_ylim(max_rain * 3, 0)
    
    # Combine legends
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center left')

    plt.title('Daily Oil Palm Water Requirement, Deficit, and Rainfall (South Sumatra Forecast)')
    fig.tight_layout()

    plt.savefig(OUTPUT_PLOT, dpi=300)
    print(f"Success! Plot saved to {OUTPUT_PLOT}")

    # --- Plot Correlations ---
    print("Generating correlation plot...")
    import seaborn as sns
    corr_df = df[['Weather.Rain', 'Water_Requirement', 'AET', 'Water_Deficit']].copy()
    corr_df.rename(columns={'Weather.Rain': 'Rainfall'}, inplace=True)
    corr_matrix = corr_df.corr()

    fig2, ax_corr = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, center=0, ax=ax_corr, fmt=".2f")
    plt.title('Correlation Matrix of Water Metrics')
    fig2.tight_layout()
    
    CORR_PLOT = r"assets\water_metrics_correlations.png"
    plt.savefig(CORR_PLOT, dpi=300)
    print(f"Success! Correlation plot saved to {CORR_PLOT}")

    # --- PROOF OF SOIL MEMORY (TIME LAG & THRESHOLDS) ---
    print("Generating proof of soil memory...")
    # 1. Calculate accumulated rainfall over the past 30 days
    df['Rain_30d_Sum'] = df['Weather.Rain'].rolling(window=30, min_periods=1).sum()
    
    # 2. Calculate new correlations
    corr_daily = df['Water_Deficit'].corr(df['Weather.Rain'])
    corr_30d = df['Water_Deficit'].corr(df['Rain_30d_Sum'])
    
    # 3. Create a scatter plot to show the non-linear threshold effect
    fig3, ax3 = plt.subplots(figsize=(8, 6))
    ax3.scatter(df['Rain_30d_Sum'], df['Water_Deficit'], alpha=0.3, color='purple')
    ax3.set_xlabel('Accumulated Rainfall over Past 30 Days (mm)')
    ax3.set_ylabel('Daily Water Deficit (mm/day)')
    ax3.set_title(f'Proof of Soil Buffering (Threshold Effect)\nDaily Rain Corr: {corr_daily:.2f} | 30-Day Rain Corr: {corr_30d:.2f}')
    
    PROOF_PLOT = r"assets\soil_memory_proof.png"
    fig3.tight_layout()
    plt.savefig(PROOF_PLOT, dpi=300)
    print(f"Success! Proof plot saved to {PROOF_PLOT}")

if __name__ == '__main__':
    main()
