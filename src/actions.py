#!/usr/bin/env python

#This is different from AIY Kit's actions
#Copying and Pasting AIY Kit's actions commands will not work

import os
import os.path
import RPi.GPIO as GPIO
import time
import re
import subprocess
import aftership
import urllib2, json


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
#Number of entities in 'var' and 'PINS' should be the same
var = ('kitchen lights', 'bathroom lights', 'bedroom lights')#Add whatever names you want. This is case is insensitive
gpio = (12,13,24)#GPIOS for 'var'. Add other GPIOs that you want

#Number of station names and station links should be the same
stnname=('Radio One', 'Radio 2', 'Radio 3', 'Radio 5')#Add more stations if you want
stnlink=('http://www.radiofeeds.co.uk/bbcradio2.pls', 'http://www.radiofeeds.co.uk/bbc6music.pls', 'http://c5icy.prod.playlists.ihrhls.com/1469_icy', 'http://playerservices.streamtheworld.com/api/livestream-redirect/ARNCITY.mp3')

#IP Address of ESP
ip='xxxxxxxxxxxx'

#Declaration of ESP names
devname=('Device 1', 'Device 2', 'Device 3')
devid=('/Device1', '/Device2', '/Device3')

for pin in gpio:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)

#Servo pin declaration
GPIO.setup(27, GPIO.OUT)
pwm=GPIO.PWM(27, 50)
pwm.start(0)

playshell = None

#Parcel Tracking declarations
#If you want to use parcel tracking, register for a free account at: https://www.aftership.com
#Add the API and uncooment next two lines
#api = aftership.APIv4('AFTERSHIP-API') 
#couriers = api.couriers.all.get()
number = ''
slug=''


#Radio Station Streaming
def radio(phrase):
    for num, name in enumerate(stnname):
        if name.lower() in phrase:
            station=stnlink[num]
            p = subprocess.Popen(["/usr/bin/vlc",station],stdin=subprocess.PIPE,stdout=subprocess.PIPE)

#ESP6266 Devcies control            
def ESP(phrase):
    for num, name in enumerate(devname):
        if name.lower() in phrase:
            dev=devid[num]
            if 'on' in phrase:
                ctrl='=ON'
            elif 'off' in phrase:
                ctrl='=OFF'
            subprocess.Popen(["elinks", ip + dev + ctrl],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
            time.sleep(2)
            subprocess.Popen(["/usr/bin/pkill","elinks"],stdin=subprocess.PIPE)

#Stepper Motor control                    
def SetAngle(angle):
    duty = angle/18 + 2
    GPIO.output(27, True)
    pwm.ChangeDutyCycle(duty)
    time.sleep(1)
    pwm.ChangeDutyCycle(0)
    GPIO.output(27, False)

#Play Youtube Music    
def YouTube(phrase):
    idx=phrase.find('play')
    track=phrase[idx:]
    track=track.replace("'}", "",1)
    track = track.replace('play','',1)
    track=track.strip()
    global playshell
    if (playshell == None):
        playshell = subprocess.Popen(["/usr/local/bin/mpsyt",""],stdin=subprocess.PIPE ,stdout=subprocess.PIPE)
    print("Playing: " + track)
    playshell.stdin.write(bytes('/' + track + '\n1\n','utf-8'))
    playshell.stdin.flush()

def stop():
    pkill = subprocess.Popen(["/usr/bin/pkill","vlc"],stdin=subprocess.PIPE)
   
#Parcel Tracking
def track():
    text=api.trackings.get(tracking=dict(slug=slug, tracking_number=number))
    numtrack=len(text['trackings'])
    print("Total Number of Parcels: " + str(numtrack))
    if numtrack==0:
        parcelnotify=("You have no parcel to track")
        say(parcelnotify)
    elif numtrack==1:
        parcelnotify=("You have one parcel to track")
        say(parcelnotify)
    elif numtrack>1:
        parcelnotify=( "You have " + str(numtrack) + " parcels to track")
        say(parcelnotify)
    for x in range(0,numtrack):
        numcheck=len(text[ 'trackings'][x]['checkpoints'])
        description = text['trackings'][x]['checkpoints'][numcheck-1]['message']
        parcelid=text['trackings'][x]['tracking_number']
        trackinfo= ("Parcel Number " + str(x+1)+ " with tracking id " + parcelid + " is "+ description)
        say(trackinfo)
        time.sleep(10)

#GPIO Device Control
def Action(phrase):
    if 'shut down' in phrase:
        subprocess.Popen(["aplay", "/home/pi/GassistPi/sample-audio-files/Pi-Close.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(10)
        os.system("sudo shutdown -h now")
        #subprocess.call(["shutdown -h now"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if 'servo' in phrase:
        for s in re.findall(r'\b\d+\b', phrase):
            SetAngle(int(s))
    if 'zero' in phrase:
        SetAngle(0)
    else:
        for num, name in enumerate(var):
            if name.lower() in phrase:
                pinout=gpio[num]
                if 'on' in phrase:
                    GPIO.output(pinout, 1)
                    subprocess.Popen(["aplay", "/home/pi/GassistPi/sample-audio-files/Device-On.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                elif 'off' in phrase:
                    GPIO.output(pinout, 0)
                    subprocess.Popen(["aplay", "/home/pi/GassistPi/sample-audio-files/Device-Off.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
