#
#  SamplerBox 
#
#  author:    Joseph Ernest (twitter: @JosephErnest, mail: contact@samplerbox.org)
#  url:       http://www.samplerbox.org/
#  license:   Creative Commons ShareAlike 3.0 (http://creativecommons.org/licenses/by-sa/3.0/)
#
#  samplerbox.py: Main file
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
#   see docs at  http://homspace.xs4all.nl/homspace/samplerbox
#   changelog in /boot/samplerbox/changelist.txt
#

##########################################################################
##  IMPORT MODULES (generic, more can be loaded depending on local config)
##  WARNING: GPIO modules in this build use mode=BCM. Do not mix modes!
##########################################################################

import wave,sounddevice,rtmidi2
from chunk import Chunk
import time,psutil,numpy,struct
import sys,os,re,threading   
import ConfigParser
import samplerbox_audio   # audio-module (cython)
import gv,getcsv
gv.rootprefix='/home/pi/samplerbox'
#gv.rootprefix='/home/hans/samplerbox'
if not os.path.isdir(gv.rootprefix):
    gv.rootprefix=""
sys.path.append('./modules')

########  Define local general functions ########
usleep = lambda x: time.sleep(x/1000000.0)
msleep = lambda x: time.sleep(x/1000.0)
def GPIOcleanup():
    if USE_GPIO:
        import RPi.GPIO as GPIO
        GPIO.cleanup()
def getindex(key, table, onecol=False):
    for i in range(len(table)):
        if onecol:
            if key==table[i]:   return i
        else:
            if key==table[i][0]:return i
    return -100
notenames=["C","Cs","C#","Dk","D","Ds","D#","Ek","E","Es","F","Fs","F#","Gk","G","Gs","G#","Ak","A","As","A#","Bk","B","Bs"]
def notename2midinote(notename,fractions):
    notename=notename.title()
    if notename[:2]=="Ck":  # normalize synonyms
        notename="Bs%d" %(int(notename[-1])-1) # Octave number switches between B and C
    elif notename[:2]=="FK":
        notename="Es%s"%notename[-1]
    try:
        x=notenames.index(format(notename[:len(notename)-1]))
        if fractions==1:    # we have undivided semi-tones = 12-tone scale
            x,y=divmod(x,2) # so our range is half of what's tested
            if y!=0:        # and we can't process any found q's.
                print "Ignored quartertone %s as we are in 12-tone mode" %notename
                midinote=-1
            # next statements places note C4 on 60
            else:            # 12 note logic
                midinote = x + (int(notename[-1])+1) * 12
        else:               # 24 note logic
            midinote = x + (int(notename[-1])-2) * 24 +12
    except:
        print "Ignored unrecognized notename '%s'" %notename
        midinote=-128
    return midinote
def midinote2notename(midinote,fractions):
    notename=None
    octave=None
    note=None
    if   midinote==-2: notename="Ctrl"
    elif midinote==-1: notename="None"
    else:
        if midinote<gv.stop127 and midinote>(127-gv.stop127):
            if fractions==1:
                octave,note=divmod(midinote,12)
                octave-=1
                note*=2
            else:
                octave,note=divmod(midinote+36,24)
            notename="%s%d" %(notenames[note],octave)
        else: notename="%d" %(midinote)
    return notename
def setChord(x,*z):
    y=getindex(x,gv.chordname,True)
    if y>-1:                # ignore if undefined
        gv.currscale=0      # playing chords excludes scales
        gv.currchord=y
        display("")
def setScale(x,*z):
    y=getindex(x,gv.scalename,True)
    if y>-1:                # ignore if undefined
        gv.currchord=0      # playing chords excludes scales
        gv.currscale=y
        display("")
CCmap=[]
def setVoice(x, iv=0, *z):
    global CCmap
    if iv==0:
        xvoice=int(x)
    else:
        xvoice=getindex(int(x),gv.voicelist)
    if xvoice>-1:                       # ignore if undefined
        voice=gv.voicelist[xvoice][0]
        if voice!=gv.currvoice:         # also ignore if active
            #print gv.voicelist[xvoice]
            if iv>-1:   # -1 means mapdriven voice change: map should not be changed by voice def!
                setNotemap(gv.voicelist[xvoice][3])
            gv.currvoice=voice
            gv.sample_mode=gv.voicelist[xvoice][2]
            gv.CCmap = list(gv.CCmapBox)            # construct this voice's CC setup
            for i in xrange(len(gv.CCmapSet)):
                found=False
                if gv.CCmapSet[i][3]==0 or gv.CCmapSet[i][3]==voice:# voice applies
                    for j in xrange(len(gv.CCmap)):                 # so check if button is known
                        if gv.CCmapSet[i][0]==gv.CCmap[j][0]:
                            found=True
                            if (gv.CCmapSet[i][3]>=gv.CCmap[j][3]): # voice specific takes precedence
                                gv.CCmap[j]=gv.CCmapSet[i]          # replace entry
                            continue
                    if not found:
                        gv.CCmap.append(gv.CCmapSet[i])             # else add entry
        display("")
def setNotemap(x, *z):
    try:
        y=x-1
    except:
        y=getindex(x,gv.notemaps,True)
    if y>-1:
        if gv.notemaps[y]!=gv.currnotemap:
            gv.currnotemap=gv.notemaps[y]
            gv.notemapping=[]
            for i in xrange(len(gv.notemap)):       # do we have note mapping ?
                if gv.notemap[i][0]==gv.currnotemap:
                    gv.notemapping.append([gv.notemap[i][2],gv.notemap[i][1],gv.notemap[i][3],gv.notemap[i][4],gv.notemap[i][5]])
    else:
        gv.currnotemap=""
        gv.notemapping=[]
    display("")
    
playingbacktracks=0
def playBackTrack(x,*z):
    global playingbacktracks
    playnote=int(x)+130
    if playnote in gv.playingnotes and gv.playingnotes[playnote]!=[]: # is the track playing?
        playingbacktracks-=1
        for m in gv.playingnotes[playnote]:
            m.playing2end()         # let it finish
    else:
        try:
            gv.playingnotes.setdefault(playnote,[]).append(gv.samples[playnote, 127, 0].play(playnote, playnote, 127*gv.globalgain, 0, 0))
            playingbacktracks+=1
        except:
            print 'Unassigned/unfilled track or other exception for backtrack %s->%d' % (x,playnote)

gv.GPIOcleanup=GPIOcleanup              # and announce the procs to modules
gv.getindex=getindex
gv.notename2midinote=notename2midinote
gv.midinote2notename=midinote2notename
gv.setVoice=setVoice
gv.setNotemap=setNotemap
gv.setMC(gv.CHORDS,setChord)
gv.setMC(gv.SCALES,setScale)
gv.setMC(gv.VOICES,setVoice)
gv.setMC(gv.NOTEMAPS,setNotemap)
gv.setMC(gv.BACKTRACKS,playBackTrack)

########  LITERALS used in the main module only ########
PLAYLIVE = "Keyb"                       # reacts on "keyboard" interaction
PLAYBACK = "Once"                       # ignores loop markers ("just play the sample with option to stop")
PLAYBACK2X = "Onc2"                     # ignores loop markers with note-off by same note
PLAYLOOP = "Loop"                       # recognize loop markers, note-off by 127-note
PLAYLOOP2X = "Loo2"                     # recognize loop markers, note-off by same note
BACKTRACK = "Back"                      # recognize loop markers, loop-off by same note or controller
PLAYMONO = "Mono"                       # monophonic (with chords), loop like Loo2, but note/chord stops when next note is played.
VELSAMPLE = "Sample"                    # velocity equals sampled value, requires multiple samples to get differentation
VELACCURATE = "Accurate"                # velocity as played, allows for multiple (normalized!) samples for timbre
SAMPLES_INBOX = gv.rootprefix+"/samples/"  # Builtin directory containing the sample-sets.
SAMPLES_ONUSB = gv.rootprefix+"/media/"    # USB-Mount directory containing the sample-sets.
CONFIG_LOC = gv.rootprefix+"/boot/samplerbox/"
CHORDS_DEF = "chords.csv"
SCALES_DEF = "scales.csv"
CTRLCCS_DEF = "controllerCCs.csv"
KEYNAMES_DEF = "keynotes.csv"


