#!/bin/bash
filename=$1
avrdude -p m328p -c arduino -P /dev/ttyUSB0 -b 115200 -U flash:w:${filename}