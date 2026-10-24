import os
import psycopg2

SCHEMA = os.environ.get("PGSCHEMA", "DW Health")

conn = psycopg2.connect(dbname=os.environ.get("PGDATABASE", "postgres"))
cur = conn.cursor()

# Date window (set via env to your investigation period)
period_start = os.environ.get("FATIGUE_START", "2026-01-01")
period_end = os.environ.get("FATIGUE_END", "2026-12-31")

print("=== VERIFYING DATA IMPORT ===")
cur.execute(f"""
    SELECT type, COUNT(*) 
    FROM "{SCHEMA}".health_records 
    WHERE start_date >= %s 
    GROUP BY type
    ORDER BY count DESC
    LIMIT 10;
""", (period_start,))
for row in cur.fetchall():
    print(f"{row[0]}: {row[1]}")

print("\n=== FATIGUE INDICATORS (period) ===")
q_trends = f"""
SELECT 
    date,
    MAX(CASE WHEN type = 'HKQuantityTypeIdentifierRestingHeartRate' THEN val END) as rhr,
    MAX(CASE WHEN type = 'HKQuantityTypeIdentifierHeartRateVariabilitySDNN' THEN val END) as hrv,
    MAX(CASE WHEN type = 'HKCategoryTypeIdentifierSleepAnalysis' THEN val END) as sleep,
    MAX(CASE WHEN type = 'HKQuantityTypeIdentifierStepCount' THEN val END) as steps,
    MAX(CASE WHEN type = 'HKQuantityTypeIdentifierActiveEnergyBurned' THEN val END) as active_energy
FROM (
    SELECT 
        DATE(start_date AT TIME ZONE 'America/Vancouver') as date,
        type,
        CASE 
            WHEN type IN ('HKQuantityTypeIdentifierStepCount', 'HKQuantityTypeIdentifierActiveEnergyBurned') THEN SUM(value)
            WHEN type = 'HKCategoryTypeIdentifierSleepAnalysis' THEN SUM(value) -- Depends on how it imported, we'll see
            ELSE AVG(value)
        END as val
    FROM "{SCHEMA}".health_records
    WHERE start_date >= %s AND start_date < %s
      AND type IN (
          'HKQuantityTypeIdentifierRestingHeartRate',
          'HKQuantityTypeIdentifierHeartRateVariabilitySDNN',
          'HKQuantityTypeIdentifierStepCount',
          'HKQuantityTypeIdentifierActiveEnergyBurned',
          'HKCategoryTypeIdentifierSleepAnalysis'
      )
    GROUP BY 1, 2
) grouped
GROUP BY 1
ORDER BY 1;
"""
cur.execute(q_trends, (period_start, period_end))
print(f"{'Date':<12} | {'RHR':<5} | {'HRV':<5} | {'Sleep':<5} | {'Steps':<7} | {'Active Cal':<10}")
print("-" * 60)
for row in cur.fetchall():
    date, rhr, hrv, sleep, steps, active = row
    rhr_str = f"{rhr:.1f}" if rhr else "N/A"
    hrv_str = f"{hrv:.1f}" if hrv else "N/A"
    sleep_str = f"{sleep:.1f}h" if sleep else "N/A"
    steps_str = f"{steps:.0f}" if steps else "0"
    active_str = f"{active:.0f}" if active else "0"
    print(f"{str(date):<12} | {rhr_str:<5} | {hrv_str:<5} | {sleep_str:<5} | {steps_str:<7} | {active_str:<10}")

conn.close()