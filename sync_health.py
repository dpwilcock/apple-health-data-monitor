import os
import socket
import json
import time
import psycopg2
from datetime import datetime, timedelta

SCHEMA = os.environ.get("PGSCHEMA", "DW Health")

TARGET = (os.environ.get("HEALTH_HOST", "localhost"), int(os.environ.get("HEALTH_PORT", "9000")))

def fetch_data():
    req = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "callTool",
        "params": {
            "name": "health_metrics",
            "arguments": {
                "start": os.environ.get("HEALTH_START", "2026-01-01 00:00:00 -0700"),
                "end": os.environ.get("HEALTH_END", "2026-12-31 23:59:59 -0700"),
                "metrics": "step_count",
                "interval": "hours",
                "aggregate": True
            }
        }
    }
    
    for attempt in range(1, 6):
        try:
            print(f"Attempt {attempt}...")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect(TARGET)
            s.sendall(json.dumps(req).encode('utf-8') + b'\n')
            
            resp_bytes = b''
            while True:
                chunk = s.recv(8192)
                if not chunk: break
                resp_bytes += chunk
            s.close()
            
            return json.loads(resp_bytes)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)
            
    return None

data = fetch_data()
if not data or 'result' not in data:
    print("Failed to get data")
    exit(1)

metrics = data['result']['data']['metrics'][0]
metric_name = metrics['name']
unit = metrics['units']
records = metrics['data']

print(f"Got {len(records)} records for {metric_name}. Inserting to DB...")

conn = psycopg2.connect(dbname=os.environ.get("PGDATABASE", "postgres"))
cur = conn.cursor()

inserted = 0
for r in records:
    # e.g. {"date":"2026-06-01 03:00:00 -0700","qty":12,"source":"Apple Watch"}
    qty = r.get('qty')
    dt = r.get('date')
    source = r.get('source', '')
    
    if qty is None or dt is None: continue
    
    cur.execute(f"""
        INSERT INTO "{SCHEMA}".health_records (type, source_name, unit, value, start_date, end_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """, (metric_name, source, unit, qty, dt, dt))
    inserted += 1

conn.commit()
cur.close()
conn.close()

print(f"Successfully inserted {inserted} records into \"DW Health\".health_records!")
