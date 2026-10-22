import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.adapters.simulator import SimulatorAdapter
from app.database import get_db, initialize_database


app = FastAPI(title="Fieldnote BMS API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
Connection = Annotated[sqlite3.Connection, Depends(get_db)]


def simulator_snapshot() -> dict[str, dict[str, object]]:
    return {
        str(point["point_id"]): point
        for point in SimulatorAdapter().read_points()
    }


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    location: str = Field(min_length=2, max_length=120)
    building_type: str = Field(min_length=2, max_length=60)


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "local-simulation"}


@app.get("/api/overview")
def overview(connection: Connection) -> dict[str, object]:
    project_count = connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    equipment_count = connection.execute("SELECT COUNT(*) FROM equipment").fetchone()[0]
    point_count = connection.execute("SELECT COUNT(*) FROM points").fetchone()[0]
    alarms = connection.execute(
        """SELECT p.id, p.name, p.value, p.unit, e.name AS equipment_name
           FROM points p JOIN equipment e ON p.equipment_id = e.id
           WHERE p.quality != 'good' ORDER BY p.observed_at DESC"""
    ).fetchall()
    readings = connection.execute(
        """SELECT p.id, p.name, p.value, p.unit, p.quality, p.observed_at,
                  e.name AS equipment_name
           FROM points p JOIN equipment e ON p.equipment_id = e.id
           ORDER BY p.id LIMIT 5"""
    ).fetchall()
    simulated = simulator_snapshot()
    latest_readings = []
    for row in readings:
        reading = dict(row)
        sample = simulated.get(str(reading["id"]))
        if sample is not None:
            reading.update(
                {key: sample[key] for key in ("value", "observed_at")}
            )
        latest_readings.append(reading)
    return {
        "project_count": project_count,
        "equipment_count": equipment_count,
        "point_count": point_count,
        "active_alarms": [dict(row) for row in alarms],
        "latest_readings": latest_readings,
    }


@app.get("/api/projects")
def list_projects(connection: Connection) -> list[dict[str, object]]:
    rows = connection.execute(
        """SELECT p.id, p.name, p.building_type, p.created_at,
                  s.name AS site_name, s.location,
                  COUNT(DISTINCT e.id) AS equipment_count,
                  COUNT(DISTINCT pt.id) AS point_count
           FROM projects p
           LEFT JOIN sites s ON s.project_id = p.id
           LEFT JOIN zones z ON z.site_id = s.id
           LEFT JOIN equipment e ON e.zone_id = z.id
           LEFT JOIN points pt ON pt.equipment_id = e.id
           GROUP BY p.id ORDER BY p.id"""
    ).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/projects", status_code=201)
def create_project(payload: ProjectCreate, connection: Connection) -> dict[str, object]:
    try:
        cursor = connection.execute(
            "INSERT INTO projects (name, building_type) VALUES (?, ?)",
            (payload.name.strip(), payload.building_type.strip()),
        )
        project_id = cursor.lastrowid
        connection.execute(
            "INSERT INTO sites (project_id, name, location) VALUES (?, ?, ?)",
            (project_id, payload.name.strip(), payload.location.strip()),
        )
        connection.commit()
    except sqlite3.Error as error:
        connection.rollback()
        raise HTTPException(status_code=500, detail="Unable to create project") from error
    return {
        "id": project_id,
        "name": payload.name.strip(),
        "building_type": payload.building_type.strip(),
        "site_name": payload.name.strip(),
        "location": payload.location.strip(),
        "equipment_count": 0,
        "point_count": 0,
    }


@app.get("/api/devices")
def list_devices(connection: Connection) -> list[dict[str, object]]:
    rows = connection.execute(
        """SELECT e.id, e.name, e.equipment_type, e.adapter, z.name AS zone_name,
                  s.name AS site_name, p.id AS point_id, p.name AS point_name,
                  p.value, p.unit, p.point_type, p.quality, p.observed_at
           FROM equipment e
           JOIN zones z ON e.zone_id = z.id
           JOIN sites s ON z.site_id = s.id
           LEFT JOIN points p ON p.equipment_id = e.id
           ORDER BY e.id, p.id"""
    ).fetchall()
    devices: dict[int, dict[str, object]] = {}
    simulated = simulator_snapshot()
    for row in rows:
        device = devices.setdefault(
            row["id"],
            {
                "id": row["id"],
                "name": row["name"],
                "equipment_type": row["equipment_type"],
                "adapter": row["adapter"],
                "zone_name": row["zone_name"],
                "site_name": row["site_name"],
                "points": [],
            },
        )
        if row["point_id"] is not None:
            point = {
                "id": row["point_id"],
                "name": row["point_name"],
                "value": row["value"],
                "unit": row["unit"],
                "point_type": row["point_type"],
                "quality": row["quality"],
                "observed_at": row["observed_at"],
            }
            sample = simulated.get(str(row["point_id"]))
            if sample is not None:
                point.update(
                    {key: sample[key] for key in ("value", "observed_at")}
                )
            device["points"].append(
                point
            )
    return list(devices.values())


@app.get("/api/trends/{point_id}")
def point_trend(point_id: str, connection: Connection) -> dict[str, object]:
    point = connection.execute(
        "SELECT id, name, value, unit FROM points WHERE id = ?", (point_id,)
    ).fetchone()
    if point is None:
        raise HTTPException(status_code=404, detail="Point not found")
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    base = float(point["value"])
    points = []
    for hours_ago in range(23, -1, -1):
        timestamp = now - timedelta(hours=hours_ago)
        wave = ((hours_ago * 7) % 13 - 6) * 0.12
        points.append(
            {"time": timestamp.isoformat(), "value": round(base + wave, 1)}
        )
    return {
        "point_id": point["id"],
        "name": point["name"],
        "unit": point["unit"],
        "points": points,
    }


@app.get("/api/simulator/adapter")
def simulator_values() -> list[dict[str, object]]:
    return SimulatorAdapter().read_points()
