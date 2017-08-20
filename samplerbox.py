#
#  SamplerBox 
#
#  author:    Joseph Ernest (twitter: @JosephErnest, mail: contact@samplerbox.org)
#  url:       http://www.samplerbox.org/
#  license:   Creative Commons ShareAlike 3.0 (http://creativecommons.org/licenses/by-sa/3.0/)
#
#  samplerbox.py: Main file
#
#   June 19th 2015 version extended by https://www.facebook.com/hanshom
#                          see docs at  http://homspace.xs4all.nl?start=samplerbox
#       - Play samples in playback mode (ignoring normal note-off),
#         driven by "mode=keyb|once|on64|loop" in definition.txt, default=once
#       - filter the midi channel (see LOCAL CONFIG below)
#       - Presets 1-16 iso 0-15, so the preset/folder name and program change number correspond
#       - Replaced 7segment display code by 16x2LCD
#       - Use 3 buttons: one for choosing functions and two other for +/-.
#         functions: preset, channel, volume, transpose, renewUSB/MidiMute.



#########################################
##  LOCAL  
##  CONFIG
#########################################

AUDIO_DEVICE_ID = 2                     # change this number to use another soundcard, default=0
AUDIO_DEVICE_OUT = "Speaker"            # change this name according soundcard, default="PCM"
SAMPLES_DIR = "/media/"                 # The root directory containing the sample-sets. Example: "/media/" to look for samples on a USB stick / SD card
USE_SERIALPORT_MIDI = False             # Set to True to enable MIDI IN via SerialPort (e.g. RaspberryPi's GPIO UART pins)
USE_HD44780_16x2_LCD = True             # Set to True to use a HD44780 based 16x2 LCD
USE_BUTTONS = True                      # Set to True to use momentary buttons (connected to RaspberryPi's GPIO pins) to change preset
MAX_POLYPHONY = 80                      # This can be set higher, but 80 is a safe value
MIDI_CHANNEL = 11                       # midi channel
PLAYBACK = "Once"                       # ignores loop markers and note-off ("just play the sample")
PLAYSTOP = "On64"                       # ignores loop markers with note-off by note+64 ("just play the sample with option to stop")
PLAYLOOP = "Loop"                       # recognize loop markers, note-off by note+64 ("just play the loop with option to stop")
PLAYLIVE = "Keyb"                       # reacts on "keyboard" interaction
sample_mode = PLAYBACK                  # we need a default...

preset = 1
midi_mute = False


#########################################
##  IMPORT 
##  MODULES
#########################################

import wave
import time
usleep = lambda x: time.sleep(x/1000000.0)
msleep = lambda x: time.sleep(x/1000.0)
import numpy
import os, re
import pyaudio
import threading   
from chunk import Chunk
import struct
import rtmidi_python as rtmidi
import samplerbox_audio


#########################################
##  based on 16x2 LCD interface code by Rahul Kar, see:
##  http://www.rpiblog.com/2012/11/interfacing-16x2-lcd-with-raspberry-pi.html
#########################################

