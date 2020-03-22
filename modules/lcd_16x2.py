###########################################################################
##   HD44780 class, based on 16x2 LCD interface code by Rahul Kar, see:
##   http://www.rpiblog.com/2012/11/interfacing-16x2-lcd-with-raspberry-pi.html
##
##   SamplerBox extended by HansEhv (https://github.com/hansehv)
##   Supports 2 line GPIO version only in current version
##   If it receives line 3 or 4 it will override line 1 or 3 respectively
##
##   Some devices are reported to intermittently show weird characters
##   So did mine, anomalies disappeared with a heavier power adapter
##   ...bad quality using extensive power?? ... mine was very cheap ...
##
###########################################################################
import RPi.GPIO as GPIO
import time
import UI
usleep = lambda x: time.sleep(x/1000000.0)
msleep = lambda x: time.sleep(x/1000.0)
LCD_RS = UI.cfg_int("LCD_RS")
LCD_E = UI.cfg_int("LCD_E")
# get&insert LCD_D0 to LCD_D3 as first elements in pins_db for 8-bit operation
LCD_D4 = UI.cfg_int("LCD_D4")
LCD_D5 = UI.cfg_int("LCD_D5")
LCD_D6 = UI.cfg_int("LCD_D6")
LCD_D7 = UI.cfg_int("LCD_D7")

class HD44780:

    def __init__(self, pin_rs=LCD_RS, pin_e=LCD_E, pins_db=[LCD_D4,LCD_D5,LCD_D6,LCD_D7]):
        self.pin_rs=pin_rs
        self.pin_e=pin_e
        self.pins_db=pins_db
        self.bits=len(pins_db)
        if  not (self.bits==4 or self.bits==8):
            print "HD44780: use/define exactly 4 or 8 datapins"
            exit(1)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_e, GPIO.OUT)
        GPIO.setup(self.pin_rs, GPIO.OUT)
        for pin in self.pins_db:
            GPIO.setup(pin, GPIO.OUT)
        self.clear()
        self.busy=False
        print 'Started 16x2 LCD via GPIO: RegisterSelect=%d, Enable=%d and Datalines=%s' %(pin_rs, pin_e, str(pins_db).replace(" ", ""))

    def clear(self):
        """ Blank / Reset LCD """
        self.cmd(0x33) # Initialization by instruction
        msleep(5)
        self.cmd(0x33)
        usleep(100)
        if self.bits==4:
            self.cmd(0x32) # set to 4-bit mode
            self.cmd(0x28) # Function set: 4-bit mode, 2 lines
        else:
            self.cmd(0x38) # Function set: 8-bit mode, 2 lines
        self.cmd(0x0C) # Display control: Display on, cursor off, cursor blink off
        self.cmd(0x06) # Entry mode set: Cursor moves to the right
        self.cmd(0x01) # Clear Display: Clears the display & set cursor position to line 1 column 0
        
    def cmd(self, bits, char_mode=0):
        """ Send command to LCD """
        time.sleep(0.001)
        bits=bin(bits)[2:].zfill(8)
        GPIO.output(self.pin_rs, char_mode)
        for pin in self.pins_db:
            GPIO.output(pin, 0)
        for i in range(self.bits):
            if bits[i] == "1":
                GPIO.output(self.pins_db[::-1][i], 1)
        self.toggle_enable()
        if self.bits==4:
            for pin in self.pins_db:
                GPIO.output(pin, 0)
            for i in range(4,8):
                if bits[i] == "1":
                    GPIO.output(self.pins_db[::-1][i-4], 1)
            self.toggle_enable()

    def toggle_enable(self):
        """ Pulse the enable flag to process data """
        GPIO.output(self.pin_e, 0)
        usleep(1)      # command needs to be > 450 nsecs to settle
        GPIO.output(self.pin_e, 1)
        usleep(1)      # command needs to be > 450 nsecs to settle
        GPIO.output(self.pin_e, 0)
        usleep(100)    # command needs to be > 37 usecs to settle

    def displayline(self,s):
        l=("%s%s"%(s," "*16))[:16]
        for c in l: self.cmd(ord(c),1)

    def display(self,l2,l3='',l4=''):
        if self.busy: return False
        self.busy=True
        s1=""
        s2=""
        if l3=='':
            vol=" %d%%" %UI.SoundVolume() if UI.USE_ALSA_MIXER else ""
            s1 = "%s%s %s%s" % (UI.Scalename()[UI.Scale()], UI.Chordname()[UI.Chord()], UI.Mode(), vol)
        else: s1=l3
        if l4=="":
            if l2=="":
                if UI.Voice()>1: s2=str(UI.Voice())+":"
                if UI.Presetlist()!=[]: s2 += UI.Presetlist()[UI.getindex(UI.Preset(),UI.Presetlist())][1]
            else: s2=l2
        else: s2=l4
        self.cmd(0x02)  # go home first
        self.displayline(s1)
        self.cmd(0xC0) # next line
        self.displayline(s2)
        self.busy=False
        return True
