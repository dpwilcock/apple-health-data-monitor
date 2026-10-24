import os
import psycopg2
import pandas as pd
from datetime import datetime, timedelta

SCHEMA = os.environ.get("PGSCHEMA", "DW Health")

conn = psycopg2.connect(dbname=os.environ.get("PGDATABASE", "postgres"))

# Date windows (set via env to your investigation periods)
# e.g. FATIGUE_START=2026-05-01 FATIGUE_END=2026-06-14
period_start = os.environ.get("FATIGUE_START", "2026-01-01")
period_end = os.environ.get("FATIGUE_END", "2026-12-31")

# 1. Check Data Completeness / Granularity
query_quality = f"""
SELECT 
    TO_CHAR(start_date AT TIME ZONE 'America/Vancouver', 'YYYY-MM') as month,
    EXTRACT(DAY FROM start_date AT TIME ZONE 'America/Vancouver') as day,
    type,
    COUNT(*) as record_count,
    SUM(value) as total_val,
    AVG(value) as avg_val
FROM "{SCHEMA}".health_records
WHERE start_date >= %s AND start_date < %s
GROUP BY 1, 2, 3
"""

df_all = pd.read_sql_query(query_quality, conn, params=[period_start, period_end])

# Split the period into two halves for comparison (first 2 weeks vs second 2 weeks)
all_dates = sorted(df_all['month'].unique())
first_half_mask = df_all['month'] == all_dates[0] if all_dates else pd.Series([False]*len(df_all))
second_half_mask = df_all['month'] == all_dates[-1] if all_dates else pd.Series([False]*len(df_all))

first_half = df_all[first_half_mask]
second_half = df_all[second_half_mask]

metrics = [
    'HKQuantityTypeIdentifierStepCount',
    'HKQuantityTypeIdentifierHeartRate',
    'HKQuantityTypeIdentifierRestingHeartRate',
    'HKCategoryTypeIdentifierSleepAnalysis',
    'HKQuantityTypeIdentifierHeartRateVariabilitySDNN'
]

print("=== DATA QUALITY & COMPLETENESS ===")
for m in metrics:
    fh_m = first_half[first_half['type'] == m]
    sh_m = second_half[second_half['type'] == m]
    
    fh_avg_records = fh_m['record_count'].mean() if not fh_m.empty else 0
    sh_avg_records = sh_m['record_count'].mean() if not sh_m.empty else 0
    print(f"{m}:")
    print(f"  {all_dates[0] if all_dates else 'first half'}: ~{fh_avg_records:.0f} records/day")
    print(f"  {all_dates[-1] if all_dates else 'second half'}: ~{sh_avg_records:.0f} records/day")

# 2. Fatigue Indicators (last 7-10 days of the period)
fatigue_start = (datetime.strptime(period_end, "%Y-%m-%d") - timedelta(days=10)).strftime("%Y-%m-%d")
query_fatigue = """
SELECT 
    DATE(start_date AT TIME ZONE 'America/Vancouver') as date,
    type,
    SUM(value) as total_val,
    AVG(value) as avg_val
FROM "{SCHEMA}".health_records
WHERE start_date >= %s AND start_date < %s
AND type IN (
    'HKQuantityTypeIdentifierRestingHeartRate',
    'HKQuantityTypeIdentifierHeartRateVariabilitySDNN',
    'HKQuantityTypeIdentifierStepCount',
    'HKCategoryTypeIdentifierSleepAnalysis'
)
GROUP BY 1, 2
ORDER BY 1, 2
"""
df_fatigue = pd.read_sql_query(query_fatigue, conn, params=[fatigue_start, period_end])
print("\n=== FATIGUE INDICATORS (last 10 days of period) ===")
for date in sorted(df_fatigue['date'].unique()):
    day_data = df_fatigue[df_fatigue['date'] == date]
    
    rhr = day_data[day_data['type'] == 'HKQuantityTypeIdentifierRestingHeartRate']['avg_val'].mean()
    hrv = day_data[day_data['type'] == 'HKQuantityTypeIdentifierHeartRateVariabilitySDNN']['avg_val'].mean()
    steps = day_data[day_data['type'] == 'HKQuantityTypeIdentifierStepCount']['total_val'].sum()
    
    # Sleep is tricky if we just sum 0s, but let's see what's there
    sleep = day_data[day_data['type'] == 'HKCategoryTypeIdentifierSleepAnalysis']['total_val'].sum()
    
    print(f"{date}: RHR={rhr:.1f} | HRV={hrv:.1f} | Steps={steps:.0f} | SleepVal={sleep}")

conn.close()