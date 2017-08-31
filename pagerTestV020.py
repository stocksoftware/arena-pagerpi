#!/usr/bin/python

import sys
import serial
import urllib
import httplib
import datetime
import random
import time

import config_stuff
from config_stuff import CONFIG, STATUS

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

DEBUG = 1;

port = '/dev/serial0' 
baud = 9600

outFileName = '/home/pi/pagerOut020.txt'

serverURL = "arenatest.nafc.org.au:80"

pager = serial.Serial()
pager.baudrate = baud
pager.port = port

def openSerialPort():
  try:
    pager.open()
  except:
    print "Failed to open ",port

def closeSerialPort():
  pager.close()

def writeToFile(data):
  outFile = open(outFileName, 'a')
  outFile.write(datetime.datetime.now().isoformat())
  outFile.write("\n")
  outFile.write(data)
  outFile.write("\n")
  outFile.close()

def sendToURL(params):
#
# alternative http://docs.python-requests.org/en/master/user/quickstart/#passing-parameters-in-urls
#
  headers = {"content-type": "application/x-www-form-urlencoded", "x-version": CONFIG['xver'], "authorization": CONFIG['auth']}
  conn = httplib.HTTPConnection(CONFIG['serverurl'])
  conn.request("POST", CONFIG['path'], params, headers)
  response = conn.getresponse()
  conn.close()
  if response.reason != 200:
	print "HTTP RESPONSE: ",response.status, response.reason

def getSerialData(data):
  # example
  # ALERT F160104053 WBBG2 G&SC1 GRASS FIRE SPREADING 25 CRYSTAL LANE WAREEK /PORTEOUS RD SVC 6098 C10 (326009) LAT/LON:-37.0088221, 143.6151728 AIRBEN CBOWE CDUNU CMAGH CWBBG [AIRBEN]
  # data = "P 000569192 @@ALERT F151210997 TYLD3 G&SC1 GRASS FIRE SPREADING 1394 TRENTHAM RD KYNETON SOUTH /PREMIER MINE RD SVC 6274 B11 (718696) LAT/LON:-37.2919713, 144.4262171 AIRBEN CCARL CKYNE CTYLD FBD302 [AIRBEN]"
  #
  data = data.strip('\n')   # strip the end of line character
  pieces = data.split(" ")  # break the line in to pieces - some are useful later
  msgType = pieces[2]
  capCode = pieces[1]
  if msgType[:2] == "@@" and "ALERT" in data:   # look for ALERT messages
    config_stuff.STATUS['alert_messages'] += 1
    print "\n"
    capCode = pieces[1]
    cadEvent = pieces[3]
    assignmentArea = pieces[4]
    incType = pieces[5][0:-2]
    responseCode = pieces[5][-1:]
    lBracketIdx = data.rfind(" (") 
    rBracketIdx = data.rfind(") ")     
    dirIdx = data.rfind(" RSSI: ")
    dirRef = dirIdx
    dirType = "Unknown"
    svIdx = data.rfind(" SV")
    if svIdx != -1:
      dirType = "SV" 
      dirIdx = svIdx+1
    melwaysIdx = data.rfind(" M ")
    if melwaysIdx != -1:
      dirType = "Melways" 
      dirIdx = melwaysIdx+1
    dirRef = data[dirIdx:lBracketIdx]
    coords = data[lBracketIdx+2:rBracketIdx]
    geoIdx = data.rfind(" LAT/LON:")
    aircraftMsg = 0
    if geoIdx != -1:
      geoIdx = geoIdx+len(" LAT/LON:")
      delimIdx = data.rfind(", ", geoIdx)
      latitude = data[geoIdx:delimIdx]
      geoIdx = delimIdx
      geoIdx = geoIdx+len(", ")
      delimIdx = data.rfind(" ", geoIdx)
      longitude = data[geoIdx:delimIdx].split(' ', 1)[0]
      aircraftMsg = 1
    else:
      if DEBUG == 1:
        print "NO Geo Coords - going random!"
        latitude = -37.616+random.uniform(-1, 1)
        longitude = 144.420+random.uniform(-1, 1)
        if random.randint(0,9) > 5:
          print "Random aircraft message generated!"
          aircraftMsg = 1
    rssiIdx = data.rfind(" RSSI: ") 
    rssi = data[rssiIdx+7:]
    rssi = rssi.strip()
    lSqBracketIdx = data.rfind(" [") 
    rSqBracketIdx = data.rfind("]")
    resource = "unknown"    
    if lSqBracketIdx != -1 and rSqBracketIdx != -1:
      resource = data[lSqBracketIdx+2:rSqBracketIdx]
    msgStart = data.find(pieces[6]) 
    message = data[msgStart:dirIdx]
    cleanMsg = ''.join(e for e in message if (e.isalnum() or e.isspace() or e=='/'))
    # print decoded data
    print "\a " + bcolors.WARNING
    print datetime.datetime.now().isoformat()
    print " ALERT: %s " % data + bcolors.ENDC
    print "  msgType: %s" % msgType
    print "  capCode: %s" % capCode
    print "  assignmentArea: %s" % assignmentArea
    print "  aircraftMsg: %s" % aircraftMsg
    print "  resource: %s" % resource
    print "  cadEvent: %s" % cadEvent
    print "  incType: %s" % incType
    print "  responseCode: %s" % responseCode 
    print "  directory %s: %s" % (dirType,dirRef)
    print "  coords: %s" % coords
    print "  latitude: %s" % latitude
    print "  longitude: %s" % longitude
    print "  rssi: %s" % rssi
    print "  message: %s" % cleanMsg
    print " "
    # turn decoded data into URL parameters
    params = { 'msgType' : msgType,
               'capCode' : capCode,
               'resource' : resource,
               'aircraftMsg' : aircraftMsg,
               'assignmentArea' : assignmentArea,
               'cadEvent' : cadEvent,
               'incType' : incType,
               'responseCode' : responseCode,
               'dirType' : dirType,
               'dirRef' : dirRef,
               'coords' : coords,
               'lat' : latitude,
               'lon' : longitude,
               'rssi' : rssi,
               'message' : cleanMsg}
    params =  urllib.urlencode(params)    
    sendToURL(params)
	# write data to log file
    writeToFile(params)
    writeToFile(data)
  else:                # non ALERT message
    config_stuff.STATUS['other_messages'] += 1
    sys.stdout.write('.')
    sys.stdout.flush()
