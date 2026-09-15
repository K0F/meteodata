#!/usr/bin/env python3
"""Merge raw weather data into a single clean CSV.

Inputs (all in data/raw/):
- rtl_433 JSON-lines sensor files (source = "sensor")
- chmi_karlov_daily.csv  (source = "chmi", daily, Praha-Karlov)
- era5_gaps.csv          (source = "era5", hourly reanalysis)

Deduplicates by (time, source, id) and sorts chronologically. Lines that fail
to parse (torn writes / NUL-corruption) are skipped.
"""

import csv
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE, "data", "raw")
OUT_CSV = os.path.join(BASE, "data", "meteo.csv")

SENSOR_FILES = [
    "2023_graph.json",
    "backup2.json",
    "weather_data_all.json",
    "backup.json",
    "graph.json",
]

EXTERNAL_FILES = [
    "chmi_karlov_daily.csv",
    "era5_gaps.csv",
]

FIELDS = [
    "time",
    "source",
    "id",
    "battery_ok",
    "temperature_C",
    "humidity",
    "wind_avg_m_s",
    "wind_dir_deg",
]


def _read_sensor_rows():
    for name in SENSOR_FILES:
        path = os.path.join(RAW_DIR, name)
        n_rows = 0
        n_skip = 0
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    n_skip += 1
                    continue
                d["source"] = "sensor"
                yield d
                n_rows += 1
        print(
            "{}: {} rows kept, {} skipped".format(name, n_rows, n_skip),
            file=sys.stderr,
        )


def _read_external_rows():
    for name in EXTERNAL_FILES:
        path = os.path.join(RAW_DIR, name)
        n_rows = 0
        with open(path) as fh:
            for d in csv.DictReader(fh):
                if not d.get("time"):
                    continue
                yield d
                n_rows += 1
        print("{}: {} rows".format(name, n_rows), file=sys.stderr)


def main():
    rows = {}
    for d in _read_sensor_rows():
        key = (d.get("time"), d.get("source"), d.get("id"))
        if key not in rows:
            rows[key] = d
    for d in _read_external_rows():
        key = (d.get("time"), d.get("source"), d.get("id"))
        if key not in rows:
            rows[key] = d

    rows = [rows[k] for k in sorted(rows)]
    with open(OUT_CSV, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print("wrote {} rows to {}".format(len(rows), OUT_CSV), file=sys.stderr)


if __name__ == "__main__":
    main()
