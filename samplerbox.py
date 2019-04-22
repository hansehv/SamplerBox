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
#   changelog in changelist.txt
#

##########################################################################
##  IMPORT MODULES (generic, more can be loaded depending on local config)
##  WARNING: GPIO modules in this build use mode=BCM. Do not mix modes!
##########################################################################

import wave
import time
import numpy
import sys,os,re
import sounddevice
import threading   
from chunk import Chunk
import struct
import rtmidi2
import ConfigParser
import samplerbox_audio   # audio-module (cython)
rootprefix='/home/hans/Documents/SamplerBox'
if not os.path.isdir(rootprefix):
    rootprefix=""
sys.path.append(rootprefix+'/root/SamplerBox/modules')
import gv,getcsv

########  Define local general functions ########
usleep = lambda x: time.sleep(x/1000000.0)
msleep = lambda x: time.sleep(x/1000.0)
def getindex(key, table, onecol=False):
    for i in range(len(table)):
        if onecol:
            if key==table[i]:   return i
        else:
            if key==table[i][0]:return i
    return -1
def notename2midinote(notename,fractions):
    notenames=["C","CS","C#","DK","D","DS","D#","EK","E","ES","F","FS","F#","GK","G","GS","G#","AK","A","AS","A#","BK","B","BS"]
    notename=notename.upper()
    if notename[:2]=="CK":  # normalize synonyms
        notename="BS%d" %(int(notename[-1])-1) # Octave number switches between B and C
    elif notename[:2]=="FK":
        notename="ES%s"%notename[-1]
    try:
        x=notenames.index(format(notename[:len(notename)-1]))
        if fractions==1:    # we have undivided semi-tones = 12-tone scale
            x,y=divmod(x,2) # so our range is half of what's tested
            if y!=0:        # and we can't process any found q's.
                print "Ignored quartertone %s as we are in 12-tone mode" %notename
                midinote=-1
            # next statements places note 60 on C4
            else:            # 12 note logic
                midinote = x + (int(notename[-1])+1) * 12
        else:               # 24 note logic
            midinote = x + (int(notename[-1])-2) * 24 +12
    except:
        print "Ignored unrecognized notename '%s'" %notename
        midinote=-128
    return midinote
def retune(voice,note,cents):   # 100 cents is a semitone
    for velocity in xrange(128):
        gv.samples[note,velocity,voice].retune=cents*PITCHSTEPS/100
def setMC(mc,proc):
    gv.MC[getindex(mc,gv.MC)][2]=proc
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
def setVoice(x, i=0, *z):
    global CCmap
    if i==0:
        xvoice=int(x)
    else:
        xvoice=getindex(int(x),gv.voicelist)
    if xvoice>-1:                       # ignore if undefined
        voice=gv.voicelist[xvoice][0]
        if voice!=gv.currvoice:         # also ignore if active
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
notemap=[]
def setNotemap(x, *z):
    global notemap
    if x!=gv.currnotemap:
        gv.currnotemap=x
	notemap=[]
        for i in xrange(len(gv.notemap)):       # do we have note mapping ?
            if gv.notemap[i][0]==gv.currnotemap:
                notemap.append(gv.notemap[i])
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

gv.getindex=getindex                    # and announce the procs to modules
gv.retune=retune
gv.notename2midinote=notename2midinote
gv.MC[getindex(gv.CHORDS,gv.MC)][2]=setChord
gv.MC[getindex(gv.SCALES,gv.MC)][2]=setScale
gv.MC[getindex(gv.VOICES,gv.MC)][2]=setVoice
gv.MC[getindex(gv.BACKTRACKS,gv.MC)][2]=playBackTrack

