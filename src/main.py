import os
import requests
import pandas as pd
from datetime import datetime

CITIES = {
    "Manila": {"lat": 14.5995, "lon": 120.9842},
    "Cebu City": {"lat": 10.3157, "lon": 123.8854},
    "Davao City": {"lat": 7.1963, "lon": 125.4618},
    "Baguio": {"lat": 16.4023, "lon": 120.5960}
}

csv_path = "data/weather_history.csv"
today_str = datetime.utcnow().strftime("%Y-%m-%d")

new_rows = []
for city, coords in CITIES.items():
    url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&daily=temperature_2m_max,temperature_2m_min&timezone=Asia%2FManila"
    try:
        response = requests.get(url).json()
        max_temp = response["daily"]["temperature_2m_max"][0]
        min_temp = response["daily"]["temperature_2m_min"][0]
        avg_temp = (max_temp + min_temp) / 2
        
        new_rows.append({
            "date": today_str,
            "city": city,
            "avg_temp": round(avg_temp, 2),
            "is_anomaly": False
        })
    except Exception as e:
        print(f"Error fetching data for {city}: {e}")

df_new = pd.DataFrame(new_rows)

if os.path.exists(csv_path) and os.path.getsize(csv_path) > 10:

    df_historical = pd.read_csv(csv_path)
    df_historical = df_historical[df_historical["date"] != today_str]
    df_combined = pd.concat([df_historical, df_new], ignore_index=True)
    
    for city in CITIES.keys():
        city_data = df_combined[df_combined["city"] == city]
        if len(city_data) >= 3:
            mean = city_data["avg_temp"].mean()
            std = city_data["avg_temp"].std()
            
            today_idx = df_combined[(df_combined["city"] == city) & (df_combined["date"] == today_str)].index
            if not today_idx.empty:
                today_temp = df_combined.loc[today_idx, "avg_temp"].values[0]
                if std > 0 and abs(today_temp - mean) > (1.5 * std):
                    df_combined.loc[today_idx, "is_anomaly"] = True
else:
    df_combined = df_new

df_combined.to_csv(csv_path, index=False)

with open("README.md", "w", encoding="utf-8") as f:
    f.write("# 🇵🇭 Philippine Weather Anomaly Tracker\n\n")
    f.write("This data science pipeline runs **completely free** every single day via GitHub Actions. It ingests local city climate measurements, tracks moving baselines, and flags statistical temperature anomalies.\n\n")
    f.write(f"### 🕒 Last Pipeline Run: `{today_str} PHT`\n\n")
    f.write("| Philippine City | Today's Calculated Mean Temp | Anomaly Flag |\n")
    f.write("| :--- | :---: | :---: |\n")
    
    latest_updates = df_combined[df_combined["date"] == today_str]
    for _, row in latest_updates.iterrows():
        status = "🚨 **YES (Outlier)**" if row["is_anomaly"] else "✅ Normal"
        f.write(f"| {row['city']} | {row['avg_temp']}°C | {status} |\n")
        
print("Pipeline run successfully completed locally!")