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

query_sleep = """
WITH mood AS (
    SELECT date_trunc('day', log_time) as log_date, AVG(COALESCE(sentiment_score_dw, sentiment_score_llm)) as mood_score
    FROM "{SCHEMA}".mood_log
    WHERE COALESCE(sentiment_score_dw, sentiment_score_llm) IS NOT NULL
    GROUP BY 1
),
sleep AS (
    SELECT date_trunc('day', creation_date) as sleep_date, SUM(value) as sleep_hours
    FROM "{SCHEMA}".health_records
    WHERE type = 'HKCategoryTypeIdentifierSleepAnalysis' AND value > 0
    GROUP BY 1
)
SELECT m.mood_score, s.sleep_hours
FROM mood m
JOIN sleep s ON m.log_date = s.sleep_date
"""
try:
    cur.execute(query_sleep)
    rows = cur.fetchall()
    if len(rows) > 1:
        print(f"\n--- Apple Health Sleep - All Time (n={len(rows)}) ---")
        mood = [float(r[0]) for r in rows]
        sleep = [float(r[1]) for r in rows]
        print(f"Sleep Amount: {pearson(mood, sleep):.3f}")
except Exception as e:
    pass
