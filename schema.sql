-- Apple Health / Wearable Data PostgreSQL Schema
-- Run: psql -U postgres -d postgres -f schema.sql
--
-- Expects data pushed from a local health receiver (e.g. iPhone "Auto Export"
-- → local server) into these tables.

-- Raw health records (one row per Apple Health quantity/category sample)
CREATE TABLE IF NOT EXISTS health_records (
    id          BIGSERIAL PRIMARY KEY,
    type        TEXT NOT NULL,            -- HKQuantityTypeIdentifier* / HKCategoryTypeIdentifier*
    source_name TEXT,
    unit        TEXT,
    value       DOUBLE PRECISION,
    start_date  TIMESTAMPTZ,
    end_date    TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_health_records_type_time
    ON health_records (type, start_date DESC);

-- Daily rollups (heart-rate metrics per day)
CREATE TABLE IF NOT EXISTS daily_summary (
    summary_date       DATE PRIMARY KEY,
    hrv                DOUBLE PRECISION,   -- Heart Rate Variability (SDNN, ms)
    resting_heart_rate DOUBLE PRECISION,
    steps              INTEGER,
    sleep_total_min    INTEGER,
    updated_at         TIMESTAMPTZ DEFAULT NOW()
);

-- Activity rollups (energy, exercise, stand)
CREATE TABLE IF NOT EXISTS health_activity_summaries (
    date_components      DATE PRIMARY KEY,
    active_energy_burned DOUBLE PRECISION,
    apple_exercise_time  DOUBLE PRECISION,
    apple_stand_hours    DOUBLE PRECISION
);
