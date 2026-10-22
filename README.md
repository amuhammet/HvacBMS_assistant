# HvacBMS_assistant
Local-first HVAC and building management studio with React, FastAPI, SQLite, and simulated equipment monitoring.

# Fieldnote BMS Studio

A local-first building management and HVAC project studio starter. The first version includes a React + TypeScript dashboard, a project setup wizard, device/point monitoring, a simulator adapter, and a local SQLite-backed FastAPI service.

Live protocol writes are intentionally not implemented. BACnet/IP, Modbus TCP/RTU, MQTT, and Home Assistant are planned adapter integrations; the current adapter surface is read-only and simulation-first.

## Requirements

- Node.js 20+
- Python 3.10+

## Run locally

In the project root, install frontend dependencies and start Vite:

```powershell
npm install
npm run dev
```

In a second terminal, set up and start the API:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open the local Vite URL shown in the first terminal. The API is available at `http://127.0.0.1:8000`; interactive API documentation is at `/docs`.

The SQLite file is created at `backend/data/bms.db` on first API startup. Set `BMS_DB_PATH` to use a different local database path.

## Current scope

- Dashboard summary, simulated trends, and equipment point values
- Local project creation and listing
- SQLite models for projects, sites, zones, equipment, points, schedules, and sequences
- A shared read-only adapter protocol with a simulator implementation
- Draft schedule/sequence visibility; no sequence execution
- No network protocol discovery or equipment control

