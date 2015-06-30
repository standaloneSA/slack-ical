#!/usr/bin/python

from icalendar import Calendar
import icalendar
from datetime import datetime
from datetime  import timedelta
import logging
import json

# Import requests and set it up to use cache
import requests
from httpcache import CachingHTTPAdapter
s = requests.Session()
s.mount('http://', CachingHTTPAdapter())
s.mount('https://', CachingHTTPAdapter())
###

cachefile='/tmp/slackical.cache'

slackbotname="MyBotName"
slackwebhookurl="https://hooks.slack.com/services/YOUR/URL/HERE"

channelFeeds = [ 
        {
            'calFeed':    'https://YOUR.ICAL.URL.HERE',
            'channel':    '#channel', 
        },
        {
            'calFeed':    'https://ANOTHER.ICAL.URL.HERE',
            'channel':    '@PRIVATEMESSAGE', 
        },
]



def getFeed( calFeed ):
    message = ""
    date = ""
    headers = { 
        'Cache-Control':    'no-cache',
        'Pragma':           'no-cache',
    }
    
    requests.packages.urllib3.disable_warnings()
    r = requests.get(calFeed, headers=headers)
    
    if r.status_code == 304:
        # read from cached file
        cf=open(cachefile, 'r')
        caldata=cf.read()
    else:
        caldata=r.content
        cf=open(cachefile, 'w')
        cf.write(caldata)
        cf.close()
    
    todayDates=[]
    tomorrowDates=[]
    
    cal = Calendar.from_ical(caldata)
    for event in cal.walk('VEVENT'):
        message=event.get('SUMMARY')
        date=event.get('DTSTART').dt
        if date == datetime.today().date():
            todayDates.append({'Line': message, 'Date': date})
        elif date == datetime.today().date() + timedelta(days=1):
            tomorrowDates.append({'Line': message, 'Date': date})
    return [ todayDates, tomorrowDates ] 
        
def getSlackMessage (todayDates, tomorrowDates):
    message="*Today* (" + datetime.today().strftime("%A") + "):\n"
    if len(todayDates) > 0: 
        for line in todayDates:
            message = message + line['Line']  + "\n"
    else:
        message = message + "_-none-_\n"

    message = message + "*Tomorrow:*\n"
    if len(tomorrowDates) > 0:
        for line in tomorrowDates:
            message = message + line['Line'] + "\n"
    else:
        message = message + "_-none-_\n"
    
    return message

### Begin main 

for feed in channelFeeds: 
    todayDates, tomorrowDates = getFeed(feed['calFeed'])
    message = getSlackMessage(todayDates, tomorrowDates)

    slackMessage={
        'username':     slackbotname,
        'icon_emoji':   ":calculon:",
        'channel':      feed['channel'],
        'text':         message,
    }

    r = requests.post(slackwebhookurl, data=json.dumps(slackMessage))


