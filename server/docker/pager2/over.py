import logging
import traceback
import urllib
import urllib2

def send_messages(config, message):
    text_message = "%s" % (message['message'],)
    title = "CFA Alert"
    data=urllib.urlencode({
        "token" : config.get_config('api_token'),
        "user" : config.get_config('group_token'),
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