########  LITERALS ########
PLAYLIVE = "Keyb"                       # reacts on "keyboard" interaction
PLAYBACK = "Once"                       # ignores loop markers ("just play the sample with option to stop")
PLAYBACK2X = "Onc2"                     # ignores loop markers with note-off by same note
PLAYLOOP = "Loop"                       # recognize loop markers, note-off by 127-note
PLAYLOOP2X = "Loo2"                     # recognize loop markers, note-off by same note
BACKTRACK = "Back"                      # recognize loop markers, loop-off by same note or controller
PLAYMONO = "Mono"                       # monophonic (with chords), loop like Loo2, but note/chord stops when next note is played.
VELSAMPLE = "Sample"                    # velocity equals sampled value, requires multiple samples to get differentation
VELACCURATE = "Accurate"                # velocity as played, allows for multiple (normalized!) samples for timbre
SAMPLES_INBOX = rootprefix+"/samples/"  # Builtin directory containing the sample-sets.
SAMPLES_ONUSB = rootprefix+"/media/"    # USB-Mount directory containing the sample-sets.
CONFIG_LOC = rootprefix+"/boot/samplerbox/"
CHORDS_DEF = "chords.csv"
SCALES_DEF = "scales.csv"
CTRLCCS_DEF = "controllerCCs.csv"
CTRLMAP_DEF = "CCmap.csv"
KEYNAMES_DEF = "keynotes.csv"
NOTEMAP_DEF = "notemap.csv"

##########  read LOCAL CONFIG ==> /boot/samplerbox/configuration.txt
gv.cp=ConfigParser.ConfigParser()
gv.cp.read(CONFIG_LOC + "configuration.txt")
s="config"
AUDIO_DEVICE_ID = gv.cp.getint(s,"AUDIO_DEVICE_ID".lower())
USE_SERIALPORT_MIDI = gv.cp.getboolean(s,"USE_SERIALPORT_MIDI".lower())
USE_HD44780_16x2_LCD = gv.cp.getboolean(s,"USE_HD44780_16x2_LCD".lower())
USE_OLED = gv.cp.getboolean(s,"USE_OLED".lower())
OLED_DRIVER = gv.cp.get(s,"OLED_DRIVER".lower())
USE_I2C_7SEGMENTDISPLAY = gv.cp.getboolean(s,"USE_I2C_7SEGMENTDISPLAY".lower())
gv.USE_ALSA_MIXER = gv.cp.getboolean(s,"USE_ALSA_MIXER".lower())
USE_48kHz = gv.cp.getboolean(s,"USE_48kHz".lower())
USE_BUTTONS = gv.cp.getboolean(s,"USE_BUTTONS".lower())
USE_LEDS = gv.cp.getboolean(s,"USE_LEDS".lower())
gv.MIDI_CHANNEL = gv.cp.getint(s,"MIDI_CHANNEL".lower())
gv.PRESET = gv.cp.getint(s,"PRESET".lower())
gv.PRESETBASE = gv.cp.getint(s,"PRESETBASE".lower())
MAX_POLYPHONY = gv.cp.getint(s,"MAX_POLYPHONY".lower())
BOXSAMPLE_MODE = gv.cp.get(s,"BOXSAMPLE_MODE".lower())
BOXVELOCITY_MODE = gv.cp.get(s,"BOXVELOCITY_MODE".lower())
BOXSTOP127 = gv.cp.getint(s,"BOXSTOP127".lower())
BOXRELEASE = gv.cp.getint(s,"BOXRELEASE".lower())
BOXDAMP = gv.cp.getint(s,"BOXDAMP".lower())
BOXRETRIGGER = gv.cp.get(s,"BOXRETRIGGER".lower())
RELSAMPLE= gv.cp.get(s,"RELSAMPLE".lower())
BOXXFADEOUT = gv.cp.getint(s,"BOXXFADEOUT".lower())
BOXXFADEIN = gv.cp.getint(s,"BOXXFADEIN".lower())
BOXXFADEVOL = gv.cp.getfloat(s,"BOXXFADEVOL".lower())
PITCHRANGE = gv.cp.getint(s,"PITCHRANGE".lower())
PITCHBITS = gv.cp.getint(s,"PITCHBITS".lower())
BOXFVroomsize = gv.cp.getfloat(s,"BOXFVroomsize".lower())*127
BOXFVdamp = gv.cp.getfloat(s,"BOXFVdamp".lower())*127
BOXFVlevel = gv.cp.getfloat(s,"BOXFVlevel".lower())*127
BOXFVwidth = gv.cp.getfloat(s,"BOXFVwidth".lower())*127
BOXVIBRpitch = gv.cp.getfloat(s,"BOXVIBRpitch".lower())
BOXVIBRspeed = gv.cp.getint(s,"BOXVIBRspeed".lower())
BOXVIBRtrill = gv.cp.getboolean(s,"BOXVIBRtrill".lower())
BOXTREMampl = gv.cp.getfloat(s,"BOXTREMampl".lower())
gv.BOXTREMspeed = gv.cp.getint(s,"BOXTREMspeed".lower())
BOXTREMtrill = gv.cp.getboolean(s,"BOXTREMtrill".lower())
USE_HTTP_GUI = gv.cp.getboolean(s,"USE_HTTP_GUI".lower())
gv.volume = gv.cp.getint(s,"volume".lower())
gv.volumeCC = gv.cp.getfloat(s,"volumeCC".lower())