##########  read LOCAL CONFIG ==> /boot/samplerbox/configuration.txt
gv.cp=ConfigParser.ConfigParser()
gv.cp.read(CONFIG_LOC + "configuration.txt")
AUDIO_DEVICE_ID = gv.cp.getint(gv.cfg,"AUDIO_DEVICE_ID".lower())
USE_SERIALPORT_MIDI = gv.cp.getboolean(gv.cfg,"USE_SERIALPORT_MIDI".lower())
USE_HD44780_16x2_LCD = gv.cp.getboolean(gv.cfg,"USE_HD44780_16x2_LCD".lower())
USE_OLED = gv.cp.getboolean(gv.cfg,"USE_OLED".lower())
USE_I2C_7SEGMENTDISPLAY = gv.cp.getboolean(gv.cfg,"USE_I2C_7SEGMENTDISPLAY".lower())
gv.USE_ALSA_MIXER = gv.cp.getboolean(gv.cfg,"USE_ALSA_MIXER".lower())
USE_48kHz = gv.cp.getboolean(gv.cfg,"USE_48kHz".lower())
USE_BUTTONS = gv.cp.getboolean(gv.cfg,"USE_BUTTONS".lower())
USE_LEDS = gv.cp.getboolean(gv.cfg,"USE_LEDS".lower())
USE_HTTP_GUI = gv.cp.getboolean(gv.cfg,"USE_HTTP_GUI".lower())
gv.MIDI_CHANNEL = gv.cp.getint(gv.cfg,"MIDI_CHANNEL".lower())
DRUMPAD_CHANNEL = gv.cp.getint(gv.cfg,"DRUMPAD_CHANNEL".lower())
gv.NOTES_CC = gv.cp.getint(gv.cfg,"NOTES_CC".lower())
gv.PRESET = gv.cp.getint(gv.cfg,"PRESET".lower())
gv.PRESETBASE = gv.cp.getint(gv.cfg,"PRESETBASE".lower())
MAX_POLYPHONY = gv.cp.getint(gv.cfg,"MAX_POLYPHONY".lower())
MAX_MEMLOAD = gv.cp.getint(gv.cfg,"MAX_MEMLOAD".lower())
BOXSAMPLE_MODE = gv.cp.get(gv.cfg,"BOXSAMPLE_MODE".lower())
BOXVELOCITY_MODE = gv.cp.get(gv.cfg,"BOXVELOCITY_MODE".lower())
BOXSTOP127 = gv.cp.getint(gv.cfg,"BOXSTOP127".lower())
BOXRELEASE = gv.cp.getint(gv.cfg,"BOXRELEASE".lower())
BOXDAMP = gv.cp.getint(gv.cfg,"BOXDAMP".lower())
BOXRETRIGGER = gv.cp.get(gv.cfg,"BOXRETRIGGER".lower())
RELSAMPLE= gv.cp.get(gv.cfg,"RELSAMPLE".lower())
BOXXFADEOUT = gv.cp.getint(gv.cfg,"BOXXFADEOUT".lower())
BOXXFADEIN = gv.cp.getint(gv.cfg,"BOXXFADEIN".lower())
BOXXFADEVOL = gv.cp.getfloat(gv.cfg,"BOXXFADEVOL".lower())
PITCHRANGE = gv.cp.getint(gv.cfg,"PITCHRANGE".lower())
PITCHBITS = gv.cp.getint(gv.cfg,"PITCHBITS".lower())
gv.volume = gv.cp.getint(gv.cfg,"volume".lower())
gv.volumeCC = gv.cp.getfloat(gv.cfg,"volumeCC".lower())

########## read CONFIGURABLE TABLES from config dir

# Definition of notes, chords and scales
getcsv.readchords(CONFIG_LOC + CHORDS_DEF)
getcsv.readscales(CONFIG_LOC + SCALES_DEF)

# Midi controllers and keyboard definition
getcsv.readcontrollerCCs(CONFIG_LOC + CTRLCCS_DEF)
getcsv.readkeynames(CONFIG_LOC + KEYNAMES_DEF)
gv.CCmapBox=getcsv.readCCmap(CONFIG_LOC + gv.CTRLMAP_DEF)

########## Initialize other globals, don't change

USE_GPIO=False
PITCHCORR = 0       # This is the 44100 to 48000 correction / hack
PITCHRANGE *= 2     # actually it is 12 up and 12 down

gv.samplesdir = SAMPLES_INBOX
gv.stop127 = BOXSTOP127
gv.sample_mode = BOXSAMPLE_MODE
velocity_mode = BOXVELOCITY_MODE
gv.pitchnotes = PITCHRANGE
PITCHSTEPS = 2**PITCHBITS
gv.pitchneutral = PITCHSTEPS/2
gv.pitchdiv = 2**(14-PITCHBITS)

if AUDIO_DEVICE_ID > 0:
    if gv.rootprefix=="":
        gv.MIXER_CARD_ID = AUDIO_DEVICE_ID-1   # The jack/HDMI of PI use 1 alsa card index
    else:
        gv.MIXER_CARD_ID = 0                   # This may vary with your HW.....
else:
    gv.MIXER_CARD_ID = 0

#########################################
# Display routine
#########################################
try:

    if USE_HD44780_16x2_LCD:
        USE_GPIO=True
        import lcd_16x2
        lcd = lcd_16x2.HD44780()
        def display(s2,s7=""):
            lcd.display(s2)
        display('Start Samplerbox')

    elif USE_OLED:
        USE_GPIO=True
        import OLED
        oled = OLED.oled()
        def display(s2,s7=""):
            oled.display(s2)
        display('Start Samplerbox')

    elif USE_I2C_7SEGMENTDISPLAY:
        import I2C_7segment
        def display(s2,s7=""):
            I2C_7segment.display(s7)
        display('','----')

    elif USE_LEDS:
        USE_GPIO=True
        import LEDs
        def display(s2,s7=""):
            LEDs.signal()
        LEDs.green(False)
        LEDs.red(True,True)

    else:
        def display(s2,s7=""):
            pass    
    gv.display=display                          # and announce the procs to modules

except:
    print "Error activating requested display routine"
    GPIOcleanup()
    exit(1)

##################################################################################
# Effects/Filters
##################################################################################

#
# Arpeggiator (play chordnotes in sequentially, ie open chords)
# Process replaces the note-on/off logic, so rather cheap
#
import arp

#
# Reverb, Moogladder, Wah (envelope, lfo and pedal) and Delay (echo and flanger)
# Based on changing the audio output which requires heavy processing
#
import ctypes
import Cpp
c_float_p = ctypes.POINTER(ctypes.c_float)

#
# Vibrato, tremolo, pan and rotate (poor man's single speaker leslie)
# Being input based, these effects are cheap: less than 1% CPU on PI3
#
import LFO      # take notice: part of process in audio callback

#
# Chorus (add pitch modulated and delayed copies of notes)
# Process incorporated in the note-on logic, so rather cheap as well
#
import CHOrus   # take notice: part of process in midi callback and ARP

#########################################
##  SLIGHT MODIFICATION OF PYTHON'S WAVE MODULE
##  TO READ CUE MARKERS & LOOP MARKERS if applicable in mode
#########################################

