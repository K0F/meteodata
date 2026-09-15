#!/usr/bin/env python3
"""Merge raw rtl_433 JSON-lines weather data into a single clean CSV.

Deduplicates by (time, id) and sorts chronologically. Lines that fail to
parse (torn writes / NUL-corruption) are skipped.
"""

import csv
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE, "data", "raw")
OUT_CSV = os.path.join(BASE, "data", "meteo.csv")

RAW_FILES = [
    "2023_graph.json",
    "backup2.json",
    "weather_data_all.json",
    "backup.json",
    "graph.json",
]

FIELDS = [
    "time",
    "id",
    "battery_ok",
    "temperature_C",
    "humidity",
    "wind_avg_m_s",
    "wind_dir_deg",
]


def main():
    rows = {}
    for name in RAW_FILES:
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
                key = (d.get("time"), d.get("id"))
                if key in rows:
                    continue
                rows[key] = d
                n_rows += 1
        print(
            "{}: {} rows kept, {} skipped".format(name, n_rows, n_skip), file=sys.stderr
        )

    rows = [rows[k] for k in sorted(rows)]
    with open(OUT_CSV, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print("wrote {} rows to {}".format(len(rows), OUT_CSV), file=sys.stderr)


if __name__ == "__main__":
    main()
