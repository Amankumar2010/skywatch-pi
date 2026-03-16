import os
import time
import requests
import psycopg2
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────
DUMP1090_URL = os.getenv("DUMP1090_URL", "http://localhost:8080/data/aircraft.json")
DB_HOST      = os.getenv("DB_HOST",     "timescaledb")
DB_PORT      = os.getenv("DB_PORT",     "5432")
DB_NAME      = os.getenv("DB_NAME",     "skywatch")
DB_USER      = os.getenv("DB_USER",     "skywatch")
DB_PASS      = os.getenv("DB_PASS",     "skywatch123")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "5"))

# ── DB connect with retry ─────────────────────────────────
def get_connection():
    while True:
        try:
            conn = psycopg2.connect(
                host=DB_HOST, port=DB_PORT,
                dbname=DB_NAME, user=DB_USER, password=DB_PASS
            )
            print("✅ Connected to TimescaleDB")
            return conn
        except Exception as e:
            print(f"⏳ Waiting for DB... {e}")
            time.sleep(3)

# ── Fetch from dump1090 ───────────────────────────────────
def fetch_aircraft():
    try:
        r = requests.get(DUMP1090_URL, timeout=5)
        r.raise_for_status()
        return r.json().get("aircraft", [])
    except Exception as e:
        print(f"⚠️  dump1090 fetch failed: {e}")
        return []

# ── Insert into TimescaleDB ───────────────────────────────
def insert_aircraft(conn, aircraft_list):
    if not aircraft_list:
        return

    now = datetime.now(timezone.utc)
    rows = []

    for a in aircraft_list:
        # Only insert if we have position data
        if a.get("lat") and a.get("lon"):
            rows.append((
                now,
                a.get("hex", ""),
                a.get("flight", "").strip() or None,
                a.get("lat"),
                a.get("lon"),
                a.get("alt_baro") or a.get("altitude"),
                a.get("gs") or a.get("speed"),
                a.get("track"),
                a.get("squawk"),
                a.get("messages"),
                a.get("seen"),
            ))

    if not rows:
        return

    try:
        with conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO aircraft
                  (time, hex, flight, lat, lon, altitude,
                   speed, track, squawk, messages, seen)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, rows)
        conn.commit()
        print(f"✈️  Inserted {len(rows)} aircraft at {now.strftime('%H:%M:%S')}")
    except Exception as e:
        print(f"❌ DB insert failed: {e}")
        conn.rollback()

# ── Main loop ─────────────────────────────────────────────
def main():
    print("🚀 SkyWatch pipeline starting...")
    conn = get_connection()

    while True:
        aircraft = fetch_aircraft()
        print(f"📡 Fetched {len(aircraft)} aircraft from dump1090")
        insert_aircraft(conn, aircraft)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
