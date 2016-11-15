#!/usr/bin/python2
# append a rain obsveration to the logfile

import datetime
import sys
import re

# LOOK full path need for cron
datafile = "/home/pi/Wx/rainobsv.txt"
dts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

dailyrainin=0.00;

# pass in rain fall accumulation on the argv in inches
# or just take the argument from command line

# using reg exp badly - this works but were just foolin around
# the brackets create the set of characters for the match
quitchar= re.compile('[quQxexit]')

if  len(sys.argv) < 2:
  rainobsv = raw_input("Rainfall obsv or q to quit: ")
  #x= quitchar.match(rainobsv)
  #if x:
  if quitchar.match(rainobsv):
        sys.exit()
  dailyrainin = float (rainobsv)
else:
  # the rain amount is on the argv
  program, rainobsv = sys.argv
  dailyrainin = float (rainobsv)

print("input {:.2f} # {} ".format (dailyrainin,dts))

# write the rainfall obsv to datafile
with open(datafile, "a") as myfile:
    myfile.write("{:.2f} # {}\n".format (dailyrainin, dts))

myfile.close();