########## read CONFIGURABLE TABLES from config dir

# Definition of notes, chords and scales
getcsv.readchords(CONFIG_LOC + CHORDS_DEF)
getcsv.readscales(CONFIG_LOC + SCALES_DEF)

# Midi controllers and keys mapping
getcsv.readcontrollerCCs(CONFIG_LOC + CTRLCCS_DEF)
gv.CCmapBox=getcsv.readCCmap(CONFIG_LOC + CTRLMAP_DEF)
getcsv.readkeynames(CONFIG_LOC + KEYNAMES_DEF)

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
gv.VIBRpitch=1.0*BOXVIBRpitch
gv.VIBRspeed=BOXVIBRspeed
gv.VIBRtrill=BOXVIBRtrill
gv.TREMampl=BOXTREMampl
gv.TREMspeed=gv.BOXTREMspeed
gv.TREMtrill=BOXTREMtrill

if AUDIO_DEVICE_ID > 0:
    if rootprefix=="":
        gv.MIXER_CARD_ID = AUDIO_DEVICE_ID-1   # The jack/HDMI of PI use 1 alsa card index
    else:
        gv.MIXER_CARD_ID = 0                   # This may vary with your HW.....
else:
    gv.MIXER_CARD_ID = 0

#########################################
# Display routine
#########################################

if USE_HD44780_16x2_LCD:
    USE_GPIO=True
    import lcd_16x2
    lcd = lcd_16x2.HD44780()
    def display(s2,s7=""):
        lcd.display(s2,gv.basename,gv.sample_mode,gv.USE_ALSA_MIXER,gv.volume,gv.currvoice,gv.currchord,gv.chordname,gv.scalename,gv.currscale,gv.button_disp,gv.buttfunc)
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

##################################################################################
# Effects/Filters
##################################################################################

def NoProc(x=0,y=0,z=0):
    pass
#
# C++ DLL interface method inspired by Erik Nieuwlands (www.nickyspride.nl/sb2/)
#
import ctypes
from ctypes import *
c_float_p = ctypes.POINTER(ctypes.c_float)
c_short_p = ctypes.POINTER(ctypes.c_short)
c_filters = cdll.LoadLibrary('./filters/interface.so')
#
# Reverb based on Freeverb by Jezar at Dreampoint
# Reverb is costly: about 10% on PI3
#
c_filters.setroomsize.argtypes = [c_float]
c_filters.setdamp.argtypes = [c_float]
c_filters.setwet.argtypes = [c_float]
c_filters.setdry.argtypes = [c_float]
c_filters.setwidth.argtypes = [c_float]
def FVsetroomsize(x,*z):
    gv.FVroomsize=1.0*x/127.0
    c_filters.setroomsize(gv.FVroomsize)
def FVsetdamp(x,*z):
    gv.FVdamp=1.0*x/127.0
    c_filters.setdamp(gv.FVdamp)
def FVsetlevel(x,*z):
    gv.FVlevel=1.0*x/127.0
    c_filters.setwet(gv.FVlevel)
    c_filters.setdry(1-gv.FVlevel)
def FVsetwidth(x,*z):
    gv.FVwidth=1.0*x/127.0
    c_filters.setwidth(gv.FVwidth)
def FVinit():
    FVsetroomsize(BOXFVroomsize)
    FVsetdamp(BOXFVdamp)
    FVsetlevel(BOXFVlevel)
    FVsetwidth(BOXFVwidth)
FVinit()    # init global vars and filter in one step
gv.FVsetlevel=FVsetlevel        # and announce the procs to modules
gv.FVsetroomsize=FVsetroomsize
gv.FVsetdamp=FVsetdamp
gv.FVsetwidth=FVsetwidth
gv.MC[getindex(gv.REVERBLVL,gv.MC)][2]=FVsetlevel   # and to CCmap
gv.MC[getindex(gv.REVERBROOM,gv.MC)][2]=FVsetroomsize
gv.MC[getindex(gv.REVERBDAMP,gv.MC)][2]=FVsetdamp
gv.MC[getindex(gv.REVERBWIDTH,gv.MC)][2]=FVsetwidth
gv.FVinit=FVinit
 
