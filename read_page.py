import sys
import random
from datetime import datetime


def handle_serial_data(app, pager_message):
    alert = read_alert_message(app, pager_message)
    if alert:
        if app.verbose:
            show_alert_message(pager_message, alert)
        else:
            print 'alert message: %r' % (alert['message'],)
        app.on_alert_message(alert)
    else:
        app.status['other_messages'] += 1
        print 'other message: %r' % (pager_message,)


def read_alert_message(app, data):
  data = data.strip('\n')   # strip the end of line character
  pieces = data.split(" ")  # break the line in to pieces - some are useful later
  if len(pieces) < 6:
      # if we don't have six individual words it can't be an alert message
      return
  msgType = pieces[2]
  capCode = pieces[1]
  if msgType[:2] == "@@" and "ALERT" in data:   # look for ALERT messages
    app.status['alert_messages'] += 1
    if app.verbose:
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
      if app.debug == 1:
        if app.verbose:
            print "NO Geo Coords - going random!"
        latitude = -37.616+random.uniform(-1, 1)
        longitude = 144.420+random.uniform(-1, 1)
        if random.randint(0,9) > 5:
          if app.verbose:
              print "Random aircraft message generated!"
          aircraftMsg = 1
      else:
          latitude = longitude = None
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
    cleanMsg = ''.join(e for e in message
                       if (e.isalnum() or e.isspace() or e=='/'))
    return {
        'msgType' : msgType,
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
        'message' : cleanMsg,
    }

def show_alert_message(message):
    print "\a " + bcolors.WARNING
    print datetime.datetime.now().isoformat()
    print " ALERT: %s " % messages['cleanMsg'] + bcolors.ENDC
    print "  msgType: %s" % message['msgType']
    print "  capCode: %s" % message['capCode']
    print "  assignmentArea: %s" % message['assignmentArea']
    print "  aircraftMsg: %s" % message['aircraftMsg']
    print "  resource: %s" % message['resource']
    print "  cadEvent: %s" % message['cadEvent']
    print "  incType: %s" % message['incType']
    print "  responseCode: %s" % message['responseCode'] 
    print "  directory %s: %s" % (message['dirType'], message['dirRef'])
    print "  coords: %s" % message['coords']
    print "  latitude: %s" % message['lat']
    print "  longitude: %s" % message['lon']
    print "  rssi: %s" % message['rssi']
    print "  message: %s" % message['cleanMsg']
    print " "
