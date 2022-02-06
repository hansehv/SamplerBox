###############################################################
#   Rudimentary signals via leds
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
import RPi.GPIO as GPIO
import gv

LED_red = gv.cp.getint(gv.cfg,"LED_red".lower())
LED_green = gv.cp.getint(gv.cfg,"LED_green".lower())
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_red,GPIO.OUT)
GPIO.setup(LED_green,GPIO.OUT)
print('Started LEDs via GPIO: Red=%d, Green=%d' %(LED_red,LED_green))

redblink=False
greenblink=False
blinkstage=0
blinkstage1=25
blinkstages=50

def red_on():   GPIO.output(LED_red,GPIO.HIGH)
def red_off():  GPIO.output(LED_red,GPIO.LOW)
def green_on(): GPIO.output(LED_green,GPIO.HIGH)
def green_off():GPIO.output(LED_green,GPIO.LOW)

def blink():
    global blinkstage,blinkstage1
    if blinkstage==0:
        if redblink: red_off()
        if greenblink: green_on()
    elif blinkstage==blinkstage1:
        if redblink: red_on()
        if greenblink: green_off()
    blinkstage+=1
    if blinkstage>blinkstages:
        blinkstage=0
gv.LEDsblink=blink

def setblink(short):
    global blinkstage,blinkstages,blinkstage1
    if short:
        blinkstages=130
        blinkstage1=125
    else:
        blinkstages=30
        blinkstage1=15

def red(on=True,blink=False,short=False):
    global redblink,greenblink
    if on:
        if blink:
            redblink=True
            setblink(short)
        else:
            redblink=False
            red_on()
    else:
        redblink=False
        red_off()
    gv.LEDblink=(redblink or greenblink)

def green(on=True,blink=False,short=False):
    global redblink,greenblink
    if on:
        if blink:
            greenblink=True
            setblink(short)
        else:
            greenblink=False
            green_on()
    else:
        greenblink=False
        green_off()
    gv.LEDblink=(redblink or greenblink)

def signal():
    if gv.ActuallyLoading:      # When loading: blink red with green off
        green(False)
        red(True,True)
    elif len(gv.voicelist)==0:  # When loaded something unplayable: red with blinking green
        red()
        green(True,True)
    else:                       # Otherwise red off and green on
        red(False)
        green()
        # Now check if short blinks should be given for ignored errors
        if gv.ConfigErr: red(True,True,True)
        if gv.DefinitionErr!="": green(True,True,True)
    