class waveread(wave.Wave_read):
#class waveread():
    def initfp(self, file):
        s="%s" %file
        wavname = s.split(',')[0][11:]
        self._convert = None
        self._soundpos = 0
        self._cue = []
        self._loops = []
        self._ieee = False
        self._file = Chunk(file, bigendian=0)
        if self._file.getname() != 'RIFF':
            print '%s does not start with RIFF id' % (wavname)
            raise Error, '%s does not start with RIFF id' % (wavname)
        if self._file.read(4) != 'WAVE':
            print '%s is not a WAVE file' % (wavname)
            raise Error, '%s is not a WAVE file' % (wavname)
        self._fmt_chunk_read = 0
        self._data_chunk = None
        self._cue=0
        while 1:
            self._data_seek_needed = 1
            try:
                chunk = Chunk(self._file, bigendian=0)
            except EOFError:
                break
            except:
                if self._fmt_chunk_read and self._data_chunk:
                    print "Read %s with errors" % (wavname)
                    break   # we have sufficient data so leave the error as is
                else:
                    print "Skipped %s because of chunk.skip error" %file
                    raise Error, "Error in chunk.skip in %s" % (wavname)
            chunkname = chunk.getname()
            #print "Found chunk:" + chunkname
            if chunkname == 'fmt ':
                try:
                    self._read_fmt_chunk(chunk)
                    self._fmt_chunk_read = 1
                except:
                    print "Invalid fmt chunk in %s, please check: max sample rate = 44100, max bit rate = 24" % (wavname)
                    break
            elif chunkname == 'data':
                if not self._fmt_chunk_read:
                    print 'data chunk before fmt chunk in %s' % (wavname)
                else:
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
                    print "invalid cue chunk in %s" % (wavname)
            elif chunkname == 'smpl':
                manuf, prod, sampleperiod, midiunitynote, midipitchfraction, smptefmt, smpteoffs, numsampleloops, samplerdata = struct.unpack('<iiiiiiiii',chunk.read(36))
                #for i in range(numsampleloops):
                if numsampleloops > 0:      # we don't need the repeat loops...
                    cuepointid, type, start, end, fraction, playcount = struct.unpack('<iiiiii',chunk.read(24)) 
                    self._loops.append([start,end])
            try:
                chunk.skip()
            except:
                if self._fmt_chunk_read and self._data_chunk:
                    print "Read %s with errors" % (wavname)
                    break   # we have sufficient data so leave the error as is
                else:
                    print "Skipped %s because of chunk.skip error" %file
                    raise Error, "Error in chunk.skip in %s" % (wavname)
        if not self._fmt_chunk_read or not self._data_chunk:
            print 'fmt chunk and/or data chunk missing in %s' % (wavname)
            raise Error, 'fmt chunk and/or data chunk missing in %s' % (wavname)

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
        stopmode = -1                           # don't stop, play sample at full length (unless restarted)
    elif mode==PLAYLOOP:
        stopmode = 127                          # stop on 127-key
    elif mode==PLAYBACK2X or mode==PLAYLOOP2X or mode==PLAYMONO:
        stopmode = 2                            # stop on 2nd keypress
    elif mode==BACKTRACK:
        stopmode = 3                            # finish looping+outtro on 2nd keypress or defined midi controller
    return stopmode
def GetLoopmode(mode):
    if mode==PLAYBACK or mode==PLAYBACK2X:
        loopmode = -1
    else:
        loopmode = 1
    return loopmode
        
class PlayingSound:
    def __init__(self, sound, voice, note, vel, pos, end, loop, stopnote, retune):
        self.sound = sound
        self.pos = pos
        self.end = end
        self.loop = loop
        self.fadeoutpos = 0
        self.isfadeout = False
        if pos > 0 : self.isfadein = True
        else       : self.isfadein = False
        self.voice = voice
        self.note = note
        self.retune=retune
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
    def playingstopmode(self):
        return self.sound.stopmode
    def playing2end(self):
        self.loop=-1
        self.end=self.sound.eof
    def fadeout(self,sustain=True):
        self.isfadeout=True
        if sustain==False:      # Damp is fadeout with shorter (=no sustained) release,
            self.isfadein=True  # ...a dirty misuse of this field :-)
    #def stop(self):
    #    try: gv.playingsounds.remove(self) 
    #    except: pass

class Sound:
    def __init__(self, filename, voice, midinote, velocity, mode, release, damp, retrigger, gain, xfadeout, xfadein, xfadevol, fractions):
        global RELSAMPLE
        wf = waveread(filename)
        self.fname = filename
        self.voice = voice
        self.midinote = midinote
        self.velocity = velocity
        self.stopmode = GetStopmode(mode)
        #print "%s stopmode: %s=%d" % (self.fname, mode, self.stopmode)
        self.release = release
        self.damp = damp
        self.retrigger = retrigger
        self.gain = gain
        self.xfadein = xfadein
        self.xfadevol = xfadevol
        self.fractions = fractions
        self.eof = wf.getnframes()
        self.loop = GetLoopmode(mode)       # if no loop requested it's useless to check the wav's capability
        if self.loop > 0 and wf.getloops():
            self.loop = wf.getloops()[0][0] # Yes! the wav can loop
            self.nframes = wf.getloops()[0][1] + 2
            self.relmark = wf.getmarkers()
            if self.relmark < self.nframes:
                self.relmark = self.nframes # a release marker before loop-end cannot be right
                self.eof = self.nframes     # so we just stick to the loop to savegv.playingsounds processing and memory
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

    def play(self, midinote, note, vel, startparm, retune):
        if startparm < 0:       # playing of release part of sample is requested
            pos = self.relmark  # so where does it start
            end = self.eof      # and when does it end
            loop = -1           # a release marker does not loop
            stopnote = 128      # don't react on any artificial note-off's anymore
            vel = vel*self.xfadevol     # apply the defined volume correction
        else:
            pos = startparm     # normally 0, chorus needs small displacement
            end = self.nframes  # play till end of loop/file as 
            loop = self.loop    # we loop if possible by the sample
            if arp.active:      # arpeggiator is a keyboard robot
                stopnote=128    # ..so force keyboardmode
            else:
                stopnote=self.stopmode  # use stopmode to determine possible stopnote
                if stopnote==2 or stopnote==3:
                    stopnote = midinote     # let autochordnotes be turned off by their trigger only
                elif stopnote==127:
                    stopnote = 127-note
        snd = PlayingSound(self, self.voice, note, vel, pos, end, loop, stopnote, retune)
        gv.playingsounds.append(snd)
        return snd

    def frames2array(self, data, sampwidth, numchan):
        if sampwidth == 2:
            npdata = numpy.fromstring(data, dtype = numpy.int16)
        elif sampwidth == 3:    # convert 24bit to 16bit
            npdata = samplerbox_audio.binary24_to_int16(data, len(data)/3)
        if numchan == 1:        # make a left and right track from a mone sample
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
SPEEDRANGE = 48     # 2*48=96 is larger than 88, so a (middle) C4-A4 can facilitate largest keyboard
SPEED = numpy.power(2, numpy.arange(-1.0*SPEEDRANGE*PITCHSTEPS, 1.0*SPEEDRANGE*PITCHSTEPS)/(12*PITCHSTEPS)).astype(numpy.float32)