class HD44780:

    #def __init__(self, pin_rs=7, pin_e=8, pins_db=[25,24,22,23,27,17,18,4]):
    def __init__(self, pin_rs=7, pin_e=8, pins_db=[27,17,18,4]):
                                                #remove first 4 elements for 4-bit operation
                                                #and mind the physical wiring !
        self.pin_rs=pin_rs
        self.pin_e=pin_e
        self.pins_db=pins_db

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_e, GPIO.OUT)
        GPIO.setup(self.pin_rs, GPIO.OUT)
        for pin in self.pins_db:
            GPIO.setup(pin, GPIO.OUT)

        self.clear()

    def clear(self):
        """ Blank / Reset LCD """
        
        self.cmd(0x33) # Initialization by instruction
        msleep(5)
        self.cmd(0x33)
        usleep(100)
        self.cmd(0x32) # set to 4-bit mode
        self.cmd(0x28) # Function set: 4-bit mode, 2 lines
        #self.cmd(0x38) # Function set: 8-bit mode, 2 lines
        self.cmd(0x0C) # Display control: Display on, cursor off, cursor blink off
        self.cmd(0x06) # Entry mode set: Cursor moves to the right
        self.cmd(0x01) # Clear Display: Clears the display & set cursor position to line 1 column 0
        
    def cmd(self, bits, char_mode=False):
        """ Send command to LCD """

        sleep(0.001)
        bits=bin(bits)[2:].zfill(8)

        GPIO.output(self.pin_rs, char_mode)

        for pin in self.pins_db:
            GPIO.output(pin, False)

        #for i in range(8):       # use range 4 for 4-bit operation
        for i in range(4):       # use range 4 for 4-bit operation
            if bits[i] == "1":
                GPIO.output(self.pins_db[::-1][i], True)

        GPIO.output(self.pin_e, True)
        usleep(1)      # command needs to be > 450 nsecs to settle
        GPIO.output(self.pin_e, False)
        usleep(100)    # command needs to be > 37 usecs to settle

        """ 4-bit operation start """
        for pin in self.pins_db:
            GPIO.output(pin, False)

        for i in range(4,8):
            if bits[i] == "1":
                GPIO.output(self.pins_db[::-1][i-4], True)

        GPIO.output(self.pin_e, True)
        usleep(1)      # command needs to be > 450 nsecs to settle
        GPIO.output(self.pin_e, False)
        usleep(100)    # command needs to be > 37 usecs to settle
        """ 4-bit operation end """

    def message(self, text):
        """ Send string to LCD. Newline wraps to second line"""

        self.cmd(0x01) # Clear Display: Clears the display & set cursor position to line 1 column 0
        x = 0
        for char in text:
            if char == '\n':
                self.cmd(0xC0) # next line
                x = 0
            else:
                x += 1
                if x < 17: self.cmd(ord(char),True)


#########################################
##  SLIGHT MODIFICATION OF PYTHON'S WAVE MODULE
##  TO READ CUE MARKERS & LOOP MARKERS if in live mode
#########################################

class waveread(wave.Wave_read):
    def initfp(self, file):
        self._convert = None
        self._soundpos = 0
        self._cue = []
        self._loops = []
        self._ieee = False
        self._file = Chunk(file, bigendian=0)
        if self._file.getname() != 'RIFF':
            raise Error, 'file does not start with RIFF id'
        if self._file.read(4) != 'WAVE':
            raise Error, 'not a WAVE file'
        self._fmt_chunk_read = 0
        self._data_chunk = None
        while 1:
            self._data_seek_needed = 1
            try:
                chunk = Chunk(self._file, bigendian=0)
            except EOFError:
                break
            chunkname = chunk.getname()
            if chunkname == 'fmt ':
                self._read_fmt_chunk(chunk)
                self._fmt_chunk_read = 1
            elif chunkname == 'data':
                if not self._fmt_chunk_read:
                    raise Error, 'data chunk before fmt chunk'
                self._data_chunk = chunk
                self._nframes = chunk.chunksize // self._framesize
                self._data_seek_needed = 0
            elif chunkname == 'cue ':
                numcue = struct.unpack('<i',chunk.read(4))[0]
                for i in range(numcue): 
                  id, position, datachunkid, chunkstart, blockstart, sampleoffset = struct.unpack('<iiiiii',chunk.read(24))
                  self._cue.append(sampleoffset)
            elif chunkname == 'smpl':
                manuf, prod, sampleperiod, midiunitynote, midipitchfraction, smptefmt, smpteoffs, numsampleloops, samplerdata = struct.unpack('<iiiiiiiii',chunk.read(36))
                for i in range(numsampleloops):
                   cuepointid, type, start, end, fraction, playcount = struct.unpack('<iiiiii',chunk.read(24)) 
                   self._loops.append([start,end]) 
            chunk.skip()
        if not self._fmt_chunk_read or not self._data_chunk:
            raise Error, 'fmt chunk and/or data chunk missing'

    def getmarkers(self):
        return self._cue
        
    def getloops(self):
        if sample_mode == PLAYLIVE or sample_mode == PLAYLOOP:
            return self._loops