#
# AutoWah
#

#
# Vibrato, tremolo and rotate (poor man's single speaker leslie)
# Being input based, these effects are cheap: less than 1% CPU on PI3
#
import LFO
#
# Filter (de)activation
#
gv.Filters={"None":NoProc,gv.REVERB:c_filters.reverb,gv.VIBRATO:LFO.Vibrato,gv.TREMOLO:LFO.Tremolo,gv.ROTATE:LFO.Rotate}
gv.FilterTidy={"None":NoProc,gv.REVERB:NoProc,gv.VIBRATO:LFO.VibratoTidy,gv.TREMOLO:LFO.TremoloTidy,gv.ROTATE:LFO.RotateTidy}
gv.Filterkeys=gv.Filters.keys()
def setFilter(newfilter):
    if newfilter < len(gv.Filters):
        gv.FilterTidy[gv.Filterkeys[gv.currfilter]](False)
        gv.currfilter=newfilter
        gv.FilterTidy[gv.Filterkeys[gv.currfilter]](True)
        gv.filterproc=gv.Filters[gv.Filterkeys[newfilter]]
setFilter(gv.currfilter)
def setEffect(effect):
    for i in range(len(gv.Filterkeys)):
        if gv.Filterkeys[i]==effect:
            if gv.currfilter==i:
                setFilter(0)
            else:
                setFilter(i)
            continue
# Relate the effects, the CCmapping and control change handling handling to each other
def Reverb(CCval,*z):  setEffect(gv.REVERB)
def Tremolo(CCval,*z): setEffect(gv.TREMOLO)
def Vibrato(CCval,*z): setEffect(gv.VIBRATO)
def Rotate(CCval,*z):  setEffect(gv.ROTATE)
def EffectsOff(*z):
    gv.currfilter=0
    setFilter(gv.currfilter)
    #FVinit()                   # no cleanup necessary
    LFO.RotateTidy(False)       # cleans up vibrato+tremolo+rotate
gv.setFilter=setFilter          # and announce the procs to modules
gv.MC[getindex(gv.REVERB,gv.MC)][2]=Reverb
gv.MC[getindex(gv.TREMOLO,gv.MC)][2]=Tremolo
gv.MC[getindex(gv.VIBRATO,gv.MC)][2]=Vibrato
gv.MC[getindex(gv.ROTATE,gv.MC)][2]=Rotate
gv.MC[getindex(gv.EFFECTSOFF,gv.MC)][2]=EffectsOff

#########################################
##  SLIGHT MODIFICATION OF PYTHON'S WAVE MODULE
##  TO READ CUE MARKERS & LOOP MARKERS if applicable in mode
#########################################

class waveread(wave.Wave_read):
#class waveread():
    def initfp(self, file):
        self._convert = None
        self._soundpos = 0
        self._cue = []
        self._loops = []
        self._ieee = False
        self._file = Chunk(file, bigendian=0)
        if self._file.getname() != 'RIFF':
            print '%s does not start with RIFF id' % (file)
            raise Error, '%s does not start with RIFF id' % (file)
        if self._file.read(4) != 'WAVE':
            print '%s is not a WAVE file' % (file)
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
            except:
                if self._fmt_chunk_read and self._data_chunk:
                    print "Read %s with errors" % (file)
                    break   # we have sufficient data so leave the error as is
                else:
                    print "Skipped %s because of chunk.skip error" %file
                    raise Error, "Error in chunk.skip in %s" % (file)
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
                    print 'data chunk before fmt chunk in %s' % (file)
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
                    print "invalid cue chunk in %s" % (file)
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
                    print "Read %s with errors" % (file)
                    break   # we have sufficient data so leave the error as is
                else:
                    print "Skipped %s because of chunk.skip error" %file
                    raise Error, "Error in chunk.skip in %s" % (file)
        if not self._fmt_chunk_read or not self._data_chunk:
            print 'fmt chunk and/or data chunk missing in %s' % (file)
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
        self.retune = 0
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
SPEEDRANGE = 48     # 2*48=96 is larger than 88, so a (middle) C4-A4 can facilitate largest keyboard
SPEED = numpy.power(2, numpy.arange(-1.0*SPEEDRANGE*PITCHSTEPS, 1.0*SPEEDRANGE*PITCHSTEPS)/(12*PITCHSTEPS)).astype(numpy.float32)

