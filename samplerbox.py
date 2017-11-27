#
#  SamplerBox 
#
#  author:    Joseph Ernest (twitter: @JosephErnest, mail: contact@samplerbox.org)
#  url:       http://www.samplerbox.org/
#  license:   Creative Commons ShareAlike 3.0 (http://creativecommons.org/licenses/by-sa/3.0/)
#
#  samplerbox.py: Main file
#
#   SamplerBox extended by HansEhv
#   see docs at  http://homspace.xs4all.nl/homspace/samplerbox
#   changelog in changelog.txt
#

########  LITERALS, don't change ########
PLAYLIVE = "Keyb"                       # reacts on "keyboard" interaction
PLAYBACK = "Once"                       # ignores loop markers ("just play the sample with option to stop")
PLAYBACK2X = "Onc2"                     # ignores loop markers with note-off by same note ("just play the sample with option to stop")
PLAYLOOP = "Loop"                       # recognize loop markers, note-off by 127-note ("just play the loop with option to stop")
PLAYLOOP2X = "Loo2"                     # recognize loop markers, note-off by same note ("just play the loop with option to stop")
VELSAMPLE = "Sample"                    # velocity equals sampled value, requires multiple samples to get differentation
VELACCURATE = "Accurate"                # velocity as played, allows for multiple (normalized!) samples for timbre
#########################################
##  LOCAL CONFIG  
##  Adapt to your setup !
#########################################

AUDIO_DEVICE_ID = 2                     # change this number to use another soundcard, default=0
SAMPLES_DIR = "/media/"                 # The root directory containing the sample-sets. Example: "/media/" to look for samples on a USB stick / SD card
USE_SERIALPORT_MIDI = False             # Set to True to enable MIDI IN via SerialPort (e.g. RaspberryPi's GPIO UART pins)
USE_HD44780_16x2_LCD = True             # Set to True to use a HD44780 based 16x2 LCD
USE_ALSA_MIXER = True                   # Set to True to use to use the alsa mixer (via pyalsaaudio)
USE_BUTTONS = True                      # Set to True to use momentary buttons connected to RaspberryPi's GPIO pins
MAX_POLYPHONY = 80                      # This can be set higher, but 80 is a safe value
MIDI_CHANNEL = 11                       # midi channel
BOXSAMPLE_MODE = PLAYLIVE               # we need a default: original samplerbox
BOXVELOCITY_MODE = VELSAMPLE            # we need a default: original samplerbox
BOXSTOP127 = 109   # 88-key:108=C8 77-key:103=G7 61-key:96=C7. "Left side" has some notes slack
volume = 87                             # the startup (alsa=output) volume (0-100), change with function buttons
volumeCC = 1.0                          # assumed value of the volumeknob controller before first use, max=1.0 (the knob can only decrease).
BOXRELEASE = 30                         # 30 results in the samplerbox default (FADEOUTLENGTH=30000)
RELSAMPLE= "N"                          # release samples: N=none, E=Embedded, S=Separate(not implemented)
BOXXFADEOUT = 10                        # crossfade glues the sample to the release sample
BOXXFADEIN = 1                          # crossfade glues the sample to the release sample
BOXXFADEVOL = 1.0                       # crossfade glues the sample to the release sample
PRESETBASE = 0                          # Does the programchange / sample set start at 0 (MIDI style) or 1 (human style)
preset = 0 + PRESETBASE                 # the default patch to load
PITCHRANGE = 12                         # default range of the pitchwheel in semitones (max=12 is een octave)
PITCHBITS = 7                           # pitchwheel resolution, 0=disable, max=14 (=16384 steps)
                                        # values below 7 will produce bad results

if USE_ALSA_MIXER:
    ########## Mixercontrols I experienced, add your soundcard's specific....
    MIXER_CONTROL = ["PCM","Speaker","Headphone"]

########## Chords & Scales definitions  # You always need index=0 (is single note, "normal play")

chordname=["","Maj","Min","Augm","Dim","Sus2","Sus4","Dom7","Maj7","Min7","MiMa7","hDim7","Dim7","Aug7","AuMa7","D7S4"]
chordnote=[[0],[0,4,7],[0,3,7],[0,4,8],[0,3,6],[0,2,7],[0,5,7],[0,4,7,10],[0,4,7,11],[0,3,7,10],[0,3,7,11],[0,3,6,10],[0,3,6,9],[0,4,8,10],[0,4,8,11],[0,5,7,10]]
currchord=0                             # single note, "normal play"

scalename=["","C","D","E","F","G","A","B","Cm","Dm","Em","Fm","Gm","Am","Bm"]
scalechord=[
    [0,0,0,0,0,0,0,0,0,0,0,0],  # 0
    [1,0,2,0,2,1,0,1,0,2,1,4],  # C
    [1,3,1,0,2,0,2,1,0,1,0,2],  # D
    [0,2,1,3,1,0,2,0,2,1,0,1],  # E
    [1,0,2,1,4,1,0,2,0,2,1,0],  # F
    [1,0,1,0,2,1,3,1,0,2,0,2],  # G
    [0,2,1,0,1,0,2,1,3,1,0,2],  # A
    [0,2,0,2,1,0,1,0,2,1,0,1],  # B
    [2,0,4,1,0,2,0,2,1,0,1,0],  # Cm
    [1,0,2,0,4,1,0,2,0,2,1,0],  # Dm
    [1,0,1,0,2,0,3,1,0,2,0,2],  # Em
    [2,1,0,1,0,2,2,4,1,0,2,0],  # Fm
    [2,0,2,1,0,1,0,2,0,4,1,0],  # Gm
    [1,0,2,0,2,1,0,1,0,2,0,4],  # Am
    [0,3,1,0,2,0,2,1,0,1,0,2]   # Bm
    ]
