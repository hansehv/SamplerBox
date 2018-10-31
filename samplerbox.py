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
if os.path.isdir('/home/hans'):
    test=True
    testprefix='/home/hans/Documents/SamplerBox'
else:
    test=False
    testprefix=""
sys.path.append(testprefix+'/root/SamplerBox/modules')
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
def setVoice(x,*z):
    voice=int(x)
    y=getindex(voice,gv.voicelist)
    if y>-1:                # ignore if undefined
        gv.currvoice=voice
        gv.sample_mode=gv.voicelist[y][2]
        display("")
def playBackTrack(x,*z):
    playnote=int(x)+130
    if playnote in gv.playingnotes:    # is the track playing?
        for m in gv.playingnotes[playnote]:
            m.playing2end()         # let it finish
    else:
        try:
            gv.playingnotes.setdefault(playnote,[]).append(gv.samples[playnote, 127, 0].play(playnote, playnote, 127, 0))
        except:
            print 'Unassigned/unfilled track or other exception for backtrack %s->%d' % (x,playnote)

gv.getindex=getindex                            # and announce the procs to modules
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
SAMPLES_INBOX = testprefix+"/samples/"  # Builtin directory containing the sample-sets.
SAMPLES_ONUSB = testprefix+"/media/"    # USB-Mount directory containing the sample-sets.
CONFIG_LOC = testprefix+"/boot/samplerbox/"
CHORDS_DEF = "chords.csv"
SCALES_DEF = "scales.csv"
MIDICCS_DEF = "midi_controllers.csv"
MIDIMAP_DEF = "midi_mapping.csv"
HTTP_PORT = 80

