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
            "metrics": "sleep_analysis",
            "interval": "days",
            "aggregate": True
        }
    }
}

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect(TARGET)
    s.sendall(json.dumps(req).encode('utf-8') + b'\n')
    resp_bytes = b''
    while True:
        chunk = s.recv(8192)
        if not chunk: break
        resp_bytes += chunk
    s.close()
    
    data = json.loads(resp_bytes)
    metrics = data.get('result', {}).get('data', {}).get('metrics', [])
    if metrics:
        sleep_data = metrics[0].get('data', [])
        print(f"{'Date':<12} | {'Total':<6} | {'Deep':<6} | {'Core':<6} | {'REM':<6}")
        print("-" * 45)
        for d in sleep_data:
            date = d.get('date', '')[:10]
            total = d.get('totalSleep', 0)
            deep = d.get('deep', 0)
            core = d.get('core', 0)
            rem = d.get('rem', 0)
            print(f"{date:<12} | {total:<6.1f} | {deep:<6.1f} | {core:<6.1f} | {rem:<6.1f}")
    else:
        print("No sleep data returned.")
except Exception as e:
    print(f"Error connecting to iPhone TCP server: {e}")
