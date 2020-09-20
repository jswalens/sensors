#!/usr/bin/env python3

import datetime as dt
import json
import rapidjson
from flask import Flask, send_file, jsonify
APP = Flask("sensors",)

@APP.route("/")
def home():
    return send_file("index.html")

def parse_mhz19_line(line):
    try:
        line = rapidjson.loads(line)
        return {
            "time": dt.datetime.strptime(line["time"], "%Y-%m-%dT%H:%M:%S%z"),
            "co2": line["co2"],
            "temperature": line["temperature"],
        }
    except json.decoder.JSONDecodeError:
        return None
    except ValueError:
        return None

def parse_sds011_line(line):
    line = line.split(",")
    if len(line) != 3:
        return None
    try:
        time = dt.datetime.strptime(line[0], "%Y-%m-%dT%H:%M:%S%z")
        time = time.astimezone(dt.timezone.utc)
        pm25 = float(line[1])
        pm10 = float(line[2])
        if pm25 == 0 and pm10 == 0:
            return None
        return {
            "time": time,
            "pm25": pm25,
            "pm10": pm10,
        }
    except ValueError:
        return None

@APP.route("/co2.json")
def data_co2():
    TIME_LIMIT = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)
    LINE_LIMIT = 12000  # 14 days of a measurement every 2 minutes = 10.080 measurements
    result = []
    with open("mh-z19.log") as f:
        data = f.readlines()
        data = data[-LINE_LIMIT:]
    for l in data:
        d = parse_mhz19_line(l)
        if d is None:
            continue
        if d["time"] < TIME_LIMIT:
            continue
        d["time"] = d["time"].isoformat()
        result.append(d)
    return jsonify(co2=result)

@APP.route("/pm.json")
def data_pm():
    TIME_LIMIT = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)
    LINE_LIMIT = 2500  # 14 days of a measurement every 10 minutes = 2016 measurements
    result = []
    with open("sds-011.log") as f:
        data = f.readlines()
        data = data[-LINE_LIMIT:]
    for l in data:
        d = parse_sds011_line(l)
        if d is None:
            continue
        if d["time"] < TIME_LIMIT:
            continue
        d["time"] = d["time"].isoformat()
        result.append(d)
    return jsonify(pm=result)

if __name__ == "__main__":
    APP.run()
