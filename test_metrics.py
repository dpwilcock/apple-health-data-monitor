import os
import socket
import json
import time

TARGET = (os.environ.get("HEALTH_HOST", "localhost"), int(os.environ.get("HEALTH_PORT", "9000")))

req = {
    "jsonrpc": "2.0", "id": "1", "method": "callTool",
    "params": {
        "name": "health_metrics",
        "arguments": {
            "start": os.environ.get("HEALTH_START", "2026-01-01 00:00:00 -0700"),
            "end": os.environ.get("HEALTH_END", "2026-12-31 23:59:59 -0700"),
            "interval": "days",
            "aggregate": True,
            "metrics": "active_energy,basal_energy,heart_rate,resting_heart_rate,sleep_analysis,step_count,flights_climbed,apple_stand_time"
        }
    }
}

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
data = json.loads(resp_bytes)
if 'result' in data and 'data' in data['result']:
    for m in data['result']['data']['metrics']:
        print(f"Got {m['name']} with {len(m['data'])} records")
else:
    print("Failed", data)
