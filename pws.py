#!/usr/bin/python2
# ===========================================================================
# phm kalauao research
# personal weather station pws.py
# Code for BMP108 sensor
# uploads BMP108 temp and pressure data to the weather undergound personal weather station PWS network
# reads logfile to get last rain obsv
# parserain gets the last rain obsv... this requires manual update of a log file
# use prototype input.py  to input the obsv (so we dont need vi or cli to do it)
# Ver 3 of rain with ds1820 code for temp
# ===========================================================================
import Adafruit_DHT
import math
import time

import BMP085
import sys
import os
import glob
import datetime

# CONSTANTS
program = 'custom_pws_python'
elev_meters = 146
elev_meters = 133  # corrected to WUNDERGROUND elev
elev_meters = 128   # correction of .02 to SLP
elev_feet = elev_meters * 39.370/12
# #8/12 re-adjust elev 2 meters
elev_feet = 415  #126.5m
elev_meters = elev_feet  / (39.370/12)

dailyrainin=0.00;


# DHT - hard wire configuration
# system: maui2
dhtSensorType = 11
dhtGPIOpin =13
CORRECTION = 12


# LOOK power pin config
import RPi.GPIO as GPIO
dhtGPIOvdd = 6  # LOOK power pin for sensor


def toFarenheit (tC):
  return( tC * 9/5.0 + 32)

def DHT(dhtSensorType,dhtGPIOpin):
  # temperatures are deg Celcius
  GPIO.setmode(GPIO.BCM)
  GPIO.setwarnings(False)
  GPIO.setup(dhtGPIOvdd,GPIO.OUT)
  GPIO.output(dhtGPIOvdd,GPIO.HIGH)
  #print("Turn on sensor")
  time.sleep(1)

  humidity, temperature = Adafruit_DHT.read_retry(dhtSensorType, dhtGPIOpin)
  humidity +=  CORRECTION  #LOOK bogus correction

  if humidity > 100:
      time.sleep(2)
      humidity, temperature = Adafruit_DHT.read_retry(dhtSensorType, dhtGPIOpin)
      humidity +=  CORRECTION  #LOOK bogus correction

  dewpoint =243.04*(math.log(humidity/100)+((17.625*temperature)/(243.04+temperature)))/(17.625-math.log(humidity/100)-((17.625*temperature)/(243.04+temperature)))

  GPIO.output(dhtGPIOvdd,GPIO.LOW)  # LOOK Turn off sensor
  #print("Turn off sensor")
  return (humidity, dewpoint, temperature)


def ds18b20(device_number):
 os.system('modprobe w1-gpio')
 os.system('modprobe w1-therm')
 base_dir = '/sys/bus/w1/devices/'
 # this is the 2nd ds18b20 in the chain
 #device_number = 1
 device_folder = glob.glob(base_dir + '28*')[int(device_number)]
 device_file = device_folder + '/w1_slave'
 # read temp raw
 f = open(device_file, 'r')
 lines = f.readlines()
 f.close()
 #
 # read temp from the files
 while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
 equals_pos = lines[1].find('t=')
 if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f


def readLog(logfile):
  rain = 0
  with open(logfile,'r') as f:
      for line in f:
       # get rid of everything to the right of the comment hash #
       line = line.partition ('#')[0]
       line = line.rstrip()
       if line.strip():    # process only data lines
         dat = line.split()
         if (len(dat) >= 1):  # LOOK -- really ? kindof clumsy
           lastrain = dat[0]
           #print rain
  f.close()
  # return the last values in the file
  return (lastrain)

logfile = '/home/pi/Wx/rainobsv.txt'
rain = readLog( logfile )

dailyrainin = float (rain)

# Initialise the BMP085 and use STANDARD mode (default value)

bmp = BMP085.BMP085()

temp = bmp.read_temperature()
tempF = temp * 9/5 + 32
# I see a temp of 209 posted ... if temp > 100 retake it!

lowcount = 0
highcount = 0
while tempF > 100 or tempF < 60 :
  print("tempF QA fail {:.2f} : resample ".format (tempF))
  tempF = bmp.read_temperature() * 9/5 + 32
  if tempF > 100 :
        highcount += 1
        if highcount > 3:
                break
  if tempF < 60 :
        lowcount += 1
        if lowcount > 3:
                break

slp= (bmp.read_sealevel_pressure(elev_meters)/100)*0.02953

# allow for a very low pressure
# 8/14/16 a 29.89 anomaly sneaked in...  must we maintain a running average and filter out statistical deviants .  looking at the log, a 10min deviation  .01 is very unusual


lowcount = 0
highcount = 0
while slp > 30.12 or slp < 29.0  :
 print("SLP QA fail {:.2f} : resample ".format (slp))
 slp= (bmp.read_sealevel_pressure(elev_meters)/100)*0.02953

 if slp > 30.10  :
        highcount = highcount+1
        if highcount > 3:
                break
 if slp < 29.0 :
        lowcount=lowcount +1
        if lowcount > 3:
                break


dts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# call the ds18b20 device 1 for temp dat
(temp_c,ds18b20F)= ds18b20(1)


(DhtHumidity, dewpoint, temperature) = DHT(dhtSensorType,dhtGPIOpin )
# we only need dewpoint in Fahrenheit
dewpoint_F = toFarenheit (dewpoint)

# stdout gets printed by cron to the log
# print ("ds18b20 T1 {:.2f}".format(ds18b20F))
tempF = ds18b20F
print ("{} T {:.2f}  SLP {:.2f}  Rain {:.2f} Humidity {:.2f}  Dewpoint {:.2f}".format(dts,tempF,slp,dailyrainin,DhtHumidity, dewpoint_F))

# --uncomment quit here to debug--
#quit()

# -- send data to wunderground --

send='/usr/bin/wget "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?
ID=&PASSWORD=&dateutc=now&tempf={:.1f}&baromin={:.2f}&dailyrainin={}&dewptf={:1f}&humidity={}&softwaretype={}&action=updateraw"'.format (tempF, slp,dailyrainin,dewpoint_F,DhtHumidity,program)

os.system(send)

# blow the log file put there by the php program
for x in  glob.glob("/home/pi/update*"):
   os.remove (x)
for x in  glob.glob("/home/pi/Wx/update*"):
   os.remove (x)
