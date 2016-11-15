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
import RPi.GPIO as GPIO

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

dhtGPIOvdd = 6  # LOOK
CORRECTION = 12

def toFarenheit (tC):
  return( tC * 9/5.0 + 32)

def DHT(dhtSensorType,dhtGPIOpin):
  # temperatures are deg Celcius
  GPIO.setmode(GPIO.BCM)
  GPIO.setwarnings(False)
  GPIO.setup(dhtGPIOvdd,GPIO.OUT)
  GPIO.output(dhtGPIOvdd,GPIO.HIGH)
  print("Turn on DHT sensor")
  time.sleep(1)

  humidity, temperature = Adafruit_DHT.read_retry(dhtSensorType, dhtGPIOpin)
  humidity +=  CORRECTION  # Correction to Aiea ...  DHT is really way off

  if humidity > 100:
      time.sleep(2)
      (humidity, dewpoint, temperature) = DHT(dhtSensorType,dhtGPIOpin )
      humidity +=  CORRECTION  # Correction to Aiea ...  DHT is really way off

  dewpoint =243.04*(math.log(humidity/100)+((17.625*temperature)/(243.04+temperature)))/(17.625-math.log(humidity/100)-((17.625*temperature)/(243.04+temperature)))

  GPIO.output(dhtGPIOvdd,GPIO.LOW)  # LOOK Turn off sensor
  print("Turn off DHT sensor")
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
  lastline = "lastline"

  with open(logfile,'r') as f:
      for line in f:
       # get rid of everything to the right of the comment hash #
       lastline = line
       line = line.partition ('#')[0]
       line = line.rstrip()
       if line.strip():    # process only data lines
         dat = line.split()
         if (len(dat) >= 1):  # LOOK -- really ? kindof clumsy
           lastrain = dat[0]

  f.close()
  # return the last values in the file

  return (lastrain, lastline)

logfile = '/home/pi/Wx/rainobsv.txt'
(rain,rainobsvtext) = readLog( logfile)

dailyrainin = float (rain)

# Initialise the BMP085 and use STANDARD mode (default value)

bmp = BMP085.BMP085()

bmpTempC = bmp.read_temperature()
bmpTempF = bmpTempC * 9/5 + 32
# I see a temp of 209 posted ... if temp > 100 retake it!

lowcount = 0
highcount = 0
while bmpTempF > 100 or bmpTempF < 60 :
  print("bmpTempF QA fail {:.2f} : resample ".format (bmpTempF))
  bmpTempF = bmp.read_temperature() * 9/5 + 32
  if bmpTempF > 100 :
        highcount += 1
        if highcount > 3:
                break
  if bmpTempF < 60 :
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
(ds18b20C1,ds18b20F1)= ds18b20(1)
(ds18b20C0,ds18b20F0)= ds18b20(0)

(DhtHumidity, DhtDewpointC, DhtTemperatureC) = DHT(dhtSensorType,dhtGPIOpin )

# we only need dewpoint in Fahrenheit
DhtDewpointF = toFarenheit (DhtDewpointC)
DhtTemperatureF= toFarenheit (DhtTemperatureC)

# stdout gets printed by cron to the log
# print ("ds18b20 T1 {:.2f}".format(ds18b20F))

print ("DHT     {} T  {:.2f} Humidity {:.2f} Correction {}  Dewpoint {:.2f}".format
(dts,DhtTemperatureF, DhtHumidity, CORRECTION,  DhtDewpointF))

print ("BMP180  {} T  {:.2f} F    SLP {:.2f}".format (dts,bmpTempF,slp))

print ("ds18b20 {} T0 {:.2f} F    T1  {:.2f} F".format
(dts,ds18b20F0, ds18b20F1))

print ("rain    {} >> {}".format( rain, rainobsvtext))


# ---BME280 functions that are elsewhere---

print "BME280 \n";
sys.path.append(os.path.abspath("/home/pi/BME280"))
import bme280lib as bme

(chip_id, chip_version) = bme.readBME280ID()
print "Chip ID     :", chip_id
print "Version     :", chip_version

temperature,pressure,humidity = bme.readBME280All()
elev_meters = 133
elev_feet = elev_meters * 39.370/12

# from the bmp85 library

mmHg = pressure/1.33322
mb = pressure
mmIn = mb * 0.02953
sealevel_mb = mb / pow(1.0 - elev_meters/44330.0, 5.255)
sealevel_In = sealevel_mb * 0.02953

print('Elevation -default : {:.1f} m {:.1f} f'.format ( elev_meters , elev_feet)) # no work
#print('Elevation -default : {:6.1f} {:6.1f}'.format ( elev_meters , elev_feet))

print ("Temperature : {:.1f} C".format (temperature))
bmeTempF = temperature * 9/5 + 32
print ("Temperature : {:.1f} F".format (bmeTempF))
#print "Temperature : ", bmeTempF, "F"
print ("Pressure : {:.0f} mb".format (pressure))
print ("Pressure : {:.0f} mm Hg".format (mmHg))
print ("Pressure : {:.2f} in Hg".format (mmIn))

print ("SLPPressure : {:.2f} in".format (sealevel_In))
print ("SLPPressure : {} mb".format (int(sealevel_mb)))

#print "Pressure : ", pressure, "mb"
#print "Pressure : ", mmHg, "mm Hg"
#print "Pressure : ", mmIn, "in Hg"

#print "SLP Pressure: ", sealevel_In, " in"
#print "SLP Pressure: ", sealevel_mb, " mb"
#print "Humidity : ", humidity, "%"