currscale=0
notename=["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]  # 0 in scalechord table
#    ["Maj","C#","Min","D#","Min","Maj","F#","Maj","G#","Min","Maj","Dim"], # C
#    ["Maj","Augm","Maj","D#","Min","F","Min","Maj","G#","Maj","A#","Min"], # D
#    ["C","Min","Maj","Augm","Maj","F","Min","G","Min","Maj","A#","Maj"],   # E
#    ["Maj","C#","Min","Maj","Dim","Maj","F#","Min","G#","Min","Maj","B"],  # F
#    ["Maj","C#","Maj","D#","Min","Maj","Augm","Maj","G#","Min","A#","Min"],# G
#    ["C","Min","Maj","D#","Maj","F","Min","Maj","Augm","Maj","A#","Min"],  # A
#    ["C","Min","D","Min","Maj","F","Maj","G","Min","Maj","A#","Maj"],      # B
#    ["Min","C#","Dim","Maj","E","Min","F#","Min","Maj","A","Maj","B"],     # Cm
#    ["Maj","C#","Min","D#","Dim","Maj","F#","Min","G#","Min","Maj","B"],   # Dm
#    ["Maj","C#","Maj","D#","Min","F","Augm","Maj","G#","Min","A#","Min"],  # Em
#    ["Min","Maj","D","Maj","E","Min","Min","Dim","Maj","A","Min","B"],     # Fm
#    ["Min","C#","Min","Maj","E","Maj","F#","Min","G#","Dim","Maj","B"],    # Gm
#    ["Maj","C#","Min","D#","Min","Maj","F#","Maj","G#","Min","A#","Dim"],  # Am
#    ["C","Augm","Maj","D#","Min","F","Min","Maj","G#","Maj","A#","Min"]    # Bm

########## Initialize other globals, don't change

samples = {}
playingnotes = {}
sustainplayingnotes = []
triggernotes = []
sustain = False
playingsounds = []
globaltranspose = 0
voices=[]
currvoice = 1
midi_mute = False
globalgain = 1                         # the input volume correction, change per set in definition.txt
#test PRERELEASE = BOXRELEASE
stop127 = BOXSTOP127
sample_mode = BOXSAMPLE_MODE
PITCHBEND = 0
PITCHRANGE *= 2     # actually it is 12 up and 12 down
pitchnotes = PITCHRANGE
PITCHSTEPS = 2**PITCHBITS
pitchneutral = PITCHSTEPS/2
pitchdiv = 2**(14-PITCHBITS)
if AUDIO_DEVICE_ID > 0:
    MIXER_CARD_ID = AUDIO_DEVICE_ID-1  # This may vary with your HW. The jack/HDMI of PI use 1 alsa card index
else:
    MIXER_CARD_ID = 0

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
import sounddevice
import threading   
from chunk import Chunk
import struct
import rtmidi2
import samplerbox_audio   # audio-module


#########################################
##  LCD DISPLAY 
##   - HD44780 class, based on 16x2 LCD interface code by Rahul Kar, see:
##     http://www.rpiblog.com/2012/11/interfacing-16x2-lcd-with-raspberry-pi.html
##   - Actual display routine
#########################################

class HD44780:

    #def __init__(self, pin_rs=7, pin_e=8, pins_db=[25,24,22,23,27,17,18,4]):
    def __init__(self, pin_rs=7, pin_e=8, pins_db=[27,17,18,4]):
                                                #remove first 4 elements for 4-bit operation
                                                #and mind the physical wiring !
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
        sleep(0.001)
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

    def message(self, text):
        """ Send string to LCD. Newline wraps to second line"""
        self.cmd(0x02)  # go home first
        x = 0
        for char in text:
            if char == '\n':
                self.cmd(0xC0) # next line
                x = 0
            else:
                x += 1
                if x < 17: self.cmd(ord(char),1)

if USE_HD44780_16x2_LCD:
    import RPi.GPIO as GPIO
    from time import sleep
    lcd = HD44780()

    def display(s2):
        global basename, sample_mode, volume, globaltranspose, currvoice, currchord, chordname, scalename, currscale, button_disp, buttfunc
        if globaltranspose == 0:
            transpose = ""
        else:
            transpose = "%+d" % globaltranspose
        if USE_ALSA_MIXER:
            s1 = "%s%s %s %d%% %s" % (scalename[currscale], chordname[currchord], sample_mode, volume, transpose)
        else:
            s1 = "%s%s %s %s" % (scalename[currscale], chordname[currchord], sample_mode, transpose)
        if s2 == "":
            if currvoice>1: s2=str(currvoice)+":"
            s2 += basename
            if buttfunc>0:
                s1 += " "*15
                s1 = s1[:13] + "> "+button_disp[buttfunc]
        lcd.message(s1 + " "*15 + "\n" + s2 + " "*15)
        
    time.sleep(0.5)
    display('Start Samplerbox')
    time.sleep(0.5)

else:
    def display(s):
        pass    


#########################################
##  SLIGHT MODIFICATION OF PYTHON'S WAVE MODULE
##  TO READ CUE MARKERS & LOOP MARKERS if applicable in mode
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
            raise Error, '%s does not start with RIFF id' % (file)
        if self._file.read(4) != 'WAVE':
            raise Error, '%s is not a WAVE file' % (file)
        self._fmt_chunk_read = 0
        self._data_chunk = None
        self._cue=0
        while 1:
            self._data_seek_needed = 1
            try:
                chunk = Chunk(self._file, bigendian=0)
            except EOFError:
                break
            chunkname = chunk.getname()
            #print "Found chunk:" + chunkname
            if chunkname == 'fmt ':
                try:
                    self._read_fmt_chunk(chunk)
                    self._fmt_chunk_read = 1
                except:
                    print "Invalid fmt chunk in %s, please check: max sample rate = 44100, max bit rate = 24" % (file)
                    break
            elif chunkname == 'data':
                if not self._fmt_chunk_read:
                    raise Error, 'data chunk before fmt chunk in %s' % (file)
                self._data_chunk = chunk
                self._nframes = chunk.chunksize // self._framesize
                self._data_seek_needed = 0
            elif chunkname == 'cue ':
                try:
                    numcue = struct.unpack('<i',chunk.read(4))[0]
                    for i in range(numcue):
                        id, position, datachunkid, chunkstart, blockstart, sampleoffset = struct.unpack('<ii4siii',chunk.read(24))
                        if (sampleoffset>self._cue): self._cue=sampleoffset     # we need the last one in the sample
                        #self._cue.append(sampleoffset)                         # so we don't collect them all anymore...
                except:
                    print "invalid cue chunk in %s" % (file)
            elif chunkname == 'smpl':
                manuf, prod, sampleperiod, midiunitynote, midipitchfraction, smptefmt, smpteoffs, numsampleloops, samplerdata = struct.unpack('<iiiiiiiii',chunk.read(36))
                #for i in range(numsampleloops):
                if numsampleloops > 0:      # we don't need the repeat loops...
                    cuepointid, type, start, end, fraction, playcount = struct.unpack('<iiiiii',chunk.read(24)) 
                    self._loops.append([start,end])
            chunk.skip()
        if not self._fmt_chunk_read or not self._data_chunk:
            raise Error, 'fmt chunk and/or data chunk missing in %s' % (file)

    def getmarkers(self):
        return self._cue
        
    def getloops(self):
        return self._loops


#########################################
##  MIXER CLASSES and general procs
#########################################

def GetStopmode(mode):
    stopmode = -2
    if mode==PLAYLIVE:
        stopmode = 128                          # stop on note-off = release key
    elif mode==PLAYBACK:
        stopmode = -1                           # don't stop, play sample at full lenght (unless restarted)
    elif mode==PLAYLOOP:
        stopmode = 127                          # stop on 127-key
    elif mode==PLAYBACK2X or mode==PLAYLOOP2X:
        stopmode = 2                            # stop on 2nd keypress
    return stopmode
def GetLoopmode(mode):
    if mode==PLAYBACK or mode==PLAYBACK2X:
        loopmode = -1
    else:
        loopmode = 1
    return loopmode
        
class PlayingSound:
    def __init__(self, sound, note, vel, pos, end, loop, stopnote):
        self.sound = sound
        self.pos = pos
        self.end = end
        self.loop = loop
        self.fadeoutpos = 0
        self.isfadeout = False
        if pos > 0 : self.isfadein = True
        else       : self.isfadein = False
        self.note = note
        self.vel = vel
        self.stopnote = stopnote

    def __str__(self):
        return "<PlayingSound note: '%i', velocity: '%i', pos: '%i'>" %(self.note, self.vel, self.pos)
    def playingnote(self):
        return self.note
    def playingvelocity(self):
        return self.vel
    def playingstopnote(self):
        return self.stopnote
    
    def fadeout(self, i):
        if self.isfadeout:
            try: playingsounds.remove(self)
            except: pass
        else:
            self.isfadeout = True
        
    def stop(self):
        try: playingsounds.remove(self) 
        except: pass

class Sound:
    def __init__(self, filename, midinote, velocity, mode, release, gain, xfadeout, xfadein, xfadevol):
        global RELSAMPLE
        #print 'Reading ' + filename
        wf = waveread(filename)
        self.fname = filename
        self.midinote = midinote
        self.velocity = velocity
        self.stopmode = GetStopmode(mode)
        #print "%s stopmode: %s=%d" % (self.fname, mode, self.stopmode)
        self.release = release
        self.gain = gain
        self.xfadein = xfadein
        self.xfadevol = xfadevol
        self.eof = wf.getnframes()
        self.loop = GetLoopmode(mode)       # if no loop requested it's useless to check the wav's capability
        if self.loop > 0 and wf.getloops():
            self.loop = wf.getloops()[0][0] # Yes! the wav can loop
            self.nframes = wf.getloops()[0][1] + 2
            self.relmark = wf.getmarkers()
            if self.relmark < self.nframes:
                self.relmark = self.nframes # a release marker before loop-end cannot be right
                self.eof = self.nframes     # so we just stick to the loop to save processing and memory
            else:
                if RELSAMPLE == "E":        # we have found valid release marker,
                    self.release = xfadeout # so we can process the sample switching !
        else:
            self.loop = -1                  # a release marker without loop is unpredictable, so forget the rest
        if self.loop == -1:
            self.relmark = self.eof         # no extra release processing
            self.nframes = self.eof         # and use full length (with default samplerbox release processing

        #print "%s %s loopmode=%d stopmode=%d gain=%.2f" % (filename, mode, self.loop, self.stopmode, self.gain)
        self.data = self.frames2array(wf.readframes(self.eof), wf.getsampwidth(), wf.getnchannels())

        wf.close()            

    def play(self, note, vel, startparm):
        #print "play note %d, vel %d, startparm %d" % (note, vel, startparm)
        if startparm < 0:     # playing of release part of sample is requested
            pos = self.relmark  # so where does it start
            end = self.eof      # and when does it end
            loop = -1           # a release marker does not loop
            stopnote = 128      # don't react on any artificial note-off's anymore
            vel = vel*self.xfadevol     # apply the defined volume correction
        else:
            pos = 0             # could also be startparm (is 0 anyway) - depends future developments....
            end = self.nframes  # play till end of loop/file as 
            loop = self.loop    # we loop if possible by the sample
            stopnote=self.stopmode  # use stopmode to determine possible stopnote
            if stopnote==2:
                stopnote = note
            elif stopnote==127:
                stopnote = 127-note
        #print "play: note=%d vel=%d pos=%d loop=%d stopnote=%d" % (note, vel*self.gain, pos, loop, stopnote)
        snd = PlayingSound(self, note, vel, pos, end, loop, stopnote)
        playingsounds.append(snd)
        return snd

    def frames2array(self, data, sampwidth, numchan):
        if sampwidth == 2:
            npdata = numpy.fromstring(data, dtype = numpy.int16)
        elif sampwidth == 3:
            npdata = samplerbox_audio.binary24_to_int16(data, len(data)/3)    # audio-module
        if numchan == 1: 
            npdata = numpy.repeat(npdata, 2)
        return npdata


#########################################
##  AUDIO stuff
##  CALLBACK routine
##  OPEN AUDIO DEVICE   org frames_per_buffer = 512
##  Setup the sound card's volume control
#########################################

FADEOUTLENGTH = 640*1000  # a large table gives reasonable results (640 up to 2 sec)
FADEOUT = numpy.linspace(1., 0., FADEOUTLENGTH)     # by default, float64
FADEOUT = numpy.power(FADEOUT, 6)
FADEOUT = numpy.append(FADEOUT, numpy.zeros(FADEOUTLENGTH, numpy.float32)).astype(numpy.float32)
SPEEDRANGE = 48
SPEED = numpy.power(2, numpy.arange(-1.0*SPEEDRANGE*PITCHSTEPS, 1.0*SPEEDRANGE*PITCHSTEPS)/(12*PITCHSTEPS)).astype(numpy.float32)

def AudioCallback(outdata, frame_count, time_info, status):
    global playingsounds, volumeCC
    rmlist = []
    playingsounds = playingsounds[-MAX_POLYPHONY:]
    # audio-module:
    b = samplerbox_audio.mixaudiobuffers(playingsounds, rmlist, frame_count, FADEOUT, FADEOUTLENGTH, SPEED, SPEEDRANGE, PITCHBEND, PITCHSTEPS)
    #b = samplerbox_audio.mixaudiobuffers(playingsounds, rmlist, frame_count, FADEOUT, FADEOUTLENGTH, PRERELEASE, SPEED, SPEEDRANGE, PITCHBEND, PITCHSTEPS)
    for e in rmlist:
        #print "remove " +str(e) + ", note: " + str(e.playingnote())
        try: playingsounds.remove(e)
        except: pass
    b *= volumeCC
    outdata[:] = b.reshape(outdata.shape)

print 'Available audio devices'
print(sounddevice.query_devices())
try:
    sd = sounddevice.OutputStream(device=AUDIO_DEVICE_ID, blocksize=512, samplerate=44100, channels=2, dtype='int16', callback=AudioCallback)
    sd.start()
    print 'Opened audio device #%i' % AUDIO_DEVICE_ID
except:
    display("Invalid audiodev")
    print 'Invalid audio device #%i' % AUDIO_DEVICE_ID
    exit(1)

if USE_ALSA_MIXER:
    import alsaaudio
    ok=False
    for i in range(0, 4):
        for j in range(0, len(MIXER_CONTROL)):
            try:
                amix = alsaaudio.Mixer(cardindex=MIXER_CARD_ID+i,control=MIXER_CONTROL[j])
                MIXER_CARD_ID+=i    # save the found value
                ok=True             # indicate OK
                print 'Opened Alsamixer: card id "%i", control "%s"' % (MIXER_CARD_ID, MIXER_CONTROL[j])
                break
            except:
                pass
        if ok: break
    if ok:
        def getvolume():
            global volume
            vol = amix.getvolume()
            volume = int(vol[0])
        def setvolume(volume):
            amix.setvolume(volume)
        setvolume(volume)
        getvolume()
    else:
        USE_ALSA_MIXER=False
        display("Invalid mixerdev")
        print 'Invalid mixer card id "%i" or control "%s" --' % (MIXER_CARD_ID, MIXER_CONTROL)
        print '-- Mixer card id is "x" in "(hw:x,y)" (if present) in opened audio device.'
if not USE_ALSA_MIXER:
    def getvolume():
        pass
    def setvolume(volume):
        pass

#########################################
##  MIDI
##   - general routines
##   - CALLBACK
#########################################

def AllNotesOff():
    global playingnotes, playingsounds, sustainplayingnotes, triggernotes, currchord, currscale
    playingsounds = []
    playingnotes = {}
    sustainplayingnotes = []
    triggernotes = [128]*128     # fill with unplayable note
    currchord = 0
    currscale = 0

def MidiCallback(message, time_stamp):
    global playingnotes, sustain, sustainplayingnotes, triggernotes, stop127, RELSAMPLE
    global preset, sample_mode, midi_mute, velocity_mode, globalgain, volumeCC, voices, currvoice
    global PRERELEASE, PITCHBEND, PITCHRANGE, pitchneutral, pitchdiv, pitchnotes
    global chordnote, currchord, chordname, scalechord, currscale, notename
    messagetype = message[0] >> 4
    messagechannel = (message[0] & 15) + 1
    #print 'Channel %d, message %d' % (messagechannel , messagetype)
    if (messagechannel == MIDI_CHANNEL) and (midi_mute == False):
        note = message[1] if len(message) > 1 else None
        midinote = note
        velocity = message[2] if len(message) > 2 else None

        if messagetype==8 or messagetype==9:        # We may have a note on/off
            midinote += globaltranspose
            if velocity==0: messagetype=8           # prevent complexity in the rest of the checking
            if messagetype==8:                      # first process standard midi note-off, but take care
                if midinote in playingnotes and triggernotes[midinote]<128: # .. to not accidently turn off release samples in non-keyboard mode
                       for m in playingnotes[midinote]:
                           if m.playingstopnote() < 128:    # are we in a special mode
                               messagetype = 128            # if so, then ignore this note-off
                           else:                            # since we have the info at hand now:
                               velmixer = m.playingvelocity()  # save org value for release sample
                else: messagetype = 128             # nothing's playing, so there is nothing to stop
            if messagetype == 9:    # is a note-off hidden in this note-on ?
                if midinote in playingnotes:    # this can only be if the note is already playing
                    for m in playingnotes[midinote]:
                        xnote=m.playingstopnote()   # yes, so check it's stopnote
                        if xnote>-1 and xnote<128:  # not in once or keyboard mode
                            if midinote==xnote:     # could it be a push-twice stop?
                                messagetype = 8
                                velmixer = m.playingvelocity()  # save org value for release sample
                            elif midinote >= stop127:   # could it be mirrored stop?
                                if (midinote-127) in playingnotes:  # is the possible mirror note-on active?
                                    for m in playingnotes[midinote-127]:
                                        if midinote==m.playingstopnote():   # and has it mirrored stop?
                                            messagetype = 8
                                            velmixer = m.playingvelocity()  # save org value for release sample

            if messagetype == 9:    # Note on 
                #print 'Note on %d -> %d, voice=%d, chord=%s in %s/%s, velocity=%d, globalgain=%d' % (note, midinote, currvoice, chordname[currchord], sample_mode, velocity_mode, velocity, globalgain) #debug
                try:
                    if velocity_mode == VELSAMPLE:
                        velmixer = 127 * globalgain
                    else:
                        velmixer = velocity * globalgain
                    if currscale>0:               # scales require a chords mix
                        m = int(midinote/12)      # do a "remainder midinote/12" without...
                        currchord = scalechord[currscale][midinote-m*12]  # ...having to import the full math module
                        #print "Playing %s in %s giving %s" %(notename[midinote-m*12], scalename[currscale], chordname[currchord])
                    for n in range (len(chordnote[currchord])):
                        playnote=midinote+chordnote[currchord][n]
                        for m in sustainplayingnotes:   # safeguard polyphony; don't sustain double notes
                            if m.note == playnote:
                                m.fadeout(50)
                                #print 'clean sustain ' + str(playnote)
                        if triggernotes[playnote] < 128:  # cleanup in case of retrigger
                            if playnote in playingnotes:    # occurs in once/loops modes and chords
                                for m in playingnotes[playnote]: 
                                    #print "clean note " + str(playnote)
                                    m.fadeout(50)
                                playingnotes[playnote] = []   # housekeeping
                        triggernotes[playnote]=midinote   # we are last playing this one
                        #print "start note " + str(playnote)
                        #FMO stops: hier moet de set van voices aangezet
                        #print "start playingnotes playnote %d, velocity %d, currvoice %d, velmixer %d" %(playnote, velocity, currvoice, velmixer)
                        playingnotes.setdefault(playnote,[]).append(samples[playnote, velocity, currvoice].play(playnote, velmixer, 0))
                except:
                    print 'Unassigned/unfilled note or other exception in note %d->%d' % (midinote-globaltranspose , midinote)
                    pass

            elif messagetype == 8:  # Note off
                #print 'Note off ' + str(note) + '->' + str(midinote) + ', voice=' + str(currvoice)    #debug
                for playnote in xrange(128):
                    if triggernotes[playnote] == midinote:  # did we make this one play ?
                        if playnote in playingnotes:
                            for m in playingnotes[playnote]: 
                                if sustain:
                                    #print 'Sustain note ' + str(playnote)   # debug
                                    sustainplayingnotes.append(m)
                                else:
                                    #print "Stop note " + str(playnote)
                                    m.fadeout(50)
                                playingnotes[playnote] = []
                                triggernotes[playnote] = 128  # housekeeping
                                #FMO stops: hier moet de set van voices aangezet
                                if  RELSAMPLE == 'E':
                                    playingnotes.setdefault(playnote,[]).append(samples[playnote, velocity, currvoice].play(playnote, velmixer*globalgain, -1))

        elif messagetype == 12: # Program change
            preset = note+PRESETBASE
            #print "Program change to %d=%d" % (note, preset)
            LoadSamples()

        elif messagetype == 14: # Pitch Bend
            PITCHBEND=(((128*velocity+note)/pitchdiv)-pitchneutral)*pitchnotes

        elif messagetype == 11: # control change (CC, sometimes called Continuous Controllers)
            CCnum = note
            CCval = velocity
            #print "CCnum = %d, CCval = %d" % (CCnum, CCval)

            if CCnum == 7:       # volume knob action (0-127)
                volumeCC = CCval / 127.0   # force float

            elif CCnum == 64:    # sustain pedal
                if sample_mode == PLAYLIVE:
                    if (CCval < 64):    # sustain off
                        for n in sustainplayingnotes:
                            n.fadeout(50)
                        sustainplayingnotes = []       
                        sustain = False
                        #print 'Sustain pedal released'
                    else:               # sustain on
                        sustain = True
                        #print 'Sustain pedal pressed'

            #elif CCnum == 72:           # Sound controller 3 = release time. ...needs rethinking...
            #    PRERELEASE = CCval
                
            elif CCnum == 80:           # general purpose 80 used for voices
                if CCval > 0:           # I use MIDI CC Trigger/Release; this ignores default release value, but .....
                    if CCval in voices: # .... it skips (the override / special effects voice), which should be done anyway!
                        currvoice = CCval
                        display("")

            elif CCnum == 81:           # general purpose 81 used for chords and scales
                if CCval > 0:           # I use MIDI CC Trigger/Release; this ignores default release value
                    CCval -= 1          # align with table, makes it human human too :-)
                    if CCval < len(chordnote):
                        currchord = CCval
                        currscale = 0
                        display("")
                    CCval -= 99         # values 100-112 used for scales (theoretically, currently 100-107)
                    if CCval > -1 and CCval < len(scalechord):
                        currscale = CCval
                        currchord = 0
                        display("")

            elif CCnum == 82:           # Pitch bend sensitivity (my controller cannot send RPN)
                pitchnotes = (24*CCval+100)/127

            elif CCnum==120 or CCnum==123:    # "All sounds off" or "all notes off"
                AllNotesOff()

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
    global preset, samples, SAMPLES_DIR, BOXRELEASE, PRERELEASE, BOXXFADEIN, PREXFADEIN, BOXSTOP17, stop127
    global globaltranspose, BOXSAMPLE_MODE, basename, BOXVELOCITY_MODE, velocity_mode, globalgain, voices, currvoice, PITCHRANGE, pitchnotes, RELSAMPLE
    #print 'Entered ActuallyLoad'
    AllNotesOff()
    currbase = basename    

    samplesdir = SAMPLES_DIR if os.listdir(SAMPLES_DIR) else '.'      # use current folder (containing 0 Saw) if no user media containing samples has been found
    basename = next((f for f in os.listdir(samplesdir) if f.startswith("%d " % preset)), None)      # or next(glob.iglob("blah*"), None)
    print "We have %s, we want %s" %(currbase, basename)
    if basename:
        if basename == currbase:      # don't waste time reloading a patch
            #print 'Kept preset %s' % basename
            display("")
            return
        dirname = os.path.join(samplesdir, basename)

    mode=[]
    globalgain = 1
    currvoice = 1
    sample_mode=BOXSAMPLE_MODE      # fallback to the samplerbox default
    velocity_mode=BOXVELOCITY_MODE  # fallback to the samplerbox default
    stop127=BOXSTOP127              # fallback to the samplerbox default
    pitchnotes=PITCHRANGE           # fallback to the samplerbox default
    PRERELEASE=BOXRELEASE           # fallback to the samplerbox default
    PREXFADEOUT=BOXXFADEOUT         # fallback to the samplerbox default
    PREXFADEIN=BOXXFADEIN           # fallback to the samplerbox default
    PREXFADEVOL=BOXXFADEVOL         # fallback to the samplerbox default
    voices = []
    globaltranspose = 0
    samples = {}
    fillnotes = {}
    fillnote = 'Y'          # by default we will fill/generate missing notes
    voice0 = False

    if not basename: 
        #print 'Preset empty: %s' % preset
        basename = "%d Empty preset" %preset
        display("")
        return

    #print 'Preset loading: %s ' % basename
    display("Loading %s" % basename)
    definitionfname = os.path.join(dirname, "definition.txt")
    if os.path.isfile(definitionfname):
        with open(definitionfname, 'r') as definitionfile:
            for i, pattern in enumerate(definitionfile):
                try:
                    if r'%%gain' in pattern:
                        globalgain = abs(float(pattern.split('=')[1].strip()))
                        continue
                    if r'%%transpose' in pattern:
                        globaltranspose = int(pattern.split('=')[1].strip())
                        continue
                    if r'%%stopnotes' in pattern:
                        stop127 = (int(pattern.split('=')[1].strip()))
                        if stop127 > 127 or stop127 < 64:
                            print "Stopnotes start of %d invalid, set to %d" % (stop127, BOXSTOP127)
                            stop127 = BOXSTOP127
                        continue
                    if r'%%release' in pattern:
                        PRERELEASE = (int(pattern.split('=')[1].strip()))
                        if PRERELEASE > 127:
                            print "Release of %d limited to %d" % (PRERELEASE, 127)
                            PRERELEASE = 127
                        continue
                    if r'%%xfadeout' in pattern:
                        PREXFADEOUT = (int(pattern.split('=')[1].strip()))
                        if PREXFADEOUT > 127:
                            print "xfadeout of %d limited to %d" % (PREXFADEOUT, 127)
                            PREXFADEOUT = 127
                        continue
                    if r'%%xfadein' in pattern:
                        PREXFADEIN = (int(pattern.split('=')[1].strip()))
                        if PREXFADEIN > 127:
                            print "xfadein of %d limited to %d" % (PREXFADEIN, 127)
                            PREXFADEIN = 127
                        continue
                    if r'%%xfadevol' in pattern:
                        xfadevol = abs(float(pattern.split('=')[1].strip()))
                        continue
                    if r'%%fillnote' in pattern:
                        m = pattern.split('=')[1].strip().title()
                        if m == 'Y' or m == 'N':
                            fillnote = m
                        continue
                    if r'%%pitchbend' in pattern:
                        pitchnotes = abs(int(pattern.split('=')[1].strip()))
                        if pitchnotes > 12:
                            print "Pitchbend of %d limited to 12" % pitchnotes
                            pitchnotes = 12
                        pitchnotes *= 2     # actually it is 12 up and 12 down
                        continue
                    if r'%%mode' in pattern:
                        mode = pattern.split('=')[1].strip().title()
                        if mode==PLAYLIVE or mode==PLAYBACK or mode==PLAYBACK2X or mode==PLAYBACK64 or mode==PLAYLOOP or mode==PLAYLOOP2X or mode==PLAYLOOP64: sample_mode = mode
                        continue
                    if r'%%velmode' in pattern:
                        mode = pattern.split('=')[1].strip().title()
                        if mode == VELSAMPLE or mode == VELACCURATE: velocity_mode = mode
                        continue
                    #defaultparams = { 'midinote': '0', 'velocity': '127', 'notename': '', 'voice': '1' }
                    defaultparams = { 'midinote': '0', 'velocity': '127', 'gain': '1', 'notename': '', 'voice': '1', 'mode': sample_mode, 'transpose': '0', 'release': PRERELEASE, 'xfadeout': PREXFADEOUT, 'xfadein': PREXFADEIN, 'xfadevol': PREXFADEVOL, 'fillnote': fillnote }
                    if len(pattern.split(',')) > 1:
                        defaultparams.update(dict([item.split('=') for item in pattern.split(',', 1)[1].replace(' ','').replace('%', '').split(',')]))
                    pattern = pattern.split(',')[0]
                    pattern = re.escape(pattern.strip())
                    pattern = pattern.replace(r"\%midinote", r"(?P<midinote>\d+)").replace(r"\%velocity", r"(?P<velocity>\d+)").replace(r"\%gain", r"(?P<gain>[-+]?\d*\.?\d+)").replace(r"\%voice", r"(?P<voice>\d+)")\
                                     .replace(r"\%fillnote", r"(?P<fillnote>[YNyn]").replace(r"\%mode", r"(?P<mode>[A-Za-z0-9])").replace(r"\%transpose", r"(?P<transpose>\d+)")\
                                     .replace(r"\%release", r"(?P<release>\d+)").replace(r"\%xfadeout", r"(?P<xfadeout>\d+)").replace(r"\%xfadein", r"(?P<xfadein>\d+)")\
                                     .replace(r"\%notename", r"(?P<notename>[A-Ga-g]#?[0-9])").replace(r"\*", r".*?").strip()    # .*? => non greedy
                    for fname in os.listdir(dirname):
                        #print 'Processing ' + fname
                        if LoadingInterrupt:
                            #print 'Loading % s interrupted...' % dirname
                            return
                        m = re.match(pattern, fname)
                        if m:
                            info = m.groupdict()
                            midinote = int(info.get('midinote', defaultparams['midinote']))
                            velocity = int(info.get('velocity', defaultparams['velocity']))
                            gain = abs(float((info.get('gain', defaultparams['gain']))))
                            transpose = int(info.get('transpose', defaultparams['transpose']))
                            voice = int(info.get('voice', defaultparams['voice']))
                            voices.append(voice)
                            mode = info.get('mode', defaultparams['mode'])
                            release = int(info.get('release', defaultparams['release']))
                            if (release>127): release=127
                            xfadeout = int(info.get('xfadeout', defaultparams['xfadeout']))
                            if (xfadeout>127): xfadeout=127
                            xfadein = int(info.get('xfadein', defaultparams['xfadein']))
                            if (xfadein>127): xfadein=127
                            xfadevol = abs(float(info.get('xfadevol', defaultparams['xfadevol'])))
                            if voice == 0:          # the override / special effects voice cannot fill
                                voicefillnote = 'N' # so we ignore whatever the user wants (RTFM)
                                voice0 = True       # remember we saw one...
                            else:
                                voicefillnote = (info.get('fillnote', defaultparams['fillnote'])).title().rstrip()
                            notename = info.get('notename', defaultparams['notename'])
                            # next statement places note 60 on C3/C4/C5 with the +0/1/2. So now it is C4:
                            if notename: midinote = NOTES.index(notename[:-1].lower()) + (int(notename[-1])+1) * 12
                            midinote-=transpose
                            mode=mode.title()
                            if (GetStopmode(mode)<-1) or (GetStopmode(mode)==127 and midinote>(127-stop127)):
                                mode=PLAYLIVE   # invalid mode or note out of range
                            samples[midinote, velocity, voice] = Sound(os.path.join(dirname, fname), midinote, velocity, mode, release, gain, xfadeout, xfadein, xfadevol)
                            fillnotes[midinote, voice] = voicefillnote
                            #print "sample: %s, note: %d, voice: %d, mode: %s, fillnote: %s, release: %s, xfadein: %s" %(fname, midinote, voice, mode, voicefillnote, release, xfadein)
                except:
                    print "Error in definition file, skipping line %s." % (i+1)

    else:
        for midinote in range(128):
            if LoadingInterrupt: 
                return
            voices.append(1)
            file = os.path.join(dirname, "%d.wav" % midinote)
            #print "Trying " + file
            if os.path.isfile(file):
                #print "Processing " + file
                samples[midinote, 127, 1] = Sound(file, midinote, 127, PLAYLIVE, PRERELEASE, globalgain, PREXFADEOUT, PREXFADEIN, PREXFADEVOL)
                fillnotes[midinote, 1] = fillnote

    initial_keys = set(samples.keys())
    if len(initial_keys) > 0:

        voices = list(set(voices)) # Remove duplicates by converting to a set
        for voice in voices:
            #print "Complete info for voice %d" % (voice)
            for midinote in xrange(128):    # first complete velocities in found notes
                lastvelocity = None
                for velocity in xrange(128):
                    if (midinote, velocity, voice) in initial_keys:
                        if not lastvelocity:
                            for v in range(velocity): samples[midinote, v, voice] = samples[midinote, velocity, voice]
                        lastvelocity = samples[midinote, velocity, voice]
                    else:
                        if lastvelocity:
                            samples[midinote, velocity, voice] = lastvelocity
            initial_keys = set(samples.keys())  # we got more keys, but not enough yet
            lastlow = -130                      # force lowest unfilled notes to be filled with the nexthigh
            nexthigh = None                     # nexthigh not found yet, and start filling the missing notes
            for midinote in xrange(128-stop127, stop127):    # only fill the keyboard area.
                if (midinote, 1, voice) in initial_keys:
                    if fillnotes[midinote, voice] == 'Y':  # can we use this note for filling?
                        nexthigh = None                     # passed nexthigh
                        lastlow = midinote                  # but we got fresh low info
                else:
                    if not nexthigh:
                        nexthigh=260    # force highest unfilled notes to be filled with the lastlow
                        for m in xrange(midinote+1, 128):
                            if (m, 1, voice) in initial_keys:
                                if fillnotes[m, voice] == 'Y':  # can we use this note for filling?
                                    if m < nexthigh: nexthigh=m
                    if (nexthigh-lastlow) > 260:     # did we find a note valid for filling?
                        break                        # no, stop trying
                    if midinote <= 0.5+(nexthigh+lastlow)/2: m=lastlow
                    else: m=nexthigh
                    #print "Note %d will be generated from %d" % (midinote, m)
                    for velocity in xrange(128):
                        samples[midinote, velocity, voice] = samples[m, velocity, voice]

        if voice0:                    # do we have the override / special effects voice ?
            for midinote in xrange(128):
                if (midinote, 0) in fillnotes:
                   for voice in voices:
                        if voice > 0:
                            #print "Override note %d in voice %d" % (midinote, voice)
                            for velocity in xrange(128):
                                samples[midinote, velocity, voice] = samples[midinote, velocity, 0]

        #print 'Preset loaded: ' + str(preset)
        display("")

    else:
        #print 'Preset empty: ' + str(preset)
        basename = "%d Empty preset" %preset
        display("")


#########################################
##  BUTTONS THREAD (RASPBERRY PI GPIO)
#########################################

if USE_BUTTONS:
    import RPi.GPIO as GPIO

    lastbuttontime = 0
    butt_up = 5     # values of butt_up/down/sel depend on physical wiring
    butt_down = 13  # values of butt_up/down/sel depend on physical wiring
    butt_sel = 26   # values of butt_up/down/sel depend on physical wiring
    buttfunc = 0
    button_functions=["","Volume","Midichannel","Transpose","RenewUSB/MidMute","Play Chord:","Use Scale:"]
    button_disp=["","V","M","T","X","C","S"]  # take care, these values can used elsewhere for testing

    def Button_display():
        global volume, MIDI_CHANNEL, globaltranspose, buttfunc, button_functions, chordname, currchord, scalename, currscale
        function_value=[""," %d%%"%(volume)," %d"%(MIDI_CHANNEL)," %+d"%(globaltranspose),""," %s"%(chordname[currchord])," %s"%(scalename[currscale])]
        display(button_functions[buttfunc]+function_value[buttfunc])
        
    def Buttons():
        global preset, basename, lastbuttontime, volume, MIDI_CHANNEL, globaltranspose, midi_mute, chordname, currchord, scalename, currscale
        global buttfunc, button_functions, butt_up, butt_down, butt_sel, button_disp

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
                    #print("Button down")
                    if buttfunc==0:
                        preset -= 1
                        if preset < PRESETBASE: preset = 127+PRESETBASE
                        LoadSamples()
                    elif buttfunc==1:
                        volume-=5
                        if volume<0: volume=0
                        setvolume(volume)
                        getvolume()
                        Button_display()
                    elif buttfunc==2:
                        MIDI_CHANNEL -= 1
                        if MIDI_CHANNEL < 1: MIDI_CHANNEL = 16
                        Button_display()
                    elif buttfunc==3:
                        globaltranspose -= 1
                        if globaltranspose < -99: globaltranspose = -99
                        Button_display()
                    elif buttfunc==4:
                        if not midi_mute:
                            midi_mute = True
                            display("** MIDI muted **")
                        else:
                            midi_mute = False
                            Button_display()
                    elif buttfunc==5:
                        currscale=0     # scale and chord mode are mutually exclusive
                        currchord -= 1
                        if currchord<0: currchord=len(chordname)-1
                        Button_display()
                    elif buttfunc==6:
                        currchord=0     # scale and chord mode are mutually exclusive
                        currscale-=1
                        if currscale<0: currscale=len(scalename)-1
                        Button_display()

                elif not GPIO.input(butt_up):
                    lastbuttontime = now
                    #print("Button up")
                    midi_mute = False
                    if buttfunc==0:
                        preset += 1  
                        if preset > 127+PRESETBASE: preset = PRESETBASE
                        LoadSamples()      
                    elif buttfunc==1:
                        volume+=5
                        if volume>100: volume=100
                        setvolume(volume)
                        getvolume()
                        Button_display()
                    elif buttfunc==2:
                        MIDI_CHANNEL += 1
                        if MIDI_CHANNEL > 16: MIDI_CHANNEL = 1
                        Button_display()
                    elif buttfunc==3:
                        globaltranspose += 1
                        if globaltranspose > 99: globaltranspose = 99
                        Button_display()
                    elif buttfunc==4:
                        basename = "None"
                        LoadSamples()
                        #Button_display()
                    elif buttfunc==5:
                        currscale=0     # scale and chord mode are mutually exclusive
                        currchord += 1
                        if currchord>=len(chordname): currchord=0
                        Button_display()
                    elif buttfunc==6:
                        churrchord=0     # scale and chord mode are mutually exclusive
                        currscale += 1
                        if currscale>=len(scalename): currscale=0
                        Button_display()

                elif not GPIO.input(butt_sel):
                    lastbuttontime = now
                    #print("Function Button")
                    buttfuncmax=len(button_functions)
                    buttfunc +=1
                    if buttfunc >= len(button_functions): buttfunc=0
                    if not USE_ALSA_MIXER:
                        if button_disp[buttfunc]=="V": buttfunc +=1
                    #use if above gets complex: if buttfunc >= len(button_functions): buttfunc=0
                    midi_mute = False
                    Button_display()

                time.sleep(0.02)

    ButtonsThread = threading.Thread(target = Buttons)
    ButtonsThread.daemon = True
    ButtonsThread.start()    


#########################################
##  MIDI IN via SERIAL PORT
##  this should be extended with logic for "midi running status"
##  possible solution at http://www.samplerbox.org/forum/146
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

midi_in = rtmidi2.MidiInMulti()
curr_ports = []
prev_ports = []
try:
  while True:
    curr_ports = rtmidi2.get_in_ports()
    if (len(prev_ports) != len(curr_ports)):
        #print 'Change in midi connected devices, close all opened ports'
        midi_in.close_ports()
        prev_ports = []
        for port in curr_ports:
            if port not in prev_ports and 'Midi Through' not in port and (len(prev_ports) != len(curr_ports)):
                midi_in.open_ports(port)
                midi_in.callback = MidiCallback
                print 'Open MIDI port: ' + port
        prev_ports = curr_ports
    time.sleep(2)
except KeyboardInterrupt:
    print "\nstopped by ctrl-c\n"
except:
    print "\nstopped by Other Error"
finally:
    display('Stopped')
    sleep(0.5)
    GPIO.cleanup()