#########################################
##  MIXER CLASSES
#########################################

class PlayingSound:
    def __init__(self, sound, note):
        self.sound = sound
        self.pos = 0
        self.fadeoutpos = 0
        self.isfadeout = False
        self.note = note

    def fadeout(self, i):
        self.isfadeout = True
        
    def stop(self):
        try: playingsounds.remove(self) 
        except: pass

class Sound:
    def __init__(self, filename, midinote, velocity):
        wf = waveread(filename)
        self.fname = filename
        self.midinote = midinote
        self.velocity = velocity
        if wf.getloops(): 
            self.loop = wf.getloops()[0][0]
            self.nframes = wf.getloops()[0][1] + 2
        else:
            self.loop = -1
            self.nframes = wf.getnframes()

        self.data = self.frames2array(wf.readframes(self.nframes), wf.getsampwidth(), wf.getnchannels())

        wf.close()            

    def play(self, note):
        snd = PlayingSound(self, note)
        playingsounds.append(snd)
        return snd

    def frames2array(self, data, sampwidth, numchan):
        if sampwidth == 2:
            npdata = numpy.fromstring(data, dtype = numpy.int16)
        elif sampwidth == 3:
            npdata = samplerbox_audio.binary24_to_int16(data, len(data)/3)
        if numchan == 1: 
            npdata = numpy.repeat(npdata, 2)
        return npdata

FADEOUTLENGTH = 30000
FADEOUT = numpy.linspace(1., 0., FADEOUTLENGTH)            # by default, float64
FADEOUT = numpy.power(FADEOUT, 6)
FADEOUT = numpy.append(FADEOUT, numpy.zeros(FADEOUTLENGTH, numpy.float32)).astype(numpy.float32)
SPEED = numpy.power(2, numpy.arange(0.0, 84.0)/12).astype(numpy.float32)

samples = {}
playingnotes = {}
sustainplayingnotes = []
sustain = False
playingsounds = []
globaltranspose = 0

#########################################
##  AUDIO AND MIDI CALLBACKS
#########################################

def AudioCallback(in_data, frame_count, time_info, status):
    global playingsounds
    rmlist = []
    playingsounds = playingsounds[-MAX_POLYPHONY:]    
    b = samplerbox_audio.mixaudiobuffers(playingsounds, rmlist, frame_count, FADEOUT, FADEOUTLENGTH, SPEED)
    for e in rmlist:
        try: playingsounds.remove(e)
        except: pass
    odata = (b.astype(numpy.int16)).tostring()   
    return (odata, pyaudio.paContinue)


def MidiCallback(message, time_stamp):
    global playingnotes, sustain, sustainplayingnotes
    global preset, sample_mode, midi_mute
    ## print 'MidiCallBack called' #debug
    messagetype = message[0] >> 4
    messagechannel = (message[0] & 15) + 1
    if (messagechannel == MIDI_CHANNEL) and (midi_mute == False):
        note = message[1] if len(message) > 1 else None
        midinote = note
        velocity = message[2] if len(message) > 2 else None
        noteoff = False
        if sample_mode == PLAYLIVE: noteoff = True

        if messagetype == 9 and velocity == 0: messagetype = 8
        if (sample_mode == PLAYSTOP or sample_mode == PLAYLOOP) and messagetype == 9 and midinote > 63:
            messagetype = 8
            midinote = midinote - 64
            noteoff = True

        if messagetype == 9:    # Note on
            midinote += globaltranspose
            print 'Note on ' + str(note) + '->' + str(midinote) + ' in ' + sample_mode #debug
            try:
              playingnotes.setdefault(midinote,[]).append(samples[midinote, velocity].play(midinote))
            except:
              pass

        elif messagetype == 8:  # Note off
            midinote += globaltranspose
            if noteoff == True:
                print 'Note off ' + str(note) + '->' + str(midinote)    #debug
                if midinote in playingnotes:
                    for n in playingnotes[midinote]: 
                        if sustain:
                            sustainplayingnotes.append(n)
                        else:
                            n.fadeout(50)
                    playingnotes[midinote] = []

        elif messagetype == 12: # Program change
            note = note + 1     # make it human
            print 'Program change ' + str(note)
            preset = note
            LoadSamples()

        elif (messagetype == 11) and (note == 64) and (velocity < 64) and (sample_mode == PLAYLIVE): # sustain pedal off
            for n in sustainplayingnotes:
                n.fadeout(50)
            sustainplayingnotes = []       
            sustain = False

        elif (messagetype == 11) and (note == 64) and (velocity >= 64) and (sample_mode == PLAYLIVE): # sustain pedal on
            sustain = True