def AudioCallback(outdata, frame_count, time_info, status):
    p=len(gv.playingsounds)-MAX_POLYPHONY
    if p>0:
        print "MAX_POLYPHONY %d exceeded with %d notes" %(MAX_POLYPHONY,p)
        for i in xrange(p+playingbacktracks-1):
            if gv.playingsounds[i].playingstopmode()!=3:    # let the backtracks be
                del gv.playingsounds[i]     # get it out of the system
    # Handle arpeggiator before soundgen to reduce timing issues at chord/sequence changes
    if arp.active: arp.process()
    # audio-module:
    rmlist = []
    b = samplerbox_audio.mixaudiobuffers(rmlist, frame_count, FADEOUT, FADEOUTLENGTH, SPEED, SPEEDRANGE, gv.PITCHBEND+gv.VIBRvalue+PITCHCORR, PITCHSTEPS)
    for e in rmlist:
        try:
            if e.sound.stopmode==3 or e.sound.stopmode==-1:     # keep track of backtrack/once status
                gv.playingnotes[e.note]=[]
            gv.playingsounds.remove(e)
        except: pass
    # volume control and audio effects/filters
    LFO.process[gv.LFOtype]()
    b *= (10**(gv.TREMvalue*gv.volumeCC)-1)/9     # linear doesn't sound natural, this may be to complicated too though...
    if gv.LFtype>0: Cpp.c_filters.moog(b.ctypes.data_as(c_float_p), b.ctypes.data_as(c_float_p), frame_count)
    if gv.AWtype>0: Cpp.c_filters.autowah(b.ctypes.data_as(c_float_p), b.ctypes.data_as(c_float_p), frame_count)
    if gv.DLYtype>0: Cpp.c_filters.delay(b.ctypes.data_as(c_float_p), b.ctypes.data_as(c_float_p), frame_count)
    if gv.FVtype>0: Cpp.c_filters.reverb(b.ctypes.data_as(c_float_p), b.ctypes.data_as(c_float_p), frame_count)
    outdata[:] = b.reshape(outdata.shape)
    # Use this module as timer for ledblinks
    if gv.LEDblink: LEDs.blink()

print 'Available audio devices'
print(sounddevice.query_devices())
try:
    i=44100
    if USE_48kHz:
        if PITCHBITS < 7:
            print "==> Can't tune to 48kHz, please set PITCHBITS to 7 or higher <=="
        else:
            PITCHCORR = -147*(2**(PITCHBITS-7))
        i=48000
    sd = sounddevice.OutputStream(device=AUDIO_DEVICE_ID, blocksize=512, samplerate=i, channels=2, dtype='int16', callback=AudioCallback)
    sd.start()
    print 'Opened audio device #%i on %iHz' % (AUDIO_DEVICE_ID, i)
    Cpp.c_filters.setSampleRate(i)   # align the filters
except:
    display("Invalid audiodev")
    print 'Invalid audio device #%i' % AUDIO_DEVICE_ID
    time.sleep(0.5)
    GPIOcleanup()
    exit(1)

#########################################
##  MIDI
##   - general routines
##   - CALLBACK
#########################################

def ControlChange(CCnum, CCval):
    mc=False
    for m in gv.CCmap:    # look for mapped controllers
        j=m[0]
        if gv.controllerCCs[j][1]==CCnum and (gv.controllerCCs[j][2]==-1 or gv.controllerCCs[j][2]==CCval or gv.MC[m[1]][1]==3):
            if m[2]!=None: CCval=m[2]
            #print "Recognized %d<=>%s related to %s" %(CCnum, gv.controllerCCs[j][0], gv.MC[m[1]][0])
            gv.MC[m[1]][2](CCval,gv.MC[m[1]][0])
            mc=True
            break
    if not mc and (CCnum==120 or CCnum==123):   # "All sounds off" or "all notes off"
        AllNotesOff()

def AllNotesOff(x=0,*z):
    global playingbacktracks
    # stop the robots first
    arp.power(False)
    playingbacktracks = 0
    # empty all queues
    gv.playingsounds = []
    gv.playingnotes = {}
    gv.sustainplayingnotes = []
    gv.triggernotes = [128]*128     # fill with unplayable note
    # reset effects & display
    EffectsOff()
    display("")
def EffectsOff(*z):
    Cpp.FVsetType(0)
    Cpp.AWsetType(0)
    Cpp.DLYsetType(0)
    Cpp.LFsetType(0)
    LFO.setType(0)
    CHOrus.setType(0)
    #AutoChordOff()
def ProgramUp(CCval,*z):
    x=gv.getindex(gv.PRESET,gv.presetlist)+1
    if x>=len(gv.presetlist): x=0
    gv.PRESET=gv.presetlist[x][0]
    gv.LoadSamples()
def ProgramDown(CCval,*z):
    x=gv.getindex(gv.PRESET,gv.presetlist)-1
    if x<0: x=len(gv.presetlist)-1
    gv.PRESET=gv.presetlist[x][0]
    gv.LoadSamples()
def MidiVolume(CCval,*z):
    gv.volumeCC = CCval / 127.0
def AutoChordOff(x=0,*z):
    gv.currchord = 0
    gv.currscale = 0
    display("")
def PitchWheel(LSB,MSB=0,*z):   # This allows for single and double precision.
    try: MSB+=0 # If mapped to a double precision pitch wheel, it should work.
    except:     # But the use/result of double precision controllers does not
        MSB=LSB # justify the complexity it will introduce in the mapping.
        LSB=0   # So I ignore them here. If you want to try, plse share with me.
    gv.PITCHBEND=(((128*MSB+LSB)/gv.pitchdiv)-gv.pitchneutral)*gv.pitchnotes
def ModWheel(CCval,*z):
    print "Modwheel"
    pass        # still in idea stage
sustain=False
def Sustain(CCval,*z):
    global sustain
    if gv.sample_mode==PLAYLIVE or gv.sample_mode==PLAYMONO:
        if (CCval == 0):    # sustain off
            sustain = False
            for n in gv.sustainplayingnotes:
                n.fadeout()
            gv.sustainplayingnotes = []       
        else:               # sustain on
            sustain = True
damp=False
def Damp(CCval,*z):
    global damp
    if (CCval > 0):
        damp = True
        for m in gv.playingsounds:          # get rid of fading notes
            if m.isfadeout:
                m.isfadein=True
        for m in gv.sustainplayingnotes:    # get rid of sustained notes
            m.fadeout(False)
        gv.sustainplayingnotes = []
        for i in gv.playingnotes:           # get rid of playing notes
            for m in gv.playingnotes[i]:
                if m.playingnote()>(127-gv.stop127) and m.playingnote()<gv.stop127:
                    if m.playingstopmode()!=3:  # but exclude backtracks
                        m.fadeout(False)
                        gv.playingnotes[i] = []
                        gv.triggernotes[i] = 128  # housekeeping
    else: damp = False
def DampNew(CCval,*z):
    global damp
    if (CCval>0):   damp = True
    else:           damp = False
def DampLast(CCval,*z):
    global sustain, damp
    if (CCval>0):
        damp = True
        sustain = True
    else:
        damp = False
        sustain = False
        for m in gv.sustainplayingnotes:    # get rid of gathered notes
            m.fadeout(False)
        gv.sustainplayingnotes = []
def PitchSens(CCval,*z):
    gv.pitchnotes = (24*CCval+100)/127
                            # and announce the procs to modules
gv.setMC(gv.PANIC,AllNotesOff)
gv.setMC(gv.EFFECTSOFF,EffectsOff)
gv.setMC(gv.PROGUP,ProgramUp)
gv.setMC(gv.PROGDN,ProgramDown)
gv.setMC(gv.VOLUME,MidiVolume)
gv.setMC(gv.AUTOCHORDOFF,AutoChordOff)
gv.setMC(gv.PITCHWHEEL,PitchWheel)
gv.setMC(gv.MODWHEEL,ModWheel)
gv.setMC(gv.SUSTAIN,Sustain)
gv.setMC(gv.DAMP,Damp)
gv.setMC(gv.DAMPNEW,DampNew)
gv.setMC(gv.DAMPLAST,DampLast)
gv.setMC(gv.PITCHSENS,PitchSens)

