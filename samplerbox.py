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
PLAYBACK = "Once"                       # ignores loop markers and note-off ("just play the sample")
PLAYSTOP = "On64"                       # ignores loop markers with note-off by note+64 ("just play the sample with option to stop")
PLAYLOOP = "Loop"                       # recognize loop markers, note-off by note+64 ("just play the loop with option to stop")
PLAYLO2X = "Loo2"                       # recognize loop markers, note-off by same note ("just play the loop with option to stop")
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
sample_mode = PLAYLIVE                  # we need a default: original samplerbox
velocity_mode = VELSAMPLE               # we need a default: original samplerbox
volume = 87                             # the startup (alsa=output) volume (0-100), change with function buttons
volumeCC = 1.0                          # assumed value of the volumeknob controller before first use, max=1.0 (the knob can only decrease).
BOXRELEASE = 30                         # 30 results in the samplerbox default (FADEOUTLENGTH=30000)
PRESETBASE = 0                          # Does the programchange / sample set start at 0 (MIDI style) or 1 (human style)
preset = 0 + PRESETBASE                 # the default patch to load
PITCHRANGE = 12                         # default range of the pitchwheel in semitones (max=12 is een octave)
PITCHBITS = 7                           # pitchwheel resolution, 0=disable, max=14 (=16384 steps)
                                        # values below 7 will produce bad results

if USE_ALSA_MIXER:
    ########## Mixercontrols I experienced, add your soundcard's specific....
    MIXER_CONTROL = ["PCM","Speaker","Headphone"]

########## Chords definitions  # You always need index=0 (is single note, "normal play")

chordname=["","Maj","Min","Augm","Dim","Sus2","Sus4","Dom7","Maj7","Min7","MiMa7","hDim7","Dim7","Aug7","AuMa7","D7S4"]
chordnote=[[0],[0,4,7],[0,3,7],[0,4,8],[0,3,6],[0,2,7],[0,5,7],[0,4,7,10],[0,4,7,11],[0,3,7,10],[0,3,7,11],[0,3,6,10],[0,3,6,9],[0,4,8,10],[0,4,8,11],[0,5,7,10]]
currchord=0                             # single note, "normal play"

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
gain = 1                                # the input volume correction, change per set in definition.txt
PRERELEASE = BOXRELEASE
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
import samplerbox_audio


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
        global basename, sample_mode, volume, globaltranspose, currvoice, currchord, chordname, button_disp, buttfunc
        if globaltranspose == 0:
            transpose = ""
        else:
            transpose = "%+d" % globaltranspose
        if USE_ALSA_MIXER:
            s1 = "%s %s %d%% %s" % (chordname[currchord], sample_mode, volume, transpose)
        else:
            s1 = "%s %s %s" % (chordname[currchord], sample_mode, transpose)
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
        if sample_mode==PLAYLIVE or sample_mode==PLAYLOOP or sample_mode==PLAYLO2X:
            return self._loops


#########################################
##  MIXER CLASSES
#########################################

class PlayingSound:
    def __init__(self, sound, note, vel):
        self.sound = sound
        self.pos = 0
        self.fadeoutpos = 0
        self.isfadeout = False
        self.note = note
        self.vel = vel

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
    def __init__(self, filename, midinote, velocity, release):
        #print 'Reading ' + filename
        wf = waveread(filename)
        self.fname = filename
        self.midinote = midinote
        self.velocity = velocity
        self.release = release
        if wf.getloops(): 
            self.loop = wf.getloops()[0][0]
            self.nframes = wf.getloops()[0][1] + 2
        else:
            self.loop = -1
            self.nframes = wf.getnframes()

        self.data = self.frames2array(wf.readframes(self.nframes), wf.getsampwidth(), wf.getnchannels())

        wf.close()            

    def play(self, note, vel):
        snd = PlayingSound(self, note, vel)
        #print 'fname: ' + self.fname + ' note/vel: '+str(note)+'/'+str(vel)+' midinote: ' +str(self.midinote) + ' vel: ' + str(self.velocity)
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
    b = samplerbox_audio.mixaudiobuffers(playingsounds, rmlist, frame_count, FADEOUT, FADEOUTLENGTH, PRERELEASE, SPEED, SPEEDRANGE, PITCHBEND, PITCHSTEPS)
    for e in rmlist:
        try: playingsounds.remove(e)
        except: pass
    b *= volumeCC
    outdata[:] = b.reshape(outdata.shape)

print 'Available audio devices'
print(sounddevice.query_devices())
try:
    # A thing to try: add latency="low" (default is "high") to the parameters below
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
    global playingnotes, playingsounds, sustainplayingnotes, triggernotes
    playingsounds = []
    playingnotes = {}
    sustainplayingnotes = []
    triggernotes = [128]*128     # fill with unplayable note

