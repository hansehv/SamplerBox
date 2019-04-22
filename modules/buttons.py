###############################################################
#   The three external buttons
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
import RPi.GPIO as GPIO
import time,threading
import gv

BUT_incr = gv.cp.getint(gv.cfg,"BUT_incr".lower())
BUT_decr = gv.cp.getint(gv.cfg,"BUT_decr".lower())
BUT_sel  = gv.cp.getint(gv.cfg,"BUT_sel".lower())

lastbuttontime = 0
buttfunc = 0
button_functions=["","Volume","Midichannel","RenewUSB/MidMute","Play Chord:","Use Scale:"]
button_disp=["","V","M","X","C","S"]  # take care, these values can used elsewhere for testing

def Button_display():
    global buttfunc, button_functions
    function_value=[""," %d%%"%(gv.volume)," %d"%(gv.MIDI_CHANNEL),""," %s"%(gv.chordname[gv.currchord])," %s"%(gv.scalename[gv.currscale])]
    gv.display(button_functions[buttfunc]+function_value[buttfunc])

def Buttons():
    global lastbuttontime, buttfunc, button_functions, BUT_incr, BUT_decr, BUT_sel, button_disp

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUT_incr, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUT_decr, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUT_sel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    lastbuttontime = time.time()
    print 'Started buttons via GPIO: Increment=%d, Decrement=%d, Select=%d' %(BUT_incr,BUT_decr,BUT_sel)

    while True:
        now = time.time()
        if (now - lastbuttontime) > 0.2:
            if not GPIO.input(BUT_decr):
                lastbuttontime = now
                if buttfunc==0:
                    x=gv.getindex(gv.PRESET,gv.presetlist)-1
                    if x<0: x=len(gv.presetlist)-1
                    gv.PRESET=gv.presetlist[x][0]
                    gv.LoadSamples()
                elif buttfunc==1:
                    gv.volume-=5
                    if gv.volume<0: gv.volume=0
                    gv.setvolume(gv.volume)
                    Button_display()
                elif buttfunc==2:
                    gv.MIDI_CHANNEL -= 1
                    if gv.MIDI_CHANNEL < 1: gv.MIDI_CHANNEL = 16
                    Button_display()
                elif buttfunc==3:
                    if not gv.midi_mute:
                        gv.midi_mute = True
                        gv.display("** MIDI muted **")
                    else:
                        gv.midi_mute = False
                        Button_display()
                elif buttfunc==4:
                    gv.currscale=0     # scale and chord mode are mutually exclusive
                    gv.currchord -= 1
                    if gv.currchord<0: gv.currchord=len(gv.chordname)-1
                    Button_display()
                elif buttfunc==5:
                    gv.currchord=0     # scale and chord mode are mutually exclusive
                    gv.currscale-=1
                    if gv.currscale<0: gv.currscale=len(gv.scalename)-1
                    Button_display()

            elif not GPIO.input(BUT_incr):
                lastbuttontime = now
                gv.midi_mute = False
                if buttfunc==0:
                    x=gv.getindex(gv.PRESET,gv.presetlist)+1
                    if x>=len(gv.presetlist): x=0
                    gv.PRESET=gv.presetlist[x][0]
                    gv.LoadSamples()      
                elif buttfunc==1:
                    gv.volume+=5
                    if gv.volume>100: gv.volume=100
                    gv.setvolume(gv.volume)
                    Button_display()
                elif buttfunc==2:
                    gv.MIDI_CHANNEL += 1
                    if gv.MIDI_CHANNEL > 16: gv.MIDI_CHANNEL = 1
                    Button_display()
                elif buttfunc==3:
                    gv.basename = "None"
                    gv.LoadSamples()
                    #Button_display()   # loadsamples also displays
                elif buttfunc==4:
                    gv.currscale=0      # scale and chord mode areLoadSamples mutually exclusive
                    gv.currchord += 1
                    if gv.currchord>=len(gv.chordname): gv.currchord=0
                    Button_display()
                elif buttfunc==5:
                    gv.churrchord=0     # scale and chord mode are mutually exclusive
                    gv.currscale += 1
                    if gv.currscale>=len(gv.scalename): gv.currscale=0
                    Button_display()

            elif not GPIO.input(BUT_sel):
                lastbuttontime = now
                buttfuncmax=len(button_functions)
                buttfunc +=1
                if buttfunc >= len(button_functions): buttfunc=0
                if not gv.USE_ALSA_MIXER:
                    if button_disp[buttfunc]=="V": buttfunc +=1
                #use if above gets complex: if buttfunc >= len(button_functions): buttfunc=0
                gv.midi_mute = False
                Button_display()

            time.sleep(0.02)

ButtonsThread = threading.Thread(target = Buttons)
ButtonsThread.daemon = True
ButtonsThread.start()