import subprocess
volume = 100
def getvolume():
    global volume
    p = subprocess.Popen(["amixer","-c%d" % AUDIO_DEVICE_ID,"get","%s,0" % AUDIO_DEVICE_OUT], stdout=subprocess.PIPE)
    out = p.stdout.read()
    pos1=out.find("[")
    pos2=out.find("]")
    volume=int(out[pos1+1:pos2-1])
getvolume()

#########################################
##  LOAD SAMPLES
#########################################

LoadingThread = None            
LoadingInterrupt = False

def LoadSamples():
    global LoadingThread
    global LoadingInterrupt

    if LoadingThread:
        LoadingInterrupt = True
        LoadingThread.join()
        LoadingThread = None
    
    LoadingInterrupt = False
    LoadingThread = threading.Thread(target = ActuallyLoad)
    LoadingThread.daemon = True
    LoadingThread.start()

NOTES = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]

basename = "None"

def ActuallyLoad():    
    global preset
    global samples
    global playingsounds
    global globaltranspose, sample_mode, basename
    mode=[]
    playingsounds = []
    samples = {}
    currbase = basename    
    basename = next((f for f in os.listdir(SAMPLES_DIR) if f.startswith("%d " % preset)), None)      # or next(glob.iglob("blah*"), None)
    globaltranspose = 0
    if basename:
        if basename ==  currbase:
            print 'Kept preset %s' % basename
            display("Kept %s" % basename)
            return
        dirname = os.path.join(SAMPLES_DIR, basename)
    if not basename: 
        print 'Preset empty: %s' % preset
        basename = "%d Empty preset" %preset
        display("")
        return
    print 'Preset loading: %s ' % basename
    display("Loading %s" % basename)
    definitionfname = os.path.join(dirname, "definition.txt")
    if os.path.isfile(definitionfname):
        with open(definitionfname, 'r') as definitionfile:
            for i, pattern in enumerate(definitionfile):
                try:
                    if r'%%volume' in pattern:        # %%parameters are global parameters
                        volume = int(pattern.split('=')[1].strip())
                        p = subprocess.Popen(["amixer","-c%d" % AUDIO_DEVICE_ID,"set","%s,0" % AUDIO_DEVICE_OUT,str(volume)+"%"], stdout=subprocess.PIPE)
                        getvolume()
                        continue
                    if r'%%transpose' in pattern:
                        globaltranspose = int(pattern.split('=')[1].strip())
                        continue
                    if r'%%mode' in pattern:        # %%parameters are global parameters
                        mode = pattern.split('=')[1].strip().title()
                        if mode == PLAYBACK or mode == PLAYLIVE or mode == PLAYSTOP or mode == PLAYLOOP: sample_mode = mode
                        print 'sample mode = ' + sample_mode
                        continue
                    defaultparams = { 'midinote': '0', 'velocity': '127', 'notename': '' }
                    if len(pattern.split(',')) > 1:
                        defaultparams.update(dict([item.split('=') for item in pattern.split(',', 1)[1].replace(' ','').replace('%', '').split(',')]))
                    pattern = pattern.split(',')[0]
                    pattern = re.escape(pattern.strip())
                    pattern = pattern.replace(r"\%midinote", r"(?P<midinote>\d+)").replace(r"\%velocity", r"(?P<velocity>\d+)")\
                                     .replace(r"\%notename", r"(?P<notename>[A-Ga-g]#?[0-9])").replace(r"\*", r".*?").strip()    # .*? => non greedy
                    for fname in os.listdir(dirname):
                        if LoadingInterrupt: 
                            return
                        m = re.match(pattern, fname)
                        if m:
                            info = m.groupdict()
                            midinote = int(info.get('midinote', defaultparams['midinote']))
                            velocity = int(info.get('velocity', defaultparams['velocity']))
                            notename = info.get('notename', defaultparams['notename'])
                            if notename: midinote = NOTES.index(notename[:-1].lower()) + (int(notename[-1])+2) * 12
                            samples[midinote, velocity] = Sound(os.path.join(dirname, fname), midinote, velocity)
                except:
                    print "Error in definition file, skipping line %s." % (i+1)

    else:
        for midinote in range(0, 127): 
            if LoadingInterrupt: 
                return
            file = os.path.join(dirname, "%d.wav" % midinote)
            if os.path.isfile(file):
                samples[midinote, 127] = Sound(file, midinote, 127)             

    initial_keys = set(samples.keys())
    for midinote in xrange(128):
        lastvelocity = None
        for velocity in xrange(128):
            if (midinote, velocity) not in initial_keys:
                samples[midinote, velocity] = lastvelocity
            else: 
                if not lastvelocity: 
                    for v in xrange(velocity): samples[midinote, v] = samples[midinote, velocity]
                lastvelocity = samples[midinote, velocity]
        if not lastvelocity: 
            for velocity in xrange(128): 
                try: samples[midinote, velocity] = samples[midinote-1, velocity]
                except: pass
    if len(initial_keys) > 0:
        print 'Preset loaded: ' + str(preset) 
    else:
        print 'Preset empty: ' + str(preset)
        basename = "%d Empty preset" %preset
    display("")    