##########  read LOCAL CONFIG ==> /boot/samplerbox/configuration.txt
gv.cp=ConfigParser.ConfigParser()
gv.cp.read(CONFIG_LOC + "configuration.txt")
s="config"
AUDIO_DEVICE_ID = gv.cp.getint(s,"AUDIO_DEVICE_ID".lower())
USE_SERIALPORT_MIDI = gv.cp.getboolean(s,"USE_SERIALPORT_MIDI".lower())
USE_HD44780_16x2_LCD = gv.cp.getboolean(s,"USE_HD44780_16x2_LCD".lower())
USE_I2C_7SEGMENTDISPLAY = gv.cp.getboolean(s,"USE_I2C_7SEGMENTDISPLAY".lower())
gv.USE_ALSA_MIXER = gv.cp.getboolean(s,"USE_ALSA_MIXER".lower())
if gv.USE_ALSA_MIXER:
    MIXER_CONTROL=gv.cp.get(s,"MIXER_CONTROL".lower()).replace(" ", "").split(',')
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
notenames=["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]  # 0 in scalechord table, also used in loadsamples(!)
getcsv.readchords(CONFIG_LOC + CHORDS_DEF)
getcsv.readscales(CONFIG_LOC + SCALES_DEF)

# Midi mapping
getcsv.readmidiCCs(CONFIG_LOC + MIDICCS_DEF)
getcsv.readmidimap(CONFIG_LOC + MIDIMAP_DEF)

########## Initialize other globals, don't change

USE_GPIO=False
PITCHCORR = 0       # This is the 44100 to 48000 correction / hack
PITCHRANGE *= 2     # actually it is 12 up and 12 down

gv.samplesdir = SAMPLES_INBOX
gv.stop127 = BOXSTOP127
gv.sample_mode = BOXSAMPLE_MODE
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
    MIXER_CARD_ID = AUDIO_DEVICE_ID-1  # This may vary with your HW. The jack/HDMI of PI use 1 alsa card index
else:
    MIXER_CARD_ID = 0

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
    LEDs.red()

else:
    def display(s2,s7=""):
        pass    
gv.display=display

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
gv.MC[getindex(gv.REVERBLVL,gv.MC)][2]=FVsetlevel   # and to midimap
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
def Reverb(CCval,*z):  setEffect(gv.REVERB)
def Tremolo(CCval,*z): setEffect(gv.TREMOLO)
def Vibrato(CCval,*z): setEffect(gv.VIBRATO)
def Rotate(CCval,*z):  setEffect(gv.ROTATE)
def EffectsOff(*z):
    gv.currfilter=0
    setFilter(gv.currfilter)
    #FVinit()                   # no cleanup necessary
    LFO.RotateTidy(False)       # cleans up vibrato+tremolo+rotate
gv.setFilter=setFilter
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
        stopmode = -1                           # don't stop, play sample at full lenght (unless restarted)
    elif mode==PLAYLOOP:
        stopmode = 127                          # stop on 127-key
    elif mode==PLAYBACK2X or mode==PLAYLOOP2X or mode==PLAYMONO:
        stopmode = 2                            # stop on 2nd keypress
    elif mode==BACKTRACK:
        stopmode = 3                            # stop looping on 2nd keypress or defined midi controller
    return stopmode
def GetLoopmode(mode):
    if mode==PLAYBACK or mode==PLAYBACK2X:
        loopmode = -1
    else:
        loopmode = 1
    return loopmode
        
class PlayingSound:
    def __init__(self, sound, voice, note, vel, pos, end, loop, stopnote, stopmode):
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
        self.vel = vel
        self.stopnote = stopnote
        self.stopmode = stopmode

    def __str__(self):
        return "<PlayingSound note: '%i', velocity: '%i', pos: '%i'>" %(self.note, self.vel, self.pos)
    def playingnote(self):
        return self.note
    def playingvelocity(self):
        return self.vel
    def playingstopnote(self):
        return self.stopnote
    def playingstopmode(self):
        return self.stopmode

    def playing2end(self):
        self.loop=-1
    def fadeout(self):
        self.isfadeout = True
    def stop(self):
        try: gv.playingsounds.remove(self) 
        except: pass

class Sound:
    def __init__(self, filename, voice, midinote, velocity, mode, release, gain, xfadeout, xfadein, xfadevol):
        global RELSAMPLE
        wf = waveread(filename)
        self.fname = filename
        self.voice = voice
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

    def play(self, midinote, note, vel, startparm):
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
        snd = PlayingSound(self, self.voice, note, vel, pos, end, loop, stopnote, self.stopmode)
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
    rmlist = []
    gv.playingsounds = gv.playingsounds[-MAX_POLYPHONY:]
    # audio-module:
    b = samplerbox_audio.mixaudiobuffers(gv.playingsounds, rmlist, frame_count, FADEOUT, FADEOUTLENGTH, SPEED, SPEEDRANGE, gv.PITCHBEND+gv.VIBRvalue+PITCHCORR, PITCHSTEPS)
    for e in rmlist:
        try:
            if e.stopmode==3: del gv.playingnotes[e.note]   # keep track of backtrack status
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

if gv.USE_ALSA_MIXER:
    import alsaaudio
    ok=False
    for i in range(0, 4):
        for j in range(0, len(MIXER_CONTROL)):
            try:
                amix = alsaaudio.Mixer(cardindex=MIXER_CARD_ID+i,control=MIXER_CONTROL[j])
                MIXER_CARD_ID+=i    # save the found value
                ok=True             # indicate OK
                print 'Opened Alsamixer: card (hw:%i,x), control %s' % (MIXER_CARD_ID, MIXER_CONTROL[j])
                break
            except:
                pass
        if ok: break
    if ok:
        def getvolume():
            vol = amix.getvolume()
            gv.volume = int(vol[0])
        def setvolume(volume):
            amix.setvolume(volume)
            getvolume()
        setvolume(gv.volume)
    else:
        gv.USE_ALSA_MIXER=False
        display("Invalid mixerdev")
        print 'Invalid mixer card id "%i" or control "%s" --' % (MIXER_CARD_ID, MIXER_CONTROL)
        print '-- Mixer card id is "x" in "(hw:x,y)" (if present) in opened audio device.'
if not gv.USE_ALSA_MIXER:
    def getvolume():
        pass
    def setvolume(volume):
        pass
gv.setvolume=setvolume

#########################################
##  MIDI
##   - general routines
##   - CALLBACK
#########################################

def AllNotesOff(x=0,*z):
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
        if (CCval < 64):    # sustain off
            for n in gv.sustainplayingnotes:
                n.fadeout()
            gv.sustainplayingnotes = []       
            gv.sustain = False
            #print 'Sustain pedal released'
        else:               # sustain on
            gv.sustain = True
            #print 'Sustain pedal pressed'
def PitchSens(CCval,*z):
    gv.pitchnotes = (24*CCval+100)/127
gv.MC[getindex(gv.PANIC,gv.MC)][2]=AllNotesOff
gv.MC[getindex(gv.VOLUME,gv.MC)][2]=MidiVolume
gv.MC[getindex(gv.AUTOCHORDOFF,gv.MC)][2]=AutoChordOff
gv.MC[getindex(gv.PITCHWHEEL,gv.MC)][2]=PitchWheel
gv.MC[getindex(gv.MODWHEEL,gv.MC)][2]=ModWheel
gv.MC[getindex(gv.SUSTAIN,gv.MC)][2]=Sustain
gv.MC[getindex(gv.PITCHSENS,gv.MC)][2]=PitchSens

def MidiCallback(src, message, time_stamp):
    global RELSAMPLE
    global velocity_mode
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
            if velocity==0: messagetype=8           # prevent complexity in the rest of the checking
            #if gv.triggernotes[midinote]==midinote and velocity==64:   # Older MIDI implementations
            #    messagetype=8                                       # like Roland PT-3100
            if messagetype==8:                      # first process standard midi note-off, but take care
                if midinote in gv.playingnotes and gv.triggernotes[midinote]<128: # .. to not accidently turn off release samples in non-keyboard mode
                       for m in gv.playingnotes[midinote]:
                           if m.playingstopnote() < 128:    # are we in a special mode
                               messagetype = 128            # if so, then ignore this note-off
                           #else:                            # since we have the info at hand now:
                           #    velmixer = m.playingvelocity()  # save org value for release sample
                else: messagetype = 128             # nothing's playing, so there is nothing to stop
            if messagetype == 9:    # is a note-off hidden in this note-on ?
                if midinote in gv.playingnotes:    # this can only be if the note is already playing
                    for m in gv.playingnotes[midinote]:
                        xnote=m.playingstopnote()   # yes, so check it's stopnote
                        if xnote>-1 and xnote<128:  # not in once or keyboard mode
                            if midinote==xnote:     # could it be a push-twice stop?
                                #if gv.sample_mode==PLAYMONO and midinote!=m.playingnote():
                                #    pass    # ignore the chord generated notes when playing monophonic
                                if m.playingstopmode()==3:
                                    messagetype=128                     # backtracks end on sample end
                                    m.playing2end()                     # so just let it finish
                                    gv.triggernotes[midinote] = 128     # housekeeping
                                else:
                                    messagetype = 8                     # all the others have an instant end
                            elif midinote >= gv.stop127:   # could it be mirrored stop?
                                if (midinote-127) in gv.playingnotes:  # is the possible mirror note-on active?
                                    for m in gv.playingnotes[midinote-127]:
                                        if midinote==m.playingstopnote():   # and has it mirrored stop?
                                            messagetype = 8
                                            #velmixer = m.playingvelocity()  # save org value for release sample

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
                        velmixer = 127 * gv.globalgain
                    else:
                        velmixer = velocity * gv.globalgain
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
                        for m in gv.sustainplayingnotes:   # safeguard polyphony; don't sustain double notes
                            if m.note == playnote:
                                m.fadeout()
                                #print 'clean sustain ' + str(playnote)
                        if gv.triggernotes[playnote] < 128:  # cleanup in case of retrigger
                            if playnote in gv.playingnotes:    # occurs in once/loops modes and chords
                                for m in gv.playingnotes[playnote]: 
                                    #print "clean note " + str(playnote)
                                    m.fadeout()
                                gv.playingnotes[playnote] = []   # housekeeping
                        gv.triggernotes[playnote]=midinote   # we are last playing this one
                        #FMO stops: hier moet de set van voices aangezet
                        #print "start playingnotes playnote %d, velocity %d, gv.currvoice %d, velmixer %d" %(playnote, velocity, gv.currvoice, velmixer)
                        gv.playingnotes.setdefault(playnote,[]).append(gv.samples[playnote, velocity, gv.currvoice].play(midinote, playnote, velmixer, 0))
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
                                elif gv.sustain:    # test keyboardarea to prevent useless checking in most cases
                                    if midinote>(127-gv.stop127) and midinote <gv.stop127:
                                        #print 'Sustain note ' + str(playnote)   # debug
                                        gv.sustainplayingnotes.append(m)
                                else:
                                    #print "Stop note " + str(playnote)
                                    m.fadeout()
                                gv.playingnotes[playnote] = []
                                gv.triggernotes[playnote] = 128  # housekeeping
                                #FMO stops: hier moet de set van voices aangezet
                                if  RELSAMPLE == 'E':
                                    gv.playingnotes.setdefault(playnote,[]).append(gv.samples[playnote, velocity, gv.currvoice].play(midinote, playnote, velmixer*gv.globalgain, -1))

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
            for m in gv.midimap:    # look for mapped controllers
                j=m[0]
                if gv.midiCCs[j][1]==CCnum and (gv.midiCCs[j][2]==-1 or gv.midiCCs[j][2]==CCval):
                    #print "Recognized %s" %gv.MC[m[1]][0]
                    if m[2]!=None: CCval=m[2]
                    gv.MC[m[1]][2](CCval,gv.MC[m[1]][0])
                    mc=True
            if not mc and (CCnum==120 or CCnum==123):   # "All sounds off" or "all notes off"
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
gv.LoadSamples=LoadSamples

def ActuallyLoad():    
    global velocity_mode, RELSAMPLE
    gv.ActuallyLoading=True
    #print 'Entered ActuallyLoad'
    AllNotesOff()
    gv.currbase = gv.basename    

    gv.samplesdir = SAMPLES_ONUSB if os.listdir(SAMPLES_ONUSB) else SAMPLES_INBOX      # use builtin folder (containing 0 Saw) if no user media containing samples has been found
    #gv.basename = next((f for f in os.listdir(gv.samplesdir) if f.startswith("%d " % gv.PRESET)), None)      # or next(glob.iglob("blah*"), None)
    presetlist=[]
    for f in os.listdir(gv.samplesdir):
        #print f
        if re.match(r'[0-9]* .*', f):
            if os.path.isdir(os.path.join(gv.samplesdir,f)):
                p=int(re.search('\d* ', f).group(0).strip())
                presetlist.append([p,f])
                if p==gv.PRESET: gv.basename=f
    presetlist=sorted(presetlist,key=lambda presetlist: presetlist[0])  # sort without having to import operator modules
    gv.presetlist=presetlist

    print "We have %s, we want %s" %(gv.currbase, gv.basename)
    if gv.basename:
        if gv.basename == gv.currbase:      # don't waste time reloading a patch
            #print 'Kept PRESET %s' % gv.basename
            gv.ActuallyLoading=False
            display("")
            return
        dirname = os.path.join(gv.samplesdir, gv.basename)

    mode=[]
    gv.globalgain = 1
    gv.currvoice = 0
    gv.sample_mode=BOXSAMPLE_MODE   # fallback to the samplerbox default
    velocity_mode=BOXVELOCITY_MODE  # fallback to the samplerbox default
    gv.stop127=BOXSTOP127           # fallback to the samplerbox default
    gv.pitchnotes=PITCHRANGE        # fallback to the samplerbox default
    PRERELEASE=BOXRELEASE           # fallback to the samplerbox default
    PREXFADEOUT=BOXXFADEOUT         # fallback to the samplerbox default
    PREXFADEIN=BOXXFADEIN           # fallback to the samplerbox default
    PREXFADEVOL=BOXXFADEVOL         # fallback to the samplerbox default
    RELSAMPLE='N'
    PRETRANSPOSE=0
    gv.samples = {}
    fillnotes = {}
    fillnote = 'Y'          # by default we will fill/generate missing notes
    gv.btracklist=[]
    tracknames  = []
    for backtrack in range(128):
        tracknames.append(["", False, ""])
    gv.voicelist =[]
    voicenames  = []
    for voice in range(128):
        voicenames.append([voice, str(voice)])
    voicemodes = [""]*128
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
                        gv.pitchnotes = abs(int(pattern.split('=')[1].strip()))
                        if gv.pitchnotes > 12:
                            print "Pitchbend of %d limited to 12" % gv.pitchnotes
                            gv.pitchnotes = 12
                        gv.pitchnotes *= 2     # actually it is 12 up and 12 down
                        continue
                    if r'%%mode' in pattern:
                        m = pattern.split('=')[1].strip().title()
                        if m==PLAYLIVE or m==PLAYBACK or m==PLAYBACK2X or m==PLAYLOOP or m==PLAYLOOP2X or m==PLAYMONO or m==BACKTRACK: gv.sample_mode = m
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
                            raise exception ("Backtrack %d=%m ignored" %(v,m))
                        tracknames[int(v)][0]=m
                        continue
                    if r'%%voice' in pattern:
                        m = pattern.split(':')[1].strip()
                        v,m=m.split("=")
                        if int(v)>127:
                            print "Voicename %m ignored" %m
                            raise exception ("Voicename %d=%m ignored" %(v,m))
                        voicenames[int(v)]=[int(v),v+" "+m]
                        continue
                    defaultparams = { 'midinote': '-1', 'velocity': '127', 'gain': '1', 'notename': '', 'voice': '1', 'mode': gv.sample_mode, 'transpose': PRETRANSPOSE, 'release': PRERELEASE, 'xfadeout': PREXFADEOUT, 'xfadein': PREXFADEIN, 'xfadevol': PREXFADEVOL, 'fillnote': fillnote, 'backtrack': '-1' }
                    if len(pattern.split(',')) > 1:
                        defaultparams.update(dict([item.split('=') for item in pattern.split(',', 1)[1].replace(' ','').replace('%', '').split(',')]))
                    pattern = pattern.split(',')[0]
                    pattern = re.escape(pattern.strip())
                    pattern = pattern.replace(r"\%midinote", r"(?P<midinote>\d+)").replace(r"\%velocity", r"(?P<velocity>\d+)").replace(r"\%gain", r"(?P<gain>[-+]?\d*\.?\d+)").replace(r"\%voice", r"(?P<voice>\d+)")\
                                     .replace(r"\%fillnote", r"(?P<fillnote>[YNyn]").replace(r"\%mode", r"(?P<mode>[A-Za-z0-9])").replace(r"\%transpose", r"(?P<transpose>\d+)")\
                                     .replace(r"\%release", r"(?P<release>\d+)").replace(r"\%xfadeout", r"(?P<xfadeout>\d+)").replace(r"\%xfadein", r"(?P<xfadein>\d+)")\
                                     .replace(r"\%backtrack", r"(?P<backtrack>\d+)").replace(r"\%notename", r"(?P<notename>[A-Ga-g]#?[0-9])").replace(r"\*", r".*?").strip()    # .*? => non greedy
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
                            # next statement places note 60 on C3/C4/C5 with the +0/1/2 at the end. So now it is C4:
                            if notename: midinote = notenames.index(notename[:-1].upper()) + (int(notename[-1])+1) * 12
                            if midinote < -1 or midinote > 127:
                                print "%s: ignored notename / midinote: '%s'/%d" %(fname, notename, midinote)
                                midinote=-1
                            transpose = int(info.get('transpose', defaultparams['transpose']))
                            mode = info.get('mode', defaultparams['mode'])
                            mode=mode.strip().title()
                            backtrack = int(info.get('backtrack', defaultparams['backtrack']))
                            if backtrack>-1:
                                if backtrack<128 and not tracknames[backtrack][1]:
                                    mode=BACKTRACK
                                    voice=0
                                    tracknames[backtrack][1]=True
                                    if tracknames[backtrack][0]=="":
                                        tracknames[backtrack][0]=fname[:-4]
                                    if midinote>-1:
                                        if notename:tracknames[backtrack][2]=notename
                                        else:       tracknames[backtrack][2]="%d" %midinote
                                else:
                                    print "Backtrack %s ignored" %fname
                                    raise exception ("Backtrack %s ignored" %fname[:-4])
                            else:
                                voice=int(info.get('voice', defaultparams['voice']))
                            if voice == 0:          # the override / special effects voice cannot fill or transpose
                                voicefillnote = 'N' # so we ignore whatever the user wants (RTFM)
                            elif voice<128:
                                voicefillnote = (info.get('fillnote', defaultparams['fillnote'])).title().rstrip()
                                midinote-=transpose
                            else:
                                print "Voice %d ignored" %voice
                                raise exception ("Voice %d ignored" %voice)
                            velocity = int(info.get('velocity', defaultparams['velocity']))
                            gain = abs(float((info.get('gain', defaultparams['gain']))))
                            release = int(info.get('release', defaultparams['release']))
                            if (release>127): release=127
                            xfadeout = int(info.get('xfadeout', defaultparams['xfadeout']))
                            if (xfadeout>127): xfadeout=127
                            xfadein = int(info.get('xfadein', defaultparams['xfadein']))
                            if (xfadein>127): xfadein=127
                            xfadevol = abs(float(info.get('xfadevol', defaultparams['xfadevol'])))
                            if (GetStopmode(mode)<-1) or (GetStopmode(mode)==127 and midinote>(127-gv.stop127)):
                                print "invalid mode '%s' or note %d out of range, set to keyboard mode." % (mode, midinote)
                                mode=PLAYLIVE   # invalid mode or note out of range
                            try:
                                if backtrack>-1:    # Backtracks are intended for start/stop via controller, so we can use unplayable notes
                                    gv.samples[130+backtrack, velocity, voice] = Sound(os.path.join(dirname, fname), voice, 130+backtrack, velocity, mode, release, gain, xfadeout, xfadein, xfadevol)
                                    #print "Added %s as backtrack" %fname
                                if midinote>-1:
                                    gv.samples[midinote, velocity, voice] = Sound(os.path.join(dirname, fname), voice, midinote, velocity, mode, release, gain, xfadeout, xfadein, xfadevol)
                                    fillnotes[midinote, voice] = voicefillnote
                                    if voicemodes[voice]=="" or mode==PLAYMONO: voicemodes[voice]=mode
                                    elif voicemodes[voice]!=PLAYMONO and voicemodes[voice]!=mode: voicemodes[voice]="Mixed"
                                    #print "Added %s as playable" %fname
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
                gv.samples[midinote, 127, 1] = Sound(file, midinote, 127, gv.sample_mode, PRERELEASE, gv.globalgain, PREXFADEOUT, PREXFADEIN, PREXFADEVOL)
                fillnotes[midinote, 1] = fillnote
        voicenames[1]=[1,"Default"]
        voicemodes[1]=gv.sample_mode

    initial_keys = set(gv.samples.keys())
    if len(initial_keys) > 0:
        for voice in xrange(128):
            if voicemodes[voice]=="": continue
            if gv.currvoice==0: gv.currvoice=voice     # make sure to start with a playable non-empty voice
            #print "Complete info for voice %d" % (voice)
            v=getindex(voice, voicenames)
            gv.voicelist.append([voice, voicenames[v][1], voicemodes[voice]])
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
            if tracknames[track][1]:
                gv.btracklist.append([track, tracknames[track][0], tracknames[track][2]])
        if gv.currvoice!=0: gv.sample_mode=gv.voicelist[getindex(gv.currvoice,gv.voicelist)][2]
        gv.ActuallyLoading=False
        display("","%04d" % gv.PRESET)

    else:
        #print 'Preset empty: ' + str(gv.PRESET)
        gv.basename = "%d Empty preset" %gv.PRESET
        gv.ActuallyLoading=False
        display("","E%03d" % gv.PRESET)


#########################################
##  BUTTONS via RASPBERRY PI GPIO
#########################################

if USE_BUTTONS:
    USE_GPIO=True
    import buttons
    ButtonsThread = threading.Thread(target = buttons.Buttons)
    ButtonsThread.daemon = True
    ButtonsThread.start()

#########################################
##  WebGUI thread
#########################################

if USE_HTTP_GUI:
    from BaseHTTPServer import HTTPServer
    from http_gui import HTTPRequestHandler

    def HTTP_Server(server_class=HTTPServer, handler_class=HTTPRequestHandler, port=HTTP_PORT):
        server_address = ('', port)
        httpd = server_class(server_address, handler_class)
        print 'Starting httpd on port %d' % (port)
        try:
            httpd.serve_forever()
        except:
            print 'Starting httpd failed'

    HTTPThread = threading.Thread(target = HTTP_Server)
    HTTPThread.daemon = True
    HTTPThread.start()

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
#########################################     

LoadSamples()

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
    print "\nstopped by ctrl-c\n"
except:
    print "\nstopped by Other Error"
finally:
    display('Stopped')
    time.sleep(0.5)
    if USE_GPIO:
        import RPi.GPIO as GPIO
        GPIO.cleanup()
