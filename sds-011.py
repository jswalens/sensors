#!/usr/bin/env python3

import sys
import datetime
import time
import pytz
from sds011 import SDS011

WAIT_PERIOD = 30 # minutes
TIMEZONE = pytz.timezone('Europe/Brussels')

sensor = SDS011('/dev/ttyUSB0')
sensor.set_work_period(work_time=WAIT_PERIOD)

def fetch_once():
    now = datetime.datetime.now().astimezone(TIMEZONE)
    nowStr = now.strftime('%Y-%m-%dT%H:%M:%S%z')
    (pm25, pm10) = sensor.query()
    print("%s,%s,%s" % (nowStr, pm25, pm10))
    sys.stdout.flush()

def fetch_loop():
    while True:
        main()
        time.sleep(WAIT_PERIOD * 60)

fetch_once()