#########################################
##  OPEN AUDIO DEVICE   org frames_per_buffer = 512
#########################################

p = pyaudio.PyAudio()
try:
    stream = p.open(format = pyaudio.paInt16, channels = 2, rate = 44100, frames_per_buffer = 512, output = True, input = False, output_device_index = AUDIO_DEVICE_ID, stream_callback = AudioCallback)
    print 'Opened audio: '+ p.get_device_info_by_index(AUDIO_DEVICE_ID)['name']
except:
    print "Invalid Audio Device ID: " + str(AUDIO_DEVICE_ID)
    print "Here is a list of audio devices:"
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        # Remove input device (not really useful on a Raspberry Pi)
        if dev['maxOutputChannels'] > 0:
            print str(i) + " -- " + dev['name']
    exit(1)



#########################################
##  LCD DISPLAY 
##  (HD44780 based 16x2)
#########################################

if USE_HD44780_16x2_LCD:
    import RPi.GPIO as GPIO
    from time import sleep
    lcd = HD44780()

    def display(s2):
        #lcd.clear()
        global basename, MIDI_CHANNEL, sample_mode, volume, globaltranspose
        s1 = "%d %s %d%% %+d" % (MIDI_CHANNEL, sample_mode, volume, globaltranspose)
        if s2 == "": s2 = basename
        print "display: %s \\ %s" % (s1, s2)
        #lcd.message(s1 + " "*8 + "\n" + s2 + " "*15)
        lcd.message(s1 + "\n" + s2)
    #lcd.clear()
    time.sleep(0.5)
    display('Start Samplerbox')
    time.sleep(0.5)

else:

    def display(s):
        pass    

#########################################
##  BUTTONS THREAD (RASPBERRY PI GPIO)
##  Volume knobs based on code published by Mirco,
##      see: http://www.samplerbox.org/forum/51
#########################################


