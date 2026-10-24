import os
import psycopg2
import math

SCHEMA = os.environ.get("PGSCHEMA", "DW Health")

def pearson(x, y):
    n = len(x)
    if n < 2: return 0.0
    mean_x, mean_y = sum(x)/n, sum(y)/n
    den_x = sum((xi - mean_x)**2 for xi in x)
    den_y = sum((yi - mean_y)**2 for yi in y)
    if den_x == 0 or den_y == 0: return 0.0
    num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    return num / math.sqrt(den_x * den_y)

conn = psycopg2.connect(dbname=os.environ.get("PGDATABASE", "postgres"))
cur = conn.cursor()

query_health = f"""
WITH mood AS (
    SELECT date_trunc('day', log_time) as log_date, AVG(COALESCE(sentiment_score_dw, sentiment_score_llm)) as mood_score
    FROM "{SCHEMA}".mood_log
    WHERE COALESCE(sentiment_score_dw, sentiment_score_llm) IS NOT NULL
    GROUP BY 1
)
SELECT 
    m.mood_score,
    h.active_energy_burned,
    h.apple_exercise_time,
    h.apple_stand_hours
FROM mood m
JOIN "{SCHEMA}".health_activity_summaries h ON m.log_date = date_trunc('day', h.date_components)
"""
try:
    cur.execute(query_health)
    rows = cur.fetchall()
    
    valid_rows = [r for r in rows if r[1] is not None and r[2] is not None and r[3] is not None]
    
    if len(valid_rows) > 1:
        print(f"\n--- Apple Health Activity - All Time (n={len(valid_rows)}) ---")
        mood = [float(r[0]) for r in valid_rows]
        energy = [float(r[1]) for r in valid_rows]
        exercise = [float(r[2]) for r in valid_rows]
        stand = [float(r[3]) for r in valid_rows]
        
        print(f"Active Energy Burned: {pearson(mood, energy):.3f}")
        print(f"Exercise Time: {pearson(mood, exercise):.3f}")
        print(f"Stand Hours: {pearson(mood, stand):.3f}")
except Exception as e:
    print(f"\nHealth Summaries skipped or error: {e}")