#    if capCode > "000200000":
#      cleanData = ''.join(e for e in data if (e.isalnum() or e.isspace() or e=='/'))
#      print ">> %s : %s : %s" % (msgType, capCode, cleanData)
#    else:
#      sys.stdout.write('.')
#      sys.stdout.flush()
	
print "PagerTest Startup v020"
print datetime.datetime.now().isoformat()


def print_error(e):
    print bcolors.WARNING + "ERROR...."
    print datetime.datetime.now().isoformat()
    print e 
    print bcolors.ENDC


def main():
    needs_startup = True
    start_sleep_idx = 0
    start_sleep_intervals = [5, 15, 60]
    while not stop:

        # Connect to the server to report our version and state.
        if needs_startup:
            try:
                config_stuff.startup()
            except Exception as e:
                print_error(e)
                time.sleep(start_sleep_intervals[start_sleep_idx])
                if start_sleep_idx + 1 < len(start_sleep_intervals):
                    start_sleep_idx += 1
                continue
            start_sleep_idx = 0
            needs_startup = False

        if pager.closed:
            openSerialPort()

        # read one line from the pager receiver
        try:
            data = pager.readline()
        except Exception as e:
            print_error(e)
            pager.close()
            time.sleep(5)
            continue

        # parse & handle the data that we read
        try:
            getSerialData(data)
        except Exception as e:
            print_error(e)

        try:
            config_stuff.report()
        except Exception as e:
            needs_startup = True
            print_error(e)
        

if __name__ == '__main__':
    with open(outFileName, 'a') as outFile:
        outFile.write("STARTUP\n")
        outFile.write(datetime.datetime.now().isoformat())
        outFile.write("\n")
        main()