def MidiCallback(src, message, time_stamp):
    global RELSAMPLE, velocity_mode, playingbacktracks
    keyboardarea=True
    messagetype = message[0] >> 4
    messagechannel = (message[0]&0xF) + 1   # make channel# human..
    #print '%s -> Channel %d, message %d' % (src, messagechannel , messagetype)
    # -------------------------------------------------------
    # System commands and "hardware remap" of the drumpad
    # -------------------------------------------------------
    if messagetype==15:         # System messages apply to all channels, channel position contains commands
        if messagechannel==15:  # "realtime" reset has to reset all activity & settings
            AllNotesOff()       # (..other realtime expects everything to stay intact..)
        return
    if gv.drumpad:  # using less compact coding in favor of performance...
        if messagechannel==DRUMPAD_CHANNEL:
            if messagetype==8 or messagetype==9:        # We only remap notes
                for i in xrange(len(gv.drumpadmap)):
                    if gv.drumpadmap[i][0]==message[1]:
                        message[1]=gv.drumpadmap[i][1]
                        messagechannel=gv.MIDI_CHANNEL
                        break       # found it, stop wasting time
    # -------------------------------------------------------
    # Then process channel commands if not muted
    # -------------------------------------------------------
    if (messagechannel == gv.MIDI_CHANNEL) and (gv.midi_mute == False):
        midinote = message[1] if len(message) > 1 else None
        velocity = message[2] if len(message) > 2 else None

        if messagetype==8 or messagetype==9:           # We may have a note on/off
            retune=0
            i=getindex(midinote,gv.notemapping)
            if i>-1:      # do we have a mapped note ?
                if gv.notemapping[i][2]==-2:      # This key is actually a CC = control change
                    if velocity==0 or messagetype==8: midinote=0
                    ControlChange(gv.NOTES_CC, midinote)
                    return  
                midinote=gv.notemapping[i][2]
                retune=gv.notemapping[i][3]
                if gv.notemapping[i][4]>0:
                    setVoice(gv.notemapping[i][4],-1)
            if velocity==0: messagetype=8           # prevent complexity in the rest of the checking
            if midinote>(127-gv.stop127) and midinote<gv.stop127:
                keyboardarea=True
            else:
                keyboardarea=False
            #if gv.triggernotes[midinote]==midinote and velocity==64: # Older MIDI implementations
            #    messagetype=8                                        # (like Roland PT-3100)
            if arp.active and keyboardarea:
                arp.note_onoff(messagetype, midinote, velocity, velocity_mode, VELSAMPLE)
                return
            if messagetype==8:                      # should this note-off be ignored?
                if midinote in gv.playingnotes and gv.triggernotes[midinote]<128:
                       for m in gv.playingnotes[midinote]:
                           if m.playingstopnote() < 128:    # are we in a special mode
                               return                       # if so, then ignore this note-off
                else:
                    return                                  # nothing's playing, so there is nothing to stop
            if messagetype == 9:    # is a note-off hidden in this note-on ?
                if midinote in gv.playingnotes:     # this can only be if the note is already playing
                    for m in gv.playingnotes[midinote]:
                        xnote=m.playingstopnote()   # yes, so check it's stopnote
                        if xnote>-1 and xnote<128:  # not in once or keyboard mode
                            if midinote==xnote:     # could it be a push-twice stop?
                                #if gv.sample_mode==PLAYMONO and midinote!=m.playingnote():
                                #    pass    # ignore the chord generated notes when playing monophonic
                                if m.playingstopmode()==3:  # backtracks end on sample end
                                    m.playing2end()         # so just let it finish
                                    playingbacktracks-=1
                                    return
                                else:
                                    messagetype = 8                     # all the others have an instant end
                            elif midinote >= gv.stop127:   # could it be mirrored stop?
                                if (midinote-127) in gv.playingnotes:  # is the possible mirror note-on active?
                                    for m in gv.playingnotes[midinote-127]:
                                        if midinote==m.playingstopnote():   # and has it mirrored stop?
                                            messagetype = 8

            if messagetype == 9:    # Note on 
                #print 'Note on %d, voice=%d, chord=%s in %s/%s, velocity=%d, gv.globalgain=%d' % (midinote, gv.currvoice, gv.chordname[gv.currchord], gv.sample_mode, velocity_mode, velocity, gv.globalgain) #debug
                if gv.sample_mode == PLAYMONO:     # monophonic: new note stops all that's playing in the keyboard range
                    for playnote in xrange(127-gv.stop127, gv.stop127):     # so leave the effects range out of this
                        if playnote in gv.playingnotes:
                            for m in gv.playingnotes[playnote]: 
                                if sustain:
                                    gv.sustainplayingnotes.append(m)
                                else:
                                    m.fadeout()
                                gv.playingnotes[playnote] = []
                                gv.triggernotes[playnote] = 128  # housekeeping
                                # In this mode we ignore the relsamples. I see no use and it makes previous code more complex
                try:
                    if velocity_mode == VELSAMPLE:
                        velmixer = 127
                    else:
                        velmixer = velocity
                    gv.last_midinote=midinote      # save original midinote for the webgui
                    if keyboardarea:
                        gv.last_musicnote=midinote-12*int(midinote/12) # do a "remainder midinote/12" without having to import the full math module
                        if gv.currscale>0:               # scales require a chords mix
                            gv.currchord = gv.scalechord[gv.currscale][gv.last_musicnote]
                        playchord=gv.currchord
                    else:
                        gv.last_musicnote=12 # Set musicnotesymbol to "effects" in webgui
                        playchord=0       # no chords outside keyboardrange / in effects channel.
                    for n in range (len(gv.chordnote[playchord])):
                        playnote=midinote+gv.chordnote[playchord][n]
                        # next code taken way to test if resonance improves without nasty side effects
                        # as the polyphony guard has been improved by processing the eldest notes first
                        #for m in gv.sustainplayingnotes:    # safeguard polyphony:
                        #    if m.note == playnote:          # ..don't sustain double notes
                        #        m.fadeout(False)            # ..but damp them
                        if gv.triggernotes[playnote] < 128: # cleanup in case of retrigger
                            if playnote in gv.playingnotes: # occurs in once/loops modes and chords
                                for m in gv.playingnotes[playnote]:
                                    if m.sound.retrigger!='Y':  # playing double notes not allowed
                                        if m.sound.retrigger=='R':
                                            m.fadeout(True)     # ..either release
                                        else:
                                            m.fadeout(False)    # ..or damp
                                    #gv.playingnotes[playnote]=[]   # housekeeping
                        #print "start playingnotes playnote %d, velocity %d, gv.currvoice %d, velmixer %d" %(playnote, velocity, gv.currvoice, velmixer)
                        if gv.CHOrus:
                            gv.playingnotes.setdefault(playnote,[]).append(gv.samples[playnote, velocity, gv.currvoice].play(midinote, playnote, velmixer*gv.globalgain*gv.CHOgain, 0, retune))
                            gv.playingnotes.setdefault(playnote,[]).append(gv.samples[playnote, velocity, gv.currvoice].play(midinote, playnote, velmixer*gv.globalgain*gv.CHOgain, 2, retune-(gv.CHOdepth/2+1))) #5
                            gv.playingnotes.setdefault(playnote,[]).append(gv.samples[playnote, velocity, gv.currvoice].play(midinote, playnote, velmixer*gv.globalgain*gv.CHOgain, 5, retune+gv.CHOdepth)) #8
                        else:
                            gv.playingnotes.setdefault(playnote,[]).append(gv.samples[playnote, velocity, gv.currvoice].play(midinote, playnote, velmixer*gv.globalgain, 0, retune))
                        for m in gv.playingnotes[playnote]:
                            if m.playingstopmode()== 3:
                                playingbacktracks+=1
                            else:
                                gv.triggernotes[playnote]=midinote   # we are last playing this one
                            if keyboardarea and damp:
                                if m.playingstopmode()!= 3:    # don't damp backtracks
                                    if sustain:  # damplast (=play untill pedal released
                                        gv.sustainplayingnotes.append(m)
                                    else:           # damp+dampnew (=damp played notes immediately)
                                        m.fadeout(False)
                                    gv.triggernotes[playnote]=128
                                    gv.playingnotes[playnote]=[]
                except:
                    print 'Unassigned/unfilled note or other exception in note %d' % (midinote)
                    pass

            elif messagetype == 8:  # Note off
                #print 'Note off ' + str(midinote) + ', voice=' + str(gv.currvoice)    #debug
                for playnote in xrange(128):
                    if gv.triggernotes[playnote] == midinote:   # did we make this one play ?
                        if playnote in gv.playingnotes:
                            for m in gv.playingnotes[playnote]:
                                velmixer = m.playingvelocity()  # save org value for release sample
                                stopmode = m.playingstopmode()
                                if stopmode == 3:
                                    m.playing2end()
                                elif sustain:    # sustain only works for mode=keyb notes in the keyboard area
                                    if stopmode==128 and keyboardarea:
                                        gv.sustainplayingnotes.append(m)
                                else:
                                    m.fadeout()
                                gv.playingnotes[playnote] = []
                                gv.triggernotes[playnote] = 128  # housekeeping
                                if  RELSAMPLE == 'E':
                                    gv.playingnotes.setdefault(playnote,[]).append(gv.samples[playnote, velocity, gv.currvoice].play(midinote, playnote, velmixer*gv.globalgain, -1, retune))

        elif messagetype == 12: # Program change
            gv.PRESET = midinote+gv.PRESETBASE
            LoadSamples()

        elif messagetype == 14: # Pitch Bend (velocity contains MSB, note contains 0 or LSB if supported by controller)
            PitchWheel(midinote,velocity)

        elif messagetype == 11: # control change (CC = Continuous Controllers)
            ControlChange(midinote,velocity)

