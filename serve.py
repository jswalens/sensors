#!/usr/bin/env python3

import re
import datetime as dt
import json
import rapidjson
from flask import Flask, send_file, jsonify
APP = Flask("sensors",)

@APP.route("/")
def home():
    return send_file("index.html")

MHZ19_FORMAT = re.compile(r'''{"time": "([\dTt:+-]*)", "co2": (\d+), "temperature": (\d+),''')

def parse_mhz19_line(line):
    try:
        match = MHZ19_FORMAT.match(line)
        if not match:
            return None
        return {
            "time": dt.datetime.strptime(match[1], "%Y-%m-%dT%H:%M:%S%z"),
            "co2": int(match[2]),
            "temperature": int(match[3]),
        }
        # line = rapidjson.loads(line)
        # return {
        #     "time": dt.datetime.strptime(line["time"], "%Y-%m-%dT%H:%M:%S%z"),
        #     "co2": line["co2"],
        #     "temperature": line["temperature"],
        # }
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
    result = []
    with open("mh-z19.log") as f:
        data = f.readlines()
        data.reverse()
    for l in data:
        d = parse_mhz19_line(l)
        if d is None:
            continue
        if d["time"] < TIME_LIMIT:
            break
        d["time"] = d["time"].isoformat()
        result.append(d)
    result.reverse()
    return jsonify(co2=result)

@APP.route("/pm.json")
def data_pm():
    TIME_LIMIT = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)
    result = []
    with open("sds-011.log") as f:
        data = f.readlines()
        data.reverse()
    for l in data:
        d = parse_sds011_line(l)
        if d is None:
            continue
        if d["time"] < TIME_LIMIT:
            break
        d["time"] = d["time"].isoformat()
        result.append(d)
    result.reverse()
    return jsonify(pm=result)

if __name__ == "__main__":
    APP.run()
