# Scripts for MH-Z19 CO2 and SDS-011 PM sensors

This repository contains scripts for measuring CO<sub>2</sub> levels using the MH-Z19 sensor and particulate matter (PM2.5 and PM10) using the SDS-011 sensor, on a Raspberry Pi.

The script for the SDS-011 sensor relies on the py-sds011 library ([GitHub](https://github.com/ikalchev/py-sds011) and [PyPI](https://pypi.org/project/py-sds011/)), which can be installed using `pip3 install py-sds011`. The script for the MH-Z19 sensor is a refactored version of [Ueda Takeyuki's mh-z19 library](https://github.com/UedaTakeyuki/mh-z19). These scripts require Python 3.

You can find more details on how to use the MH-Z19 CO<sub>2</sub> sensor [in my accompanying blog post](https://jnwllm.be/blog/mh-z19).

Distributed under the MIT license.