def AudioCallback(outdata, frame_count, time_info, status):
    p=len(gv.playingsounds)-MAX_POLYPHONY
    if p>0:
        print "MAX_POLYPHONY %d exceeded with %d notes" %(MAX_POLYPHONY,p)
        for i in xrange(p+playingbacktracks-1):
            if gv.playingsounds[i].playingstopmode()!=3:    # let the backtracks be
                del gv.playingsounds[i]     # get it out of the system
    # audio-module:
    rmlist = []
    b = samplerbox_audio.mixaudiobuffers(gv.playingsounds, rmlist, frame_count, FADEOUT, FADEOUTLENGTH, SPEED, SPEEDRANGE, gv.PITCHBEND+gv.VIBRvalue+PITCHCORR, PITCHSTEPS)
    for e in rmlist:
        try:
            if e.sound.stopmode==3 or e.sound.stopmode==-1:     # keep track of backtrack/once status
                gv.playingnotes[e.note]=[]
            gv.playingsounds.remove(e)
        except: pass
    #b_temp = b
    gv.filterproc(b.ctypes.data_as(c_float_p), b.ctypes.data_as(c_float_p), frame_count)
    b *= (10**(gv.TREMvalue*gv.volumeCC)-1)/9     # linear doesn't sound natural, this may be to complicated too though...
    outdata[:] = b.reshape(outdata.shape)
    # Use the module as timer for ledblinks
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
except:
    display("Invalid audiodev")
    print 'Invalid audio device #%i' % AUDIO_DEVICE_ID
    time.sleep(0.5)
    if USE_GPIO:
        import RPi.GPIO as GPIO
        GPIO.cleanup()
    exit(1)

#########################################
##  MIDI
##   - general routines
##   - CALLBACK
#########################################

def AllNotesOff(x=0,*z):
    global playingbacktracks
    playingbacktracks = 0
    gv.playingsounds = []
    gv.playingnotes = {}
    gv.sustainplayingnotes = []
    gv.triggernotes = [128]*128     # fill with unplayable note
    EffectsOff()
    AutoChordOff()
    #display("")    #also in AutoChordOff
def MidiVolume(CCval,*z):
    gv.volumeCC = CCval / 127.0
def AutoChordOff(x=0,*z):
    gv.currchord = 0
    gv.currscale = 0
    display("")
def PitchWheel(LSB,MSB=0,*z):
    gv.PITCHBEND=(((128*MSB+LSB)/gv.pitchdiv)-gv.pitchneutral)*gv.pitchnotes
def ModWheel(CCval,*z):
    pass        # still in idea stage
def Sustain(CCval,*z):
    if gv.sample_mode==PLAYLIVE or gv.sample_mode==PLAYMONO:
        if (CCval == 0):    # sustain off
            gv.sustain = False
            for n in gv.sustainplayingnotes:
                n.fadeout()
            gv.sustainplayingnotes = []       
        else:               # sustain on
            gv.sustain = True
def Damp(CCval,*z):
    if (CCval > 0):
        gv.damp = True
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
    else: gv.damp = False
def DampNew(CCval,*z):
    if (CCval>0):   gv.damp = True
    else:           gv.damp = False
def DampLast(CCval,*z):
    if (CCval>0):
        gv.damp = True
        gv.sustain = True
    else:
        gv.damp = False
        gv.sustain = False
        for m in gv.sustainplayingnotes:    # get rid of gathered notes
            m.fadeout(False)
        gv.sustainplayingnotes = []
def PitchSens(CCval,*z):
    gv.pitchnotes = (24*CCval+100)/127
                            # and announce the procs to modules
gv.MC[getindex(gv.PANIC,gv.MC)][2]=AllNotesOff
gv.MC[getindex(gv.VOLUME,gv.MC)][2]=MidiVolume
gv.MC[getindex(gv.AUTOCHORDOFF,gv.MC)][2]=AutoChordOff
gv.MC[getindex(gv.PITCHWHEEL,gv.MC)][2]=PitchWheel
gv.MC[getindex(gv.MODWHEEL,gv.MC)][2]=ModWheel
gv.MC[getindex(gv.SUSTAIN,gv.MC)][2]=Sustain
gv.MC[getindex(gv.DAMP,gv.MC)][2]=Damp
gv.MC[getindex(gv.DAMPNEW,gv.MC)][2]=DampNew
gv.MC[getindex(gv.DAMPLAST,gv.MC)][2]=DampLast
gv.MC[getindex(gv.PITCHSENS,gv.MC)][2]=PitchSens

