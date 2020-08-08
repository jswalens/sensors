#!/usr/bin/env python3
#
# Script to read data from MH-Z19B CO2 sensor.
#
# Based on https://github.com/UedaTakeyuki/mh-z19, and distributed under the
# MIT License. I refactored the script, removed support for Python 2, and
# simplified some things.
# 
# Copyright (c) 2018 Dr. Takeyuki Ueda
# Copyright (c) 2020 Janwillem Swalens
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import serial
import struct
import argparse
import json
import os.path
import datetime
import pytz

VERSION = "0.4.0-jw"
DEVICE_PATH = "/dev/serial0"
TIMEZONE = pytz.timezone('Europe/Brussels')

def current_time():
    now = datetime.datetime.now().astimezone(TIMEZONE)
    return now.strftime('%Y-%m-%dT%H:%M:%S%z')

def connect():
    return serial.Serial(DEVICE_PATH, baudrate=9600, timeout=3.0)

def read_all():
    with connect() as ser:
        ser.write(b"\xff\x01\x86\x00\x00\x00\x00\x00\x79")
        r = ser.read(9)

        if len(r) == 9 and r[0] == 0xff and r[1] == 0x86:
            return {"time": current_time(),
                    "co2": r[2]*256 + r[3],
                    "temperature": r[4] - 40,
                    "TT": r[4], # raw temperature
                    "SS": r[5], # status?
                    "Uh": r[6], # ticks in calibration cycle?
                    "Ul": r[7]} # number of performed calibrations?
        else:
            raise Exception("got unexpected answer %s" % r)

def read():
    result = read_all()
    return {"time": current_time(), "co2": result["co2"]}

def abc_on():
    with connect() as ser:
        ser.write(b"\xff\x01\x79\xa0\x00\x00\x00\x00\xe6")

def abc_off():
    with connect() as ser:
        ser.write(b"\xff\x01\x79\x00\x00\x00\x00\x00\x86")

def zero_point_calibration():
    with connect() as ser:
        ser.write(b"\xff\x01\x87\x00\x00\x00\x00\x00\x78")

def span_point_calibration(span):
    with connect() as ser:
        b3 = span // 256
        byte3 = struct.pack("B", b3)
        b4 = span % 256
        byte4 = struct.pack("B", b4)
        c = checksum([0x01, 0x88, b3, b4])
        request = b"\xff\x01\x88" + byte3 + byte4 + b"\x00\x00\x00" + c
        ser.write(request)

def detection_range_2000():
    with connect() as ser:
        ser.write(b"\xff\x01\x99\x00\x00\x00\x07\xd0\x8f")

def detection_range_5000():
    with connect() as ser:
        ser.write(b"\xff\x01\x99\x00\x00\x00\x13\x88\xcb")

def detection_range_10000():
    with connect() as ser:
        ser.write(b"\xff\x01\x99\x00\x00\x00\x27\x10\x2f")

def checksum(array):
    return struct.pack("B", 0xff - (sum(array) % 0x100) + 1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="return CO2 concentration as json",
    )

    parser.add_argument("--serial_device",
                        type=str,
                        default=DEVICE_PATH,
                        help="use this serial device file")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--version",
                       action="store_true",
                       help="show version")
    group.add_argument("--all",
                       action="store_true",
                       help="return all (time, co2, temperature, TT, SS, Uh, Ul) as json")
    group.add_argument("--abc_on",
                       action="store_true",
                       help="turn automatic calibration on")
    group.add_argument("--abc_off",
                       action="store_true",
                       help="turn automatic calibration off")
    group.add_argument("--span_point_calibration",
                       type=int,
                       help="call calibration function with SPAN point")
    group.add_argument("--zero_point_calibration",
                       action="store_true",
                       help="call calibration function with ZERO point")
    group.add_argument("--detection_range_2000",
                       action="store_true",
                       help="set detection range to 0-2000ppm")
    group.add_argument("--detection_range_5000",
                       action="store_true",
                       help="set detection range to 0-5000ppm")
    group.add_argument("--detection_range_10000",
                       action="store_true",
                       help="set detection range to 0-10000ppm")

    args = parser.parse_args()

    if args.serial_device is not None:
        DEVICE_PATH = args.serial_device

    if args.abc_on:
        abc_on()
        print("ABC on")
    elif args.abc_off:
        abc_off()
        print("ABC off")
    elif args.span_point_calibration is not None:
        span_point_calibration(args.span_point_calibration)
        print("Calibration with SPAN point")
    elif args.zero_point_calibration:
        print("Calibration with ZERO point")
        zero_point_calibration()
    elif args.detection_range_2000:
        detection_range_2000()
        print("Detection range set to 0-2000ppm")
    elif args.detection_range_5000:
        detection_range_5000()
        print("Detection range set to 0-5000ppm")
    elif args.detection_range_10000:
        detection_range_10000()
        print("Detection range set to 0-10000ppm")
    elif args.version:
        print(VERSION)
    elif args.all:
        print(json.dumps(read_all()))
    else:
        print(json.dumps(read()))