def MidiCallback(message, time_stamp):
    global playingnotes, sustain, sustainplayingnotes, triggernotes
    global preset, sample_mode, midi_mute, velocity_mode, gain, volumeCC, voices, currvoice
    global PRERELEASE, PITCHBEND, PITCHRANGE, pitchneutral, pitchdiv, pitchnotes
    global chordnote, currchord     # , chordname
    messagetype = message[0] >> 4
    messagechannel = (message[0] & 15) + 1
    if (messagechannel == MIDI_CHANNEL) and (midi_mute == False):
        note = message[1] if len(message) > 1 else None
        midinote = note
        velocity = message[2] if len(message) > 2 else None
        noteoff = False
        if sample_mode == PLAYLIVE: noteoff = True

        if messagetype == 9:    # is a note-off hidden in this note-on ?
            if velocity==0:     # midi protocol, next elif's are SB's special modes
                messagetype = 8 # noteoff must be true here :-)
            elif (sample_mode==PLAYSTOP or sample_mode==PLAYLOOP) and midinote > 63:
                messagetype = 8
                midinote = midinote - 64
                noteoff = True
            elif sample_mode==PLAYLO2X and midinote in playingnotes:
                if playingnotes[midinote]!=[]:
                    messagetype = 8
                    noteoff = True

        if messagetype == 9:    # Note on
            midinote += globaltranspose
            #print 'Note on ' + str(note) + '->' + str(midinote) + ', voice=' + str(currvoice) +', chord=' + chordname[currchord] + ' in ' + sample_mode + ', gain=' + str(gain) #debug
            try:
              if velocity_mode == VELSAMPLE:
                  velmixer = 127 * gain
              else:
                  velmixer = velocity * gain
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
                  playingnotes.setdefault(playnote,[]).append(samples[playnote, velocity, currvoice].play(playnote, velmixer))
            except:
              #print 'Unassigned/unfilled note or other exception'
              pass

        elif messagetype == 8:  # Note off
            midinote += globaltranspose
            if noteoff == True:
                #print 'Note off ' + str(note) + '->' + str(midinote) + ', voice=' + str(currvoice)    #debug
                for playnote in xrange(128):
                    if triggernotes[playnote] == midinote:  # did we make this one play ?
                        if playnote in playingnotes:
                            for m in playingnotes[playnote]: 
                                if sustain:
                                    #print 'Sustain note ' + str(playnote)   # debug
                                    sustainplayingnotes.append(m)
                                else:
                                    #print "stop note " + str(playnote)
                                    m.fadeout(50)
                            playingnotes[playnote] = []
                        triggernotes[playnote] = 128  # housekeeping

        elif messagetype == 12: # Program change
            preset = note+PRESETBASE
            #print "Program change to %d=%d" % (note, preset)
            LoadSamples()

        elif messagetype == 14: # Pitch Bend
            PITCHBEND=(((128*velocity+note)/pitchdiv)-pitchneutral)*pitchnotes

        elif messagetype == 11: # control change (CC, sometimes called Continuous Controllers)
            CCnum = note
            CCval = velocity
            #print "CCnum = " + str(CCnum) + ", CCval = " + str(CCval)

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

            elif CCnum == 72:           # Sound controller 3 = release time
                PRERELEASE = CCval
                
            elif CCnum == 80:           # general purpose 80 used for voices
                if CCval in voices:     # Voices start at 1, so no issues with trigger/release
                    currvoice = CCval
                    display("")

            elif CCnum == 81:           # general purpose 81 used for chords
                if CCval > 0:           # I use MIDI CC Trigger/Release; this ignores default release value
                    CCval -= 1          # align with table, makes it human human too :-)
                    if CCval < len(chordnote):
                        currchord = CCval
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
    global preset, samples
    global FADEOUTLENGTH, FADEOUT, BOXRELEASE,  PRERELEASE
    global globaltranspose, sample_mode, basename, velocity_mode, gain, voices, currvoice, PITCHRANGE, pitchnotes
    #print 'Entered ActuallyLoad'
    AllNotesOff()
    currbase = basename    

    samplesdir = SAMPLES_DIR if os.listdir(SAMPLES_DIR) else '.'      # use current folder (containing 0 Saw) if no user media containing samples has been found
    basename = next((f for f in os.listdir(samplesdir) if f.startswith("%d " % preset)), None)      # or next(glob.iglob("blah*"), None)
    #print "We have %s, we want %s" %(currbase, basename)
    if basename:
        if basename == currbase:      # don't waste time reloading a patch
            #print 'Kept preset %s' % basename
            display("")
            return
        dirname = os.path.join(samplesdir, basename)

    mode=[]
    gain = 1
    currvoice = 1
    pitchnotes=PITCHRANGE   # fallback to the samplerbox default
    PRERELEASE=BOXRELEASE   # fallback to the samplerbox default for the preset release time
    voices = []
    globaltranspose = 0
    samples = {}
    fillnotes = {}
    fillnote = 'Y'          # by default we will fill/generate missing notes

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
                        gain = abs(float(pattern.split('=')[1].strip()))
                        continue
                    if r'%%transpose' in pattern:
                        globaltranspose = int(pattern.split('=')[1].strip())
                        continue
                    if r'%%release' in pattern:
                        PRERELEASE = (int(pattern.split('=')[1].strip()))
                        if PRERELEASE > 127:
                            print "Release of %d limited to %d" % (PRERELEASE, 127)
                            PRERELEASE = 127
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
                        if mode==PLAYLIVE or mode==PLAYBACK or mode==PLAYSTOP or mode==PLAYLOOP or mode==PLAYLO2X: sample_mode = mode
                        continue
                    if r'%%velmode' in pattern:
                        mode = pattern.split('=')[1].strip().title()
                        if mode == VELSAMPLE or mode == VELACCURATE: velocity_mode = mode
                        continue
                    #defaultparams = { 'midinote': '0', 'velocity': '127', 'notename': '', 'voice': '1' }
                    defaultparams = { 'midinote': '0', 'velocity': '127', 'notename': '', 'voice': '1', 'release': '128', 'fillnote': fillnote }
                    if len(pattern.split(',')) > 1:
                        defaultparams.update(dict([item.split('=') for item in pattern.split(',', 1)[1].replace(' ','').replace('%', '').split(',')]))
                    pattern = pattern.split(',')[0]
                    pattern = re.escape(pattern.strip())
                    pattern = pattern.replace(r"\%midinote", r"(?P<midinote>\d+)").replace(r"\%velocity", r"(?P<velocity>\d+)")\
                                     .replace(r"\%voice", r"(?P<voice>\d+)").replace(r"\%release", r"(?P<release>\d+)").replace(r"\%fillnote", r"(?P<fillnote>[YNyn]")\
                                     .replace(r"\%notename", r"(?P<notename>[A-Ga-g]#?[0-9])").replace(r"\*", r".*?").strip()    # .*? => non greedy
                    #pattern = pattern.replace(r"\%midinote", r"(?P<midinote>\d+)").replace(r"\%velocity", r"(?P<velocity>\d+)").replace(r"\%voice", r"(?P<voice>\d+)")\
                    #                 .replace(r"\%notename", r"(?P<notename>[A-Ga-g]#?[0-9])").replace(r"\*", r".*?").strip()    # .*? => non greedy
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
                            voice = int(info.get('voice', defaultparams['voice']))
                            voices.append(voice)
                            release = int(info.get('release', defaultparams['release']))
                            voicefillnote = (info.get('fillnote', defaultparams['fillnote'])).title().rstrip()
                            notename = info.get('notename', defaultparams['notename'])
                            # next statement places note 60 on C3/C4/C5 with the +0/1/2. So now it is C4:
                            if notename: midinote = NOTES.index(notename[:-1].lower()) + (int(notename[-1])+1) * 12
                            samples[midinote, velocity, voice] = Sound(os.path.join(dirname, fname), midinote, velocity, release)
                            fillnotes[midinote, voice] = voicefillnote
                            #print "sample: %s, note: %d, voice: %d, fillnote: %s" %(fname, midinote, voice, voicefillnote)
                except:
                    print "Error in definition file, skipping line %s." % (i+1)

    else:
        for midinote in range(0, 127): 
            if LoadingInterrupt: 
                return
            voices.append(1)    # missing in original
            file = os.path.join(dirname, "%d.wav" % midinote)
            #print "Trying " + file
            if os.path.isfile(file):
                #print "Processing " + file
                samples[midinote, 127, 1] = Sound(file, midinote, 127, 128)
                fillnotes[midinote, 1] = fillnote

    initial_keys = set(samples.keys())
    if len(initial_keys) > 0:

        voices = list(set(voices)) # Remove duplicates by converting to a set
        for voice in voices:
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
            nexthigh = None                     # nexthigh not found yet
            for midinote in xrange(128):        # and start filling the missing notes
                if (midinote, 1, voice) in initial_keys:
                    #print "Note %d found as sample" % (midinote)
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
    button_functions=["","Volume","Midichannel","Transpose","RenewUSB/MidMute","Play Chord:"]
    button_disp=["","V","M","T","S","C"]  # take care, these values are used below for testing

    def Button_display():
        global volume, MIDI_CHANNEL, globaltranspose, buttfunc, button_functions, chordname, currchord
        function_value=[""," %d%%"%(volume)," %d"%(MIDI_CHANNEL)," %+d"%(globaltranspose),""," %s"%(chordname[currchord])]
        display(button_functions[buttfunc]+function_value[buttfunc])
        
    def Buttons():
        global preset, basename, lastbuttontime, volume, MIDI_CHANNEL, globaltranspose, midi_mute, chordname, currchord
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
                        currchord -= 1
                        if currchord<0: currchord=len(chordname)-1
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
                        currchord += 1
                        if currchord>=len(chordname): currchord=0
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