gv.MidiCallback=MidiCallback

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
gv.LoadSamples=LoadSamples              # and announce the procs to modules

def ActuallyLoad():    
    global velocity_mode, RELSAMPLE
    gv.ActuallyLoading=True
    #print 'Entered ActuallyLoad'
    AllNotesOff()
    gv.currbase = gv.basename    

    gv.samplesdir = SAMPLES_ONUSB if os.listdir(SAMPLES_ONUSB) else SAMPLES_INBOX      # use builtin folder (containing 0 Saw) if no user media containing samples has been found
    #gv.basename = next((f for f in os.listdir(gv.samplesdir) if f.startswith("%d " % gv.PRESET)), None)      # or next(glob.iglob("blah*"), None)
    presetlist=[]
    try:
        for f in os.listdir(gv.samplesdir):
            if re.match(r'[0-9]* .*', f):
                if os.path.isdir(os.path.join(gv.samplesdir,f)):
                    p=int(re.search('\d* ', f).group(0).strip())
                    presetlist.append([p,f])
                    if p==gv.PRESET: gv.basename=f
        presetlist=sorted(presetlist,key=lambda presetlist: presetlist[0])  # sort without having to import operator modules
    except:
        print "Error reading %s" %gv.samplesdir
    gv.presetlist=presetlist
    if gv.basename=="None":
        if len(gv.presetlist)>0:
            gv.PRESET=gv.presetlist[0][0]
            gv.basename=gv.presetlist[0][1]
            print "Missing default preset=0, first available is %d" %gv.PRESET
        else: print "No sample sets found"

    print "We have %s, we want %s" %(gv.currbase, gv.basename)
    if gv.basename:
        if gv.basename == gv.currbase:      # don't waste time reloading a patch
            gv.ActuallyLoading=False
            display("")
            return
        dirname = os.path.join(gv.samplesdir, gv.basename)

    mode=[]
    gv.globalgain = 1
    gv.currvoice = 0
    gv.currnotemap=""
    gv.notemapping=[]
    gv.sample_mode=BOXSAMPLE_MODE   # fallback to the samplerbox default
    velocity_mode=BOXVELOCITY_MODE  # fallback to the samplerbox default
    gv.stop127=BOXSTOP127           # fallback to the samplerbox default
    gv.pitchnotes=PITCHRANGE        # fallback to the samplerbox default
    PRERELEASE=BOXRELEASE           # fallback to the samplerbox default
    PREDAMP=BOXDAMP                 # fallback to the samplerbox default
    PRERETRIGGER=BOXRETRIGGER       # fallback to the samplerbox default
    PREXFADEOUT=BOXXFADEOUT         # fallback to the samplerbox default
    PREXFADEIN=BOXXFADEIN           # fallback to the samplerbox default
    PREXFADEVOL=BOXXFADEVOL         # fallback to the samplerbox default
    PREFRACTIONS=1                  # 1 midinote for 1 semitone for note filling; fractions=2 fills Q-notes = the octave having 24 notes in equal intervals
    PREQNOTE="N"                    # The midinotes mapping the quarternotes (No/Yes/Even/Odd)
    PRENOTEMAP=""
    RELSAMPLE='N'
    PRETRANSPOSE=0
    gv.samples = {}
    fillnotes = {}
    fillnote = 'Y'          # by default we will fill/generate missing notes
    gv.btracklist=[]
    tracknames  = []
    for backtrack in range(128):
        tracknames.append([False, "", ""])
    gv.voicelist =[]
    voicenames  = []
    for voice in range(128):
        voicenames.append([voice, str(voice)])
    voicemodes = [""]*128
    voicenotemap= [""]*128
    voiceqnote = ["N"]*128
    gv.DefinitionTxt = ''
    gv.DefinitionErr = ''

    if not gv.basename: 
        #print 'Preset empty: %s' % gv.PRESET
        gv.ActuallyLoading=False
        gv.basename = "%d Empty preset" %gv.PRESET
        display("","E%03d" % gv.PRESET)
        return

    #print 'Preset loading: %s ' % gv.basename
    display("Loading %s" % gv.basename,"L%03d" % gv.PRESET)
    getcsv.readnotemap(os.path.join(dirname, gv.NOTEMAP_DEF))
    gv.CCmapSet=getcsv.readCCmap(os.path.join(dirname, gv.CTRLMAP_DEF), True)
    definitionfname = os.path.join(dirname, gv.SAMPLESDEF)
    if os.path.isfile(definitionfname):
        if USE_HTTP_GUI:
            with open(definitionfname, 'r') as definitionfile:  # keep full text for the gui
                gv.DefinitionTxt=definitionfile.read()
        with open(definitionfname, 'r') as definitionfile:
            for i, pattern in enumerate(definitionfile):
                try:
                    if len(pattern.strip())==0 or pattern[0]=="#":
                        continue
                    if r'%%transpose' in pattern:
                        PRETRANSPOSE = (int(pattern.split('=')[1].strip()))
                    if r'%%gain' in pattern:
                        gv.globalgain = abs(float(pattern.split('=')[1].strip()))
                        continue
                    if r'%%stopnotes' in pattern:
                        gv.stop127 = (int(pattern.split('=')[1].strip()))
                        if gv.stop127 > 127 or gv.stop127 < 64:
                            print "Stopnotes start of %d invalid, set to %d" % (gv.stop127, BOXSTOP127)
                            gv.stop127 = BOXSTOP127
                        continue
                    if r'%%release' in pattern:
                        PRERELEASE = (int(pattern.split('=')[1].strip()))
                        if PRERELEASE > 127:
                            print "Release of %d limited to %d" % (PRERELEASE, 127)
                            PRERELEASE = 127
                        continue
                    if r'%%damp' in pattern:
                        PREDAMP = (int(pattern.split('=')[1].strip()))
                        if DAMP > 127:
                            print "Damp of %d limited to %d" % (PREDAMP, 127)
                            PREDAMP = 127
                        continue
                    if r'%%retrigger' in pattern:
                        m = pattern.split('=')[1].strip().title()
                        if m == 'R' or m == 'D' or m == 'Y':
                            PRERETRIGGER = m
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
                    if r'%%qnote' in pattern:
                        m = pattern.split('=')[1].strip().title()
                        if m == 'Y' or m == 'O' or m == 'E':
                            PREQNOTE = m
                        continue
                    #if r'%%fractions' in pattern:
                    #    PREFRACTIONS = abs(int(pattern.split('=')[1].strip()))
                    #    if PREFRACTIONS<1:
                    #        print "Fractions %d set to 1" % PREFRACTIONS
                    #        PREFRACTIONS = 1
                    #    continue
                    if r'%%pitchbend' in pattern:
                        gv.pitchnotes = abs(int(pattern.split('=')[1].strip()))
                        if gv.pitchnotes > 12:
                            print "Pitchbend of %d limited to 12" % gv.pitchnotes
                            gv.pitchnotes = 12
                        gv.pitchnotes *= 2     # actually it is 12 up and 12 down
                        continue
                    if r'%%mode' in pattern:
                        m = pattern.split('=')[1].strip().title()
                        if (GetStopmode(m)>-2): gv.sample_mode = m
                        continue
                    if r'%%velmode' in pattern:
                        m = pattern.split('=')[1].strip().title()
                        if m==VELSAMPLE or m==VELACCURATE: velocity_mode = m
                        continue
                    if r'%%relsample' in pattern:
                        m = pattern.split('=')[1].strip().title()
                        if m == 'E' or m == 'N':
                            RELSAMPLE = m
                        continue
                    if r'%%backtrack' in pattern:
                        m = pattern.split(':')[1].strip()
                        v,m=m.split("=")
                        if int(v)>127:
                            print "Backtrackname %m ignored" %m
                        else:
                            tracknames[int(v)][1]=m
                        continue
                    if r'%%voice' in pattern:
                        m = pattern.split(':')[1].strip()
                        v,m=m.split("=")
                        if int(v)>127:
                            print "Voicename %m ignored" %m
                        else:
                            voicenames[int(v)]=[int(v),v+" "+m]
                        continue
                    if r'%%notemap' in pattern:
                        PRENOTEMAP = pattern.split('=')[1].strip().title()
                        continue
                    defaultparams = { 'midinote':'-128', 'velocity':'127', 'gain':'1', 'notename':'', 'voice':'1', 'mode':gv.sample_mode, 'transpose':PRETRANSPOSE, 'release':PRERELEASE, 'damp':PREDAMP, 'retrigger':PRERETRIGGER,\
                                      'xfadeout':PREXFADEOUT, 'xfadein':PREXFADEIN, 'xfadevol':PREXFADEVOL, 'qnote':PREQNOTE, 'notemap':PRENOTEMAP, 'fillnote':fillnote, 'backtrack':'-1'}
                    if len(pattern.split(',')) > 1:
                        defaultparams.update(dict([item.split('=') for item in pattern.split(',', 1)[1].replace(' ','').replace('%', '').split(',')]))
                    pattern = pattern.split(',')[0]
                    pattern = re.escape(pattern.strip())
                    pattern = pattern.replace(r"\%midinote", r"(?P<midinote>\d+)").replace(r"\%velocity", r"(?P<velocity>\d+)").replace(r"\%gain", r"(?P<gain>[-+]?\d*\.?\d+)").replace(r"\%voice", r"(?P<voice>\d+)")\
                                     .replace(r"\%fillnote", r"(?P<fillnote>[YNyn])").replace(r"\%mode", r"(?P<mode>[A-Za-z0-9])").replace(r"\%transpose", r"(?P<transpose>\d+)").replace(r"\%release", r"(?P<release>\d+)")\
                                     .replace(r"\%damp", r"(?P<damp>\d+)").replace(r"\%retrigger", r"(?P<retrigger>[YyRrDd])").replace(r"\%xfadeout", r"(?P<xfadeout>\d+)").replace(r"\%xfadein", r"(?P<xfadein>\d+)")\
                                     .replace(r"\%qnote", r"(?P<qnote>[YyNnOoEe])").replace(r"\%notemap", r"(?P<notemap>[A-Za-z0-9]\_\-\&)")\
                                     .replace(r"\%backtrack", r"(?P<backtrack>\d+)").replace(r"\%notename", r"(?P<notename>[A-Ga-g][#ks]?[0-9])").replace(r"\*", r".*?").strip()    # .*? => non greedy
                    for fname in os.listdir(dirname):
                        if LoadingInterrupt:
                            #print 'Loading % s interrupted...' % dirname
                            gv.ActuallyLoading=False
                            return
                        m = re.match(pattern, fname)
                        if m:
                            #print 'Processing ' + fname
                            mem=psutil.virtual_memory()
                            if mem.percent>MAX_MEMLOAD:
                                print "'%s' skipped because memory reached %d%%" %(fname,mem.percent)
                                continue
                            info = m.groupdict()
                            midinote = int(info.get('midinote', defaultparams['midinote']))
                            notename = info.get('notename', defaultparams['notename'])
                            mode = info.get('mode', defaultparams['mode']).strip().title()
                            retrigger = info.get('retrigger', defaultparams['retrigger']).strip().title()
                            backtrack = int(info.get('backtrack', defaultparams['backtrack']))
                            if mode==BACKTRACK and backtrack<0: backtrack=0
                            if backtrack>-1 and backtrack<128:
                                if not (backtrack>0 and tracknames[backtrack][0]):
                                    mode=BACKTRACK
                                    voice=0
                                    if backtrack>0:
                                        tracknames[backtrack][0]=True
                                        if tracknames[backtrack][1]=="":
                                            tracknames[backtrack][1]=fname[:-4]
                                        tracknames[backtrack][2]=""
                                else:
                                    print "Backtrack %s ignored" %fname
                                    continue
                            else:
                                voice=int(info.get('voice', defaultparams['voice']))
                            if voice == 0:          # the override / special effects voice cannot fill
                                voicefillnote = 'N' # so we ignore whatever the user wants (RTFM)
                            elif voice<128:
                                voicefillnote = (info.get('fillnote', defaultparams['fillnote'])).title().rstrip()
                            else:
                                print "Voice %d ignored" %voice
                                continue
                            #print 'Processing %s, voice %d ' %(fname,voice)
                            qnote = info.get('qnote', defaultparams['qnote']).title()[0][:1] 
                            if qnote == 'Y': qnote = 'O'    # the default for qnotes is on odd midi notes (60=C).
                            fractions = PREFRACTIONS        # not yet implemented for user change (future??)
                            if qnote != 'N':
                                voiceqnote[voice] = qnote   # pick the latest; we can't check everything, RTFM :-)
                                if fractions == 1:          # condition needed in future
                                    fractions=2             # for now always true
                            voicenotemap[voice] = info.get('notemap', defaultparams['notemap']).strip().title()   # pick the latest; we can't check everything, RTFM :-)
                            if notename:
                                midinote=notename2midinote(notename,fractions)
                            transpose = int(info.get('transpose', defaultparams['transpose']))
                            if voice != 0:          # the override / special effects voice cannot transpose
                                midinote-=transpose
                            if (midinote < 0 or midinote > 127):
                                if backtrack >0:    # Keep the backtrackknob when note is unplayable
                                    midinote=-1
                                else:
                                    print "%s: ignored notename / midinote in voice %d: '%s'/%d" %(fname, voice, notename, midinote)
                                    continue
                            if backtrack > -1:
                                if midinote >-1:
                                    if notename:tracknames[backtrack][2]=notename
                                    else:       tracknames[backtrack][2]="%d" %midinote
                                else:           tracknames[backtrack][2]=""
                            if backtrack==0:
                                if tracknames[0][0]:
                                    tracknames[0][1]="Multiple tracks"
                                    tracknames[0][2]=".."
                                else:
                                    tracknames[0][0]=True
                                    tracknames[0][1]=fname[:-4]
                            velocity = int(info.get('velocity', defaultparams['velocity']))
                            gain = abs(float((info.get('gain', defaultparams['gain']))))
                            release = int(info.get('release', defaultparams['release']))
                            if (release>127): release=127
                            damp = int(info.get('damp', defaultparams['damp']))
                            if (damp>127): damp=127
                            xfadeout = int(info.get('xfadeout', defaultparams['xfadeout']))
                            if (xfadeout>127): xfadeout=127
                            xfadein = int(info.get('xfadein', defaultparams['xfadein']))
                            if (xfadein>127): xfadein=127
                            xfadevol = abs(float(info.get('xfadevol', defaultparams['xfadevol'])))
                            if (GetStopmode(mode)<-1) or (GetStopmode(mode)==127 and midinote>(127-gv.stop127)):
                                print "invalid mode '%s' or note %d out of range, set to keyboard mode." % (mode, midinote)
                                mode=PLAYLIVE
                            try:
                                if backtrack>-1:    # Backtracks are intended for start/stop via controller, so we can use unplayable notes
                                    gv.samples[130+backtrack, velocity, voice] = Sound(os.path.join(dirname, fname), voice, 130+backtrack, velocity, mode, release, damp, retrigger, gain, xfadeout, xfadein, xfadevol, fractions)
                                if midinote>-1:
                                    gv.samples[midinote, velocity, voice] = Sound(os.path.join(dirname, fname), voice, midinote, velocity, mode, release, damp, retrigger, gain, xfadeout, xfadein, xfadevol, fractions)
                                    fillnotes[midinote, voice] = voicefillnote
                                    if voicemodes[voice]=="" or mode==PLAYMONO: voicemodes[voice]=mode
                                    elif voicemodes[voice]!=PLAYMONO and voicemodes[voice]!=mode: voicemodes[voice]="Mixed"
                            except: pass    # Error should be handled & communicated in subprocs
                except:
                    m=i+1
                    v=""
                    print "Error in definition file, skipping line %d." % (m)
                    if gv.DefinitionErr != "" : v=", "
                    gv.DefinitionErr="%s%s%d" %(gv.DefinitionErr,v,m)
    else:
        for midinote in range(128):
            if LoadingInterrupt:
                gv.ActuallyLoading=False
                return
            file = os.path.join(dirname, "%d.wav" % midinote)
            #print "Trying " + file
            if os.path.isfile(file):
                #print "Processing " + file
                gv.samples[midinote, 127, 1] = Sound(file, 1, midinote, 127, gv.sample_mode, PRERELEASE, PREDAMP, PRERETRIGGER, gv.globalgain, PREXFADEOUT, PREXFADEIN, PREXFADEVOL, PREFRACTIONS)
                fillnotes[midinote, 1] = fillnote
        voicenames[1]=[1,"Default"]
        voicemodes[1]=gv.sample_mode

    initial_keys = set(gv.samples.keys())
    if len(initial_keys) > 0:
        for voice in xrange(128):
            if voicemodes[voice]=="": continue
            #print "Complete info for voice %d" % (voice)
            v=getindex(voice, voicenames)
            gv.voicelist.append([voice, voicenames[v][1], voicemodes[voice], voicenotemap[voice]])
            if gv.currvoice==0:     # make sure to start with a playable non-empty voice
                setVoice(voice,1)
            for midinote in xrange(128):    # first complete velocities in found normal notes
                lastvelocity = None
                for velocity in xrange(128):
                    if (midinote, velocity, voice) in initial_keys:
                        if not lastvelocity:
                            for v in range(velocity): gv.samples[midinote, v, voice] = gv.samples[midinote, velocity, voice]
                        lastvelocity = gv.samples[midinote, velocity, voice]
                    else:
                        if lastvelocity:
                            gv.samples[midinote, velocity, voice] = lastvelocity
            initial_keys = set(gv.samples.keys())  # we got more keys, but not enough yet
            lastlow = -130                      # force lowest unfilled notes to be filled with the nexthigh
            nexthigh = None                     # nexthigh not found yet, and start filling the missing notes
            for midinote in xrange(128-gv.stop127, gv.stop127):    # only fill the keyboard area.
                if (midinote, 1, voice) in initial_keys:
                    if fillnotes[midinote, voice] == 'Y':  # can we use this note for filling?
                        nexthigh = None                     # passed nexthigh
                        lastlow = midinote                  # but we got fresh low info
                else:
                    if not nexthigh:
                        nexthigh=260    # force highest unfilled noteLoadSampless to be filled with the lastlow
                        for m in xrange(midinote+1, 128):
                            if (m, 1, voice) in initial_keys:
                                if fillnotes[m, voice] == 'Y':  # can we use this note for filling?
                                    if m < nexthigh: nexthigh=m
                    if (nexthigh-lastlow) > 260:    # did we find a note valid for filling?
                        break                       # no, stop trying
                    if midinote <= 0.5+(nexthigh+lastlow)/2: m=lastlow
                    else: m=nexthigh
                    #print "Note %d will be generated from %d" % (midinote, m)
                    for velocity in xrange(128):
                        gv.samples[midinote, velocity, voice] = gv.samples[m, velocity, voice]

        if voicemodes[0]!="":                       # do we have the override / special effects voice ?
            for midinote in xrange(128):
                if (midinote, 0) in fillnotes:
                   for voice in xrange(1,128):
                       if voicemodes[voice]!="":
                           #print "Override note %d in voice %d" % (midinote, voice)
                           for velocity in xrange(128):
                               gv.samples[midinote, velocity, voice] = gv.samples[midinote, velocity, 0]

        for track in xrange(128):
            if tracknames[track][0]:
                gv.btracklist.append([track, tracknames[track][1], tracknames[track][2]])
        if gv.currvoice!=0: gv.sample_mode=gv.voicelist[getindex(gv.currvoice,gv.voicelist)][2]

        gv.ActuallyLoading=False
        mem=psutil.virtual_memory()
        print "Loaded '%s', %d%% free memory left" %(gv.basename, 100-mem.percent)
        display("","%04d" % gv.PRESET)

    else:
        print 'Preset empty: ' + str(gv.PRESET)
        gv.basename = "%d Empty preset" %gv.PRESET
        gv.ActuallyLoading=False
        display("","E%03d" % gv.PRESET)

