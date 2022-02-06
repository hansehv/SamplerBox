######################################################################
#   The external/GPIO buttons
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
######################################################################

import RPi.GPIO as GPIO
import time,threading
import UI

buttons=[
    [1,"BUT_incr",0],
    [2,"BUT_decr",0],
    [3,"BUT_sel",0],
    [4,"BUT_ret",0]
    ]
numbuttons=0
menubuttons=0

for m in buttons:
    try:
        m[2]=UI.cfg_int(m[1])
        if m[2]>1:      # GPIO 0 and 1 are reserved = don't use
            numbuttons+=1
            if m[0]<5: menubuttons+=1
    except:
        pass

if numbuttons:
    GPIO.setmode(GPIO.BCM)
    comma=""
    message=""
    for m in buttons:
        if m[2]>1:
            try:
                GPIO.setup(m[2], GPIO.IN, pull_up_down=GPIO.PUD_UP)
                message="%s%s %s=%d" %(message,comma,m[1],m[2])
                comma=","
            except:
                print("Invalid button GPIO channel %d" %m[2])
                numbuttons-=1
                if m[0]<5: menubuttons-=1
                m[2]=0
    lastbuttontime = 0

    def Buttons():
        global buttons,lastbuttontime
        lastbuttontime = time.time()
        while True:
            now = time.time()
            if (now-lastbuttontime) > 0.3:
                for m in buttons:
                    if m[2]>1:
                        if not GPIO.input(m[2]):
                            lastbuttontime=time.time()
                            if m[0]<5:
                                UI.menu(m[0],menubuttons)   # contains display logic
                            else:
                                print("create extra button logic here")
                                # optional display with optional lines
                                #UI.display(l2,l3,l4)
                            break
                time.sleep(0.02)        # sleep the loop to give the others cpu time

    ButtonsThread = threading.Thread(target = Buttons)
    ButtonsThread.daemon = True
    ButtonsThread.start()
    print("Started %d GPIO-buttons:%s" %(numbuttons,message))
    
    def stop():
        ButtonsThread.stop()
