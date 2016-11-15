#!/usr/bin/python2
# 11/7/16
# liter bottle rain gage calculator
# input the volume of rain in  ml collected from 106.172 mm aperture funnel
#

import datetime
import sys
import re

dts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
dailyrainin=0.00;

quitchar= re.compile('[quQxexit]')

if  len(sys.argv) < 2:
  rainobsv = raw_input("Rainfall vol in ml or q to quit: ")
  if quitchar.match(rainobsv):
        sys.exit()
else:
  # the rain amount is on the argv
  program, rainobsv = sys.argv

V = int (rainobsv)
r = 10.6172/2
A = 3.14159 * r * r
h = V / A
cm = h*10
inch = h/2.54

print("{} gage vol {} ml == {:.1f} mm = {:.2f} in".format (dts, V, cm, inch))


# write the rainfall obsv to datafile
datafile = "/home/pi/Wx/gage.txt"
with open(datafile, "a") as myfile:
 myfile.write ("{} gage vol {} ml == {:.1f} mm = {:.2f} in\n".format (dts, V, cm, inch))
myfile.close();
