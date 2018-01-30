import logging
import traceback
import urllib
import urllib2

# pushover configuration

API_TOKEN = ""
GROUP_TOKEN = ""


def send_messages(message):
    text_message = "%s" % (message['message'],)
    title = "CFA Alert"
    data=urllib.urlencode({
        "token" : API_TOKEN,
        "user" : GROUP_TOKEN,
        "message" : text_message,
        "title" : title,
    })
    
    response = urllib2.urlopen("https://api.pushover.net/1/messages.json",
                               data=data)
    response_code = response.getcode()
    response_data = response.read()
    if 200 <= response_code < 300:
        return
    logging.info(response_data)

