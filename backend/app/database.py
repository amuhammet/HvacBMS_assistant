import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Iterator


DEFAULT_DATABASE = Path(__file__).resolve().parents[1] / "data" / "bms.db"
DATABASE_PATH = Path(os.environ.get("BMS_DB_PATH", DEFAULT_DATABASE))


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def get_db() -> Iterator[sqlite3.Connection]:
    connection = get_connection()
    try:
        yield connection
    finally:
        connection.close()


def initialize_database() -> None:
    with closing(get_connection()) as connection, connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                building_type TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                location TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
                name TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone_id INTEGER NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                equipment_type TEXT NOT NULL,
                adapter TEXT NOT NULL DEFAULT 'simulator'
            );
            CREATE TABLE IF NOT EXISTS points (
                id TEXT PRIMARY KEY,
                equipment_id INTEGER NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                point_type TEXT NOT NULL,
                quality TEXT NOT NULL DEFAULT 'good',
                observed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone_id INTEGER NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                details TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                enabled INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        if connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0:
            seed_demo_project(connection)


def seed_demo_project(connection: sqlite3.Connection) -> None:
    project_id = connection.execute(
        "INSERT INTO projects (name, building_type) VALUES (?, ?)",
        ("Northwind Workspace", "Office"),
    ).lastrowid
    site_id = connection.execute(
        "INSERT INTO sites (project_id, name, location) VALUES (?, ?, ?)",
        (project_id, "Northwind HQ", "Portland, OR"),
    ).lastrowid
    zone_id = connection.execute(
        "INSERT INTO zones (site_id, name) VALUES (?, ?)", (site_id, "Level 02"),
    ).lastrowid
    equipment_id = connection.execute(
        """INSERT INTO equipment (zone_id, name, equipment_type, adapter)
           VALUES (?, ?, ?, ?)""",
        (zone_id, "AHU-01 · North Wing", "Air handling unit", "simulator"),
    ).lastrowid
    points = [
        ("sim-supply-temp", "Supply air temperature", 17.8, "°C", "analog-input"),
        ("sim-outdoor-temp", "Outdoor air temperature", 12.4, "°C", "analog-input"),
        ("sim-humidity", "Relative humidity", 45.0, "%", "analog-input"),
        ("sim-fan-status", "Supply fan status", 1.0, "On", "binary-input"),
        ("sim-filter-dp", "Filter differential pressure", 128.0, "Pa", "analog-input"),
    ]
    connection.executemany(
        """INSERT INTO points (id, equipment_id, name, value, unit, point_type)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [(point_id, equipment_id, name, value, unit, point_type)
         for point_id, name, value, unit, point_type in points],
    )
    connection.execute(
        "INSERT INTO schedules (zone_id, name, enabled, details) VALUES (?, ?, ?, ?)",
        (zone_id, "Weekday occupancy", 1, "Mon–Fri · 07:00–19:00"),
    )
    connection.execute(
        """INSERT INTO sequences (equipment_id, name, description, enabled)
           VALUES (?, ?, ?, ?)""",
        (equipment_id, "Supply air reset", "Draft sequence · simulation only", 0),
    )
