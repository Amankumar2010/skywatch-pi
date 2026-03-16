CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS aircraft (
    time        TIMESTAMPTZ NOT NULL,
    hex         TEXT NOT NULL,
    flight      TEXT,
    lat         DOUBLE PRECISION,
    lon         DOUBLE PRECISION,
    altitude    INTEGER,
    speed       INTEGER,
    track       INTEGER,
    squawk      TEXT,
    messages    INTEGER,
    seen        DOUBLE PRECISION
);

SELECT create_hypertable('aircraft', 'time', if_not_exists => TRUE);

CREATE INDEX ON aircraft (hex, time DESC);