if USE_BUTTONS:
    import RPi.GPIO as GPIO

    lastbuttontime = 0
    butt_up = 5     # values of butt_up/down/sel depend on physical wiring
    butt_down = 13
    butt_sel = 26
    buttfunc = 0
    button_functions=["","set: Volume","set: Midichannel","set: Transpose","RenewUSB/MidMute"]

    def Buttons():
        global preset, basename, lastbuttontime, volume, MIDI_CHANNEL, globaltranspose, midi_mute
        global buttfunc, button_functions, butt_up, butt_down, butt_sel

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(butt_up, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(butt_down, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(butt_sel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        lastbuttontime = time.time()

        while True:
            now = time.time()
            if (now - lastbuttontime) > 0.2:
                if not GPIO.input(butt_down):
                    lastbuttontime = now
                    print("Button down")
                    if buttfunc==0:
                        preset -= 1
                        if preset < 1: preset = 128
                        LoadSamples()
                    elif buttfunc==1:
                        volume-=5
                        if volume<0: volume=0
                        p = subprocess.Popen(["amixer","-c%d" % AUDIO_DEVICE_ID,"set","%s,0" % AUDIO_DEVICE_OUT,str(volume)+"%"], stdout=subprocess.PIPE)
                        getvolume()
                        display("")
                    elif buttfunc==2:
                        MIDI_CHANNEL -= 1
                        if MIDI_CHANNEL < 1: MIDI_CHANNEL = 16
                        display("")
                    elif buttfunc==3:
                        globaltranspose -= 1
                        if globaltranspose < -99: globaltranspose = -99
                        display("")
                    elif buttfunc==4:
                        if not midi_mute:
                            midi_mute = True
                            display("** MIDI muted **")
                        else:
                            midi_mute = False
                            display("")

                elif not GPIO.input(butt_up):
                    lastbuttontime = now
                    print("Button up")
                    midi_mute = False
                    if buttfunc==0:
                        preset += 1  
                        if preset > 128: preset = 1
                        LoadSamples()      
                    elif buttfunc==1:
                        volume+=5
                        if volume>100: volume=100
                        p = subprocess.Popen(["amixer","-c%d" % AUDIO_DEVICE_ID,"set","%s,0" % AUDIO_DEVICE_OUT,str(volume)+"%"], stdout=subprocess.PIPE)
                        getvolume()
                        display("")
                    elif buttfunc==2:
                        MIDI_CHANNEL += 1
                        if MIDI_CHANNEL > 16: MIDI_CHANNEL = 1
                        display("")
                    elif buttfunc==3:
                        globaltranspose += 1
                        if globaltranspose > 99: globaltranspose = 99
                        display("")
                    elif buttfunc==4:
                        basename = "None"
                        LoadSamples()

                elif not GPIO.input(butt_sel):
                    lastbuttontime = now
                    print("Function Button")
                    buttfunc +=1
                    midi_mute = False
                    if buttfunc >4: buttfunc=0
                    display(button_functions[buttfunc])

                time.sleep(0.02)

    ButtonsThread = threading.Thread(target = Buttons)
    ButtonsThread.daemon = True
    ButtonsThread.start()    


#########################################
##  MIDI IN via SERIAL PORT
##  
#########################################

if USE_SERIALPORT_MIDI:
    import serial

    ser = serial.Serial('/dev/ttyAMA0', baudrate=38400)       # see hack in /boot/cmline.txt : 38400 is 31250 baud for MIDI!

    def MidiSerialCallback():
        message = [0, 0, 0]
        while True:
          i = 0
          while i < 3:
            data = ord(ser.read(1)) # read a byte
            if data >> 7 != 0:  
              i = 0      # status byte!   this is the beginning of a midi message: http://www.midi.org/techspecs/midimessages.php
            message[i] = data
            i += 1
            if i == 2 and message[0] >> 4 == 12:  # program change: don't wait for a third byte: it has only 2 bytes
              message[2] = 0
              i = 3
          MidiCallback(message, None)

    MidiThread = threading.Thread(target = MidiSerialCallback)
    MidiThread.daemon = True
    MidiThread.start()


#########################################
##  LOAD FIRST SOUNDBANK
##  
#########################################     

LoadSamples()


#########################################
##  MIDI DEVICES DETECTION
##  MAIN LOOP
#########################################

midi_in = [rtmidi.MidiIn()]
previous = []
while True:
    for port in midi_in[0].ports:
        if port not in previous and 'Midi Through' not in port:
            midi_in.append(rtmidi.MidiIn())
            midi_in[-1].callback = MidiCallback        
            midi_in[-1].open_port(port)       
            print 'Opened MIDI: '+ port
    previous = midi_in[0].ports
    time.sleep(2)
