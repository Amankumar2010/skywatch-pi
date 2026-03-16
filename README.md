# 🛫 SkyWatch Pi — Live ADS-B Flight Tracker

> A real-time aircraft tracking system built on a Raspberry Pi 5, powered by an RTL-SDR dongle, dump1090, TimescaleDB, and Grafana — with a full CI/CD pipeline via GitHub Actions.

![Grafana Dashboard](https://img.shields.io/badge/Grafana-Live%20Dashboard-orange?style=flat-square&logo=grafana)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?style=flat-square&logo=docker)
![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-black?style=flat-square&logo=github)
![Flightradar24](https://img.shields.io/badge/FR24-T--VAAH4-yellow?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 📡 What is this?

SkyWatch Pi receives live **ADS-B signals** broadcast by aircraft transponders using a cheap RTL-SDR USB dongle and a 1090 MHz antenna. It decodes these signals, stores them in a time-series database, and visualizes them on a live Grafana dashboard — all running on a Raspberry Pi 5.

### First aircraft tracked: **VTARO** ✈️
- Altitude: 9,700 ft
- Speed: 297 knots
- Location: Over Ahmedabad, Gujarat, India 🇮🇳

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Raspberry Pi 5                        │
│                                                         │
│  [RTL-SDR Dongle + 1090MHz Antenna]                     │
│           │                                             │
│           ▼                                             │
│     [dump1090-fa]  ──── writes JSON ────▶  /tmp/dump1090│
│                                               │         │
│           ┌───────────────────────────────────┘         │
│           ▼                                             │
│   [Python Pipeline]  ──── inserts ────▶ [TimescaleDB]  │
│                                               │         │
│                                               ▼         │
│                                          [Grafana]      │
│                                        :3000 (live)     │
└─────────────────────────────────────────────────────────┘
         │
         ▼
  [Flightradar24]  ◀──── feeds data ────  [fr24feed]
  Radar: T-VAAH4
```

---

## 🧰 Hardware

| Component | Model | Cost |
|---|---|---|
| Single Board Computer | Raspberry Pi 5 (8GB) | — |
| SDR Dongle | RTL-SDR Blog V4 (R828D, 1PPM TCXO) | ₹5,795 |
| Antenna | Bingfu Dual Band 1090MHz 5dBi Magnetic Base | ₹3,273 |
| Storage | NVMe SSD (235GB) | — |
| **Total Hardware** | | **~₹9,000** |

---

## 🛠️ Software Stack

| Component | Technology |
|---|---|
| ADS-B Decoder | dump1090-fa (compiled from source) |
| Data Pipeline | Python 3.11 |
| Database | TimescaleDB (PostgreSQL 15) |
| Visualization | Grafana 10.4.3 |
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Remote Access | Tailscale |
| Flight Network | Flightradar24 (Radar: T-VAAH4) |
| Process Manager | systemd |

---

## 📊 Grafana Dashboard

Live dashboard with auto-refresh every 5 seconds showing:

- **Total Aircraft Seen** — unique aircraft count
- **Aircraft Right Now** — currently tracked
- **Average Altitude** — mean altitude in feet
- **Max Speed** — fastest aircraft in knots
- **Live Aircraft Count Over Time** — time series chart
- **Altitude Over Time** — avg & max altitude trends
- **Top 10 Most Seen Aircraft** — ranked by sightings
- **Speed Over Time** — avg & max speed trends

---

## 🚀 Getting Started

### Prerequisites
- Raspberry Pi 5 running Ubuntu Server 24.04
- RTL-SDR USB dongle
- 1090 MHz antenna
- Docker + Docker Compose installed

### 1. Clone the repo
```bash
git clone https://github.com/Amankumar2010/skywatch-pi.git
cd skywatch-pi
```

### 2. Build dump1090 from source
```bash
sudo apt install -y git cmake build-essential libusb-1.0-0-dev libncurses-dev rtl-sdr librtlsdr-dev
git clone https://github.com/flightaware/dump1090.git ~/dump1090
cd ~/dump1090 && make
```

### 3. Set up dump1090 as a systemd service
```bash
sudo nano /etc/systemd/system/dump1090.service
```

```ini
[Unit]
Description=dump1090 ADS-B receiver
After=network.target

[Service]
User=YOUR_USER
ExecStartPre=/bin/mkdir -p /tmp/dump1090
ExecStart=/home/YOUR_USER/dump1090/dump1090 --net --net-bind-address 0.0.0.0 --write-json /tmp/dump1090 --quiet
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable dump1090
sudo systemctl start dump1090
```

### 4. Blacklist the DVB-T driver
```bash
echo 'blacklist dvb_usb_rtl28xxu' | sudo tee /etc/modprobe.d/blacklist-rtl.conf
sudo usermod -aG plugdev $USER
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2838", GROUP="plugdev", MODE="0664"' | sudo tee /etc/udev/rules.d/rtl-sdr.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### 5. Start the stack
```bash
mkdir -p /tmp/dump1090
docker compose up -d
```

### 6. Access Grafana
```
http://YOUR_PI_IP:3000
Username: admin
Password: admin123
```

Import `skywatch-dashboard.json` from the repo root.

---

## ⚙️ CI/CD Pipeline

Every push to `main` triggers a GitHub Actions workflow that:

1. **Builds** an ARM64 Docker image of the Python pipeline
2. **Pushes** it to GitHub Container Registry (ghcr.io)
3. **Connects** to the Pi via Tailscale
4. **SSHs** into the Pi and redeploys the container

### Required GitHub Secrets

| Secret | Description |
|---|---|
| `PI_HOST` | Pi's Tailscale IP |
| `PI_USER` | SSH username |
| `PI_SSH_KEY` | Dedicated SSH private key |
| `TAILSCALE_AUTHKEY` | Ephemeral Tailscale auth key |

---

## 📁 Project Structure

```
skywatch-pi/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD pipeline
├── pipeline/
│   ├── ingest.py               # Python data pipeline
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile              # ARM64 container
├── postgres/
│   └── init/
│       └── 01_init.sql         # TimescaleDB schema
├── grafana/
│   └── provisioning/
│       └── datasources/
│           └── timescaledb.yml # Auto-provisioned datasource
├── skywatch-dashboard.json     # Grafana dashboard export
├── docker-compose.yml          # Full stack definition
└── README.md
```

---

## 🗄️ Database Schema

```sql
CREATE TABLE aircraft (
    time        TIMESTAMPTZ NOT NULL,
    hex         TEXT NOT NULL,        -- ICAO 24-bit address
    flight      TEXT,                 -- Callsign (e.g. VTARO)
    lat         DOUBLE PRECISION,     -- Latitude
    lon         DOUBLE PRECISION,     -- Longitude
    altitude    INTEGER,              -- Altitude in feet
    speed       INTEGER,              -- Ground speed in knots
    track       INTEGER,              -- Track angle
    squawk      TEXT,                 -- Squawk code
    messages    INTEGER,              -- Message count
    seen        DOUBLE PRECISION      -- Seconds since last seen
);
-- Hypertable partitioned by time (TimescaleDB)
```

---

## 📡 Flightradar24 Integration

This station feeds live ADS-B data to Flightradar24:
- **Radar ID:** T-VAAH4
- **Location:** Chandkheda, Ahmedabad, Gujarat, India
- **Coverage:** ~150-200km radius around Ahmedabad

Active feeders receive a **free Business plan** (~$500/year value).

---

## 🗺️ Roadmap

- [x] RTL-SDR dongle + dump1090 setup
- [x] Python ingestion pipeline
- [x] TimescaleDB time-series storage
- [x] Grafana live dashboard
- [x] Docker + Compose containerization
- [x] GitHub Actions CI/CD
- [x] Flightradar24 feeder (T-VAAH4)
- [ ] K3s Kubernetes deployment
- [ ] FlightAware feeder
- [ ] Cloudflare Tunnel (public access)
- [ ] ML anomaly detection
- [ ] Multi-node Pi cluster

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Amankumar** — [@Amankumar2010](https://github.com/Amankumar2010)

