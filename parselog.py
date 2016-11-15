#!/usr/bin/python2
# parse log file
# 24aug16
# -- couple of simple methids here
# spec: allow comments starting with #. ignore comments from the hash right
# fields are space delimited
# each log line is parsed using a split function

def inMemoryLogFileRead():
  theFile = open( logfile ,'r')
  FILE = theFile.readlines()
  theFile.close()
  printList = []
  for line in FILE:
     li = line.strip()
     if not li.startswith("#"):
        print line    # or write it to another file... or whatever

def readLog(logfile):
  with open(logfile,'r') as f:
      for line in f:
       # get rid of everything to the right of the comment hash #
       line = line.partition ('#')[0]
       line = line.rstrip()
       if line.strip():    # process only data lines
         dat = line.split()
         # only process records with more than 6 elements
         if (len(dat) > 6):
           #print "t ",dat[3]," p ",dat[5]," r ",dat[7]
           date = dat[0]
           time = dat[1]
           t = dat[3]
           p = dat[5]
           r = dat[7]
  f.close()
  # return the last values in the file
  return (date,time,t,p,r)

# ---------------------------------------------------------------
# run readLog
logfile = "pws.log"
(date,time,t,p,r) = readLog( logfile )
print  date," ",time," t ",t," p ",p," r ",r