def MidiCallback(src, message, time_stamp):
    global RELSAMPLE, velocity_mode, notemap, playingbacktracks
    messagetype = message[0] >> 4
    messagechannel = (message[0]&0xF) + 1
    #print '%s -> Channel %d, message %d' % (src, messagechannel , messagetype)
    # -------------------------------------------------------
    # Process system commands
    # -------------------------------------------------------
    if messagetype==15:         # System messages apply to all channels, channel position contains commands
        if messagechannel==15:  # "realtime" reset has to reset all activity & settings
            AllNotesOff()       # (..other realtime expects everything to stay intact..)
    # -------------------------------------------------------
    # Then process channel commands if not muted
    # -------------------------------------------------------
    elif (messagechannel == gv.MIDI_CHANNEL) and (gv.midi_mute == False):
        midinote = message[1] if len(message) > 1 else None
        velocity = message[2] if len(message) > 2 else None

        if messagetype==8 or messagetype==9:        # We may have a note on/off
            retune=0
            for i in xrange(len(notemap)):          # do we have note mapping ?
                if midinote==notemap[i][2]:
                    midinote=notemap[i][3]
                    retune=notemap[i][4]
                    if notemap[i][5]>0:
                        setVoice(notemap[i][5])
                    break       # found it, stop wasting time
            if velocity==0: messagetype=8           # prevent complexity in the rest of the checking
            #if gv.triggernotes[midinote]==midinote and velocity==64: # Older MIDI implementations
            #    messagetype=8                                        # (like Roland PT-3100)
            if messagetype==8:                      # should this note-off be ignored?
                if midinote in gv.playingnotes and gv.triggernotes[midinote]<128:
                       for m in gv.playingnotes[midinote]:
                           if m.playingstopnote() < 128:    # are we in a special mode
                               messagetype = 128            # if so, then ignore this note-off
                else:
                    messagetype = 128               # nothing's playing, so there is nothing to stop
            if messagetype == 9:    # is a note-off hidden in this note-on ?
                if midinote in gv.playingnotes:     # this can only be if the note is already playing
                    for m in gv.playingnotes[midinote]:
                        xnote=m.playingstopnote()   # yes, so check it's stopnote
                        if xnote>-1 and xnote<128:  # not in once or keyboard mode
                            if midinote==xnote:     # could it be a push-twice stop?
                                #if gv.sample_mode==PLAYMONO and midinote!=m.playingnote():
                                #    pass    # ignore the chord generated notes when playing monophonic
                                if m.playingstopmode()==3:
                                    messagetype=128                     # backtracks end on sample end
                                    m.playing2end()                     # so just let it finish
				    playingbacktracks-=1
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
                    for playnote in xrange(128-gv.stop127, gv.stop127):   # so leave the effects range out of this
                        if playnote in gv.playingnotes:
                            for m in gv.playingnotes[playnote]: 
                                if gv.sustain:
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
                    if midinote>(127-gv.stop127) and midinote <gv.stop127:
                        gv.last_musicnote=midinote-12*int(midinote/12) # do a "remainder midinote/12" without having to import the full math module
                        if gv.currscale>0:               # scales require a chords mix
                            gv.currchord = gv.scalechord[gv.currscale][gv.last_musicnote]
                        playchord=gv.currchord
                    else:
                        gv.last_musicnote=12 # Set musicnotesymbol to "effects" in webgui
                        playchord=0       # no chords outside keyboardrange / in effects channel.
                    for n in range (len(gv.chordnote[playchord])):
                        playnote=midinote+gv.chordnote[playchord][n]
                        for m in gv.sustainplayingnotes:    # safeguard polyphony:
                            if m.note == playnote:          # ..don't sustain double notes
                                m.fadeout(False)            # ..but damp them
                        if gv.triggernotes[playnote] < 128: # cleanup in case of retrigger
                            if playnote in gv.playingnotes: # occurs in once/loops modes and chords
                                for m in gv.playingnotes[playnote]:
                                    if m.sound.retrigger!='Y':  # playing double notes not allowed
                                        if m.sound.retrigger=='R':
                                            m.fadeout(True)     # ..either release
                                        else:
                                            m.fadeout(False)    # ..or damp
                                    #gv.playingnotes[playnote]=[]   # housekeeping
                        #FMO stops: hier moet de set van voices aangezet
                        #print "start playingnotes playnote %d, velocity %d, gv.currvoice %d, velmixer %d" %(playnote, velocity, gv.currvoice, velmixer)
                        gv.playingnotes.setdefault(playnote,[]).append(gv.samples[playnote, velocity, gv.currvoice].play(midinote, playnote, velmixer*gv.globalgain, 0, retune))
                        for m in gv.playingnotes[playnote]:
                            if m.playingstopmode()== 3: playingbacktracks+=1
                            if midinote>(127-gv.stop127) and midinote <gv.stop127:
                                if gv.damp:
                                    if m.playingstopmode()!= 3:    # don't damp backtracks
                                        if gv.sustain:  # damplast (=play untill pedal released
                                            gv.sustainplayingnotes.append(m)
                                        else:           # damp+dampnew (=damp played notes immediately)
                                            m.fadeout(False)
                                        gv.playingnotes[playnote]=[]
                                #elif m.playingstopmode()!=-1 and m.playingstopmode()!=3:
                                elif m.playingstopmode()!=3:
                                    gv.triggernotes[playnote]=midinote   # we are last playing this one
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
                                elif gv.sustain:    # sustain only works for mode=keyb notes in the keyboard area
                                    if stopmode==128 and midinote>(127-gv.stop127) and midinote <gv.stop127:
                                        gv.sustainplayingnotes.append(m)
                                else:
                                    m.fadeout()
                                gv.playingnotes[playnote] = []
                                gv.triggernotes[playnote] = 128  # housekeeping
                                #FMO stops: hier moet de set van voices aangezet
                                if  RELSAMPLE == 'E':
                                    gv.playingnotes.setdefault(playnote,[]).append(gv.samples[playnote, velocity, gv.currvoice].play(midinote, playnote, velmixer*gv.globalgain, -1, retune))

        elif messagetype == 12: # Program change
            gv.PRESET = midinote+gv.PRESETBASE
            LoadSamples()

        elif messagetype == 14: # Pitch Bend (velocity contains MSB, note contains 0 or LSB if supported by controller)
            PitchWheel(midinote,velocity)

        elif messagetype == 11: # control change (CC = Continuous Controllers)
            CCnum = midinote
            CCval = velocity
            #print "CCnum = %d, CCval = %d" % (CCnum, CCval)
            mc=False
            for m in gv.CCmap:    # look for mapped controllers
                j=m[0]
                if gv.controllerCCs[j][1]==CCnum and (gv.controllerCCs[j][2]==-1 or gv.controllerCCs[j][2]==CCval or gv.MC[m[1]][1]==3):
                    #print "Recognized %s" %gv.MC[m[1]][0]
                    if m[2]!=None: CCval=m[2]
                    gv.MC[m[1]][2](CCval,gv.MC[m[1]][0])
                    mc=True
            if not mc and (CCnum==120 or CCnum==123):   # "All sounds off" or "all notes off"
                AllNotesOff()

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
    gv.notemap=[]
    gv.currnotemap=""
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
    PREQCENT=50                     # The cents of qsharp (sori), the qflat (koron) is qcent-100
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
    voiceqcent = [50]*128
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
    getcsv.readnotemap(os.path.join(dirname, NOTEMAP_DEF))
    gv.CCmapSet=getcsv.readCCmap(os.path.join(dirname, CTRLMAP_DEF), True)
    definitionfname = os.path.join(dirname, gv.SAMPLESDEF)
    if os.path.isfile(definitionfname):
        if USE_HTTP_GUI:
            with open(definitionfname, 'r') as definitionfile:  # keep full text for the gui
                gv.DefinitionTxt=definitionfile.read()
        with open(definitionfname, 'r') as definitionfile:
            for i, pattern in enumerate(definitionfile):
                try:
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
                    if r'%%qcent' in pattern:
                        v = int(pattern.split('=')[1].strip())
                        if v<0: v=v+100
                        if v>99 or v==0:
                            print "Qcent= %d ignored, should between 0 and +/- 100" % v
                        else:
                            PREQCENT = v
                            if PREQNOTE == 'N':
                                PREQNOTE = 'Y'
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
                                      'xfadeout':PREXFADEOUT, 'xfadein':PREXFADEIN, 'xfadevol':PREXFADEVOL, 'qnote':PREQNOTE, 'qcent':PREQCENT, 'notemap':PRENOTEMAP, 'fillnote':fillnote, 'backtrack':'-1'}
                    if len(pattern.split(',')) > 1:
                        defaultparams.update(dict([item.split('=') for item in pattern.split(',', 1)[1].replace(' ','').replace('%', '').split(',')]))
                    pattern = pattern.split(',')[0]
                    pattern = re.escape(pattern.strip())
                    pattern = pattern.replace(r"\%midinote", r"(?P<midinote>\d+)").replace(r"\%velocity", r"(?P<velocity>\d+)").replace(r"\%gain", r"(?P<gain>[-+]?\d*\.?\d+)").replace(r"\%voice", r"(?P<voice>\d+)")\
                                     .replace(r"\%fillnote", r"(?P<fillnote>[YNyn])").replace(r"\%mode", r"(?P<mode>[A-Za-z0-9])").replace(r"\%transpose", r"(?P<transpose>\d+)").replace(r"\%release", r"(?P<release>\d+)")\
                                     .replace(r"\%damp", r"(?P<damp>\d+)").replace(r"\%retrigger", r"(?P<retrigger>[YyRrDd])").replace(r"\%xfadeout", r"(?P<xfadeout>\d+)").replace(r"\%xfadein", r"(?P<xfadein>\d+)")\
                                     .replace(r"\%qnote", r"(?P<qnote>[YyNnOoEe])").replace(r"\%qcent", r"(?P<qcent>\d+)").replace(r"\%notemap", r"(?P<notemap>[A-Za-z0-9]\_\-\&)")\
                                     .replace(r"\%backtrack", r"(?P<backtrack>\d+)").replace(r"\%notename", r"(?P<notename>[A-Ga-g][#ks]?[0-9])").replace(r"\*", r".*?").strip()    # .*? => non greedy
                    for fname in os.listdir(dirname):
                        if LoadingInterrupt:
                            #print 'Loading % s interrupted...' % dirname
                            gv.ActuallyLoading=False
                            return
                        m = re.match(pattern, fname)
                        if m:
                            #print 'Processing ' + fname
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
                            qcent = int(info.get('qcent', defaultparams['qcent']))
                            if qcent < 0: qcent = qcent+100
                            if qcent > 99 or qcent == 0:
                                print "%qcent=%d ignored, should between 0 and +/- 100" % qcent
                                qcent = PREQCENT
                            else:
                                if qnote == 'N' and qcent != PREQCENT:
                                    qnote = 'Y'
                            if qnote == 'Y': qnote = 'O'    # the default for qnotes is on odd midi notes (60=C).
                            fractions = PREFRACTIONS        # not yet implemented for user change (future??)
                            if qnote != 'N':
                                voiceqnote[voice] = qnote   # pick the latest; we can't check everything, RTFM :-)
                                voiceqcent[voice] = qcent   # pick the latest; we can't check everything, RTFM :-)
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
                setVoice(voice, None)
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
                    retune = 0
                    if voiceqnote[voice] != 'N':
                        if (midinote%2 ==0 and voiceqnote[voice]=='E') or (midinote%2 !=0 and voiceqnote[voice]=='O'):
                            retune = voiceqcent[voice]-50      # value for filling above sample (=sharp)
                            if midinote < m:        # but we're filling below sample (=flat)
                                retune = -retune
                    for velocity in xrange(128):
                        gv.samples[midinote, velocity, voice] = gv.samples[m, velocity, voice]
                        gv.samples[midinote, velocity, voice].retune = retune*PITCHSTEPS/100

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

if gv.USE_ALSA_MIXER:
    import DACvolume

if USE_BUTTONS:
    USE_GPIO=True
    import buttons

if USE_HTTP_GUI:
    import http_gui

if USE_SERIALPORT_MIDI:
    import serialMIDI

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
    if USE_GPIO:
        import RPi.GPIO as GPIO
        GPIO.cleanup()
