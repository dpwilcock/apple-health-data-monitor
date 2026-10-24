# Personal Health Monitor

Get more out of Apple Watch and Apple Health data by getting them out of Apple's data store and into your own database.  PostGres for modern DB power. iPhone App "Auto Export" is a critical part of the workflow. (https://apps.apple.com/ca/app/health-auto-export-json-csv/id1115567069)

Data is pushed to a local server/computer/laptop that also runs an Ai/LLM Agent and can coordinate/lead the analysis work that this ingestion makes possible.  

Pull wearable/health-receiver metrics into PostgreSQL, sync gaps, and run correlation/CUSUM analysis.

Utilities for collecting wearable and biometric health data from a small local health receiver (or any HTTP endpoint serving JSON), keeping PostgreSQL in sync, and running analyses: fatigue scoring, sleep/HRV correlations, CUSUM change detection, and ASCII charts for quick terminal looks.

## Components

- `sync_health.py` — pull a time-window of Apple Health step data from the local receiver into PostgreSQL
- `get_sleep_api.py` — pull sleep-stage summary data (deep/core/REM/total) from the receiver
- `test_metrics.py` — exercise the receiver's multi-metric endpoint, list record counts
- `fatigue_analysis.py` / `fatigue_final.py` — fatigue-indicator scans over HRV/RHR/steps/sleep (windows via `FATIGUE_START`/`FATIGUE_END`)
- `correlate_all.py` / `correlate_sleep.py` — Pearson correlations: mood vs. activity, mood vs. sleep
- `generate_cusum.py` — CUSUM change-point analysis (utility-consumption variant ships with this repo)
- `ascii_chart.py` — render a metric series as an ASCII bar chart

## Requirements

- Python 3.9+
- `pip install -r requirements.txt`
- A local health receiver reachable at `HEALTH_HOST:HEALTH_PORT` (default `localhost:9000`) exposing a JSON-RPC `health_metrics` method
- PostgreSQL database

## Configuration (environment variables)

| Variable | Purpose |
|----------|---------|
| `HEALTH_HOST` / `HEALTH_PORT` | Health receiver host/port (default: `localhost:9000`) |
| `PGDATABASE` | PostgreSQL database name (default: `postgres`) |

## Usage

```bash
python3 sync_health.py            # pull the configured window of step data
python3 test_metrics.py           # check which health metrics the receiver exposes
python3 get_sleep_api.py          # print sleep-stage summary rows
python3 fatigue_analysis.py       # fatigue indicators (set FATIGUE_START/FATIGUE_END)
python3 correlate_sleep.py        # mood vs. sleep-hours correlation
python3 correlate_all.py           # mood vs. activity correlation
python3 generate_cusum.py         # CUSUM change-point chart (utility example)
python3 ascii_chart.py            # ASCII bar chart of monthly mood averages
```

Every script reads `HEALTH_START`/`HEALTH_END` (ISO datetime, default full year) for its
receiver window, and `PGDATABASE` for the database.

## Design note

The receiver endpoint shape is simple JSON-RPC (method `health_metrics`); adapt the
request in `sync_health.py` to match your wearable's exporter.