#########################################
##  LOAD FIRST SOUNDBANK
#########################################     

LoadSamples()

#########################################
##      O P T I O N A L S        
##  - DAC volume control via alsamixer
##  - BUTTONS via GPIO
##  - WebGUI thread
##  - MIDI IN via SERIAL PORT
#########################################

try:

    gv.getvolume=gv.NoProc
    gv.setvolume=gv.NoProc
    if gv.USE_ALSA_MIXER:
        import DACvolume

    if USE_BUTTONS:
        USE_GPIO=True
        import buttons

    if USE_HTTP_GUI:
        import http_gui

    if USE_SERIALPORT_MIDI:
        import serialMIDI

except:
    print "Error loading optionals, can be alsa-mixer, buttons, http-gui or serial-midi"
    time.sleep(0.5)
    GPIOcleanup()
    exit(1)

#########################################
##  MIDI DEVICES DETECTION
##  MAIN LOOP
#########################################

midi_in = rtmidi2.MidiInMulti()
midi_in.callback = MidiCallback
curr_inports = []
prev_inports = []
try:
  while True:
    curr_inports = rtmidi2.get_in_ports()
    if (len(prev_inports) != len(curr_inports)):
        midi_in.close_ports()
        prev_ports = []
        i=0
        for port in curr_inports:
            if 'Midi Through' not in port:
                print 'Open %s as MIDI IN %d ' % (port,i)
                midi_in.open_ports(port)
            i+=1
        curr_inports = rtmidi2.get_in_ports()   # we do this indirect to catch
        prev_inports = curr_inports             # auto opened virtual ports
    time.sleep(2)
except KeyboardInterrupt:
    print "\nstopped by user via ctrl-c\n"
except:
    print "\nstopped by unexpected error"
finally:
    display('Stopped')
    time.sleep(0.5)
    GPIOcleanup()
