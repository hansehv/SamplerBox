#  samplerbox.py: Main file
#
#  SamplerBox extended by HansEhv (https://github.com/hansehv)
#  see docs at https://homspace.nl/samplerbox
#  changelog in changelist.txt
#
#  Original SamplerBox :
#  author:    Joseph Ernest (twitter: @JosephErnest, mail: contact@samplerbox.org)
#  url:       http://www.samplerbox.org/
#  license:   Creative Commons ShareAlike 3.0 (http://creativecommons.org/licenses/by-sa/3.0/)

##########################################################################
##  IMPORT MODULES (generic, more can be loaded depending on local config)
##  WARNING: GPIO modules in this build use mode=BCM. Do not mix modes!
##  Miscellaneous generic procs (too small to split off), published via gv
##########################################################################

import sys
sys.path.append('./modules')
import gv

########  Have some debugging help first  ########
print ( "=" *42 )
print ( "  https://github.com/hansehv/SamplerBox" )
try:
    with open('/boot/z_distbox.txt') as f:
        print ( f.read().strip() )
        gv.RUN_FROM_IMAGE = True
except:
    print ( "   Not running from distribution image" )
    gv.RUN_FROM_IMAGE = False
print ( "no track of local changes, that's for you!" )
print ( "=" *42 )

########  continue importing  ########
import wave,rtmidi2
from chunk import Chunk
import time,psutil,numpy,struct,copy
import sys,os,re,operator,threading
from numpy import random
import configparser
import samplerbox_audio   # audio-module (cython)
import gp, getcsv
#gv.rootprefix='/home/pi/samplerbox'
#if not os.path.isdir(gv.rootprefix):
#    gv.rootprefix=""

########  Define local general functions ########
usleep = lambda x: time.sleep(x/1000000.0)
msleep = lambda x: time.sleep(x/1000.0)

def setVoice(x,iv=0,*z):
    #iv=-1 means mapchange, -2 means multitimbral voice change
    if not isinstance(iv,int):
        iv=1
    if iv==0:       # we got the index of the voice table
        xvoice=int(x)
    else:           # we got the voicenumber
        xvoice=gp.getindex(int(x),gv.voicelist)
    if xvoice <0:   # no option :-(
        print("Undefined voice", x)
    else:
        #gv.voicelist = []:
        # 0=voice#, 1=descr, 2=mode, 3=notemap, 4=velocitylevels, 5=fxpreset, 6=layers
        voice = gv.voicelist[xvoice][0]
        if voice != gv.currvoice:         # also ignore if active
            gv.currvoice = voice
            gv.sample_mode = gv.voicelist[xvoice][2]
            if iv >- 2:   # not MT voice change so layering can be changed
                gv.currlayers = [ [gv.currvoice, 1] ]   # the voice = base = first layer
                gv.currlayername = ""
                if gv.voicelist[xvoice][6]:         # construct this voice's layer setup
                    x = gp.getindex( gv.voicelist[xvoice][6], gv.layernames, True, False )
                    if x > -1:
                        gv.currlayername = gv.voicelist[xvoice][6]
                        for layer in gv.layers[x]:
                            gv.currlayers.append( layer )
                if iv >- 1:   # not map change so mappings can be changed
                    gv.setNotemap( gv.voicelist[xvoice][3] )
                    FXset = gv.voicelist[xvoice][5]
                    FXset = gp.setFXpresets(FXset)      # when FXset doesn't exist, result will be "None"
                    gv.FXpreset_last = FXset            # force showing of the FX preset
                    gv.CCmap = list(gv.CCmapBox)        # construct this voice's CC setup
                    for i in range( len(gv.CCmapSet) ):
                        found = False
                        if gv.CCmapSet[i][3]==0 or gv.CCmapSet[i][3]==voice:    # voice applies
                            for j in range( len(gv.CCmap) ):                 # so check if button is known
                                if gv.CCmapSet[i][0] == gv.CCmap[j][0]:
                                    found = True
                                    if (gv.CCmapSet[i][3] >= gv.CCmap[j][3]): # voice specific takes precedence
                                        gv.CCmap[j] = gv.CCmapSet[i]          # replace entry
                                    continue
                            if not found:
                                gv.CCmap.append( gv.CCmapSet[i] )             # else add entry
                    if gv.AFTERTOUCH:
                        AfterTouch.msgFilter()  # filter unused aftertouch signals
                    gv.display("")
                    gv.menu_CCdef()
def setMTvoice(mididev,MIDIchannel,voice):
    voicemap = mididev.lower()
    if gv.USE_SMFPLAYER:    # smf files may have specific mapping
        if smfplayer.issending(mididev):
            voicemap = gv.smfseqs[gv.currsmf][4].lower()
    newvoice=voice  #define the var
    xvoice=-1       #define the var
    fallback=True
    for v in gv.voicemap:
        if v[0]=="0" or v[0].lower()==voicemap.lower():   # because of sort generic precedes the names/details
            if v[1]==0 or v[1]==MIDIchannel:
                if v[2]==0 or v[2]==voice:
                    newvoice=v[3]
                    if v[0]!="0" or v[1]!=0 or v[2]!=0:
                        fallback=False
    if fallback and gp.getindex(voice,gv.voicelist)>-1:
        newvoice=voice  # the requested voice is in the sample set, so we don't need the full fallback (it can be a "straight" GM map)
    else:
        print("Use voice %d for channel %d, programchange %d from %s" % \
            (newvoice, MIDIchannel, voice, mididev))
    voice=newvoice
    xvoice=gp.getindex(voice,gv.voicelist)
    if xvoice <0:   # still no succes, out of options :-(
        voice=0
    if voice==0:    # pick first available
        for m in gv.voicelist:
            if m[0]>0:
                print("Voice %d not in MT channelmap and samples, fall back to %d" %(voice,m[0]))
                voice=m[0]
                break
    return voice

gv.setVoice=setVoice                    # and announce the procs to modules
gv.setMC(gv.VOICES,setVoice)

########  LITERALS used in the main module only ########
PLAYLIVE = "Keyb"                       # reacts on "keyboard" interaction
PLAYBACK = "Once"                       # ignores loop markers ("just play the sample with option to stop")
PLAYBACK2X = "Onc2"                     # ignores loop markers with note-off by same note
PLAYLOOP = "Loos"                       # recognize loop markers, note-off by 127-note
PLAYLOOP2X = "Loop"                     # recognize loop markers, note-off by same note
BACKTRACK = "Back"                      # recognize loop markers, loop-off by same note or controller
VELSAMPLE = "Sample"                    # velocity equals sampled value, requires multiple samples to get differentation
VELACCURATE = "Accurate"                # velocity as played, allows for multiple (normalized!) samples for timbre
VELOSTEPS = [127,64,32,16,8,4,2,1]      # accepted numer of velocity layers
CTRLCCS_DEF = "controllerCCs.csv"
KEYNAMES_DEF = "keynotes.csv"
MENU_DEF = "menu.csv"
FXPRESETS_DEF = "FXpresets.csv"
LAYERS_DEF = "layers.csv"


##########  Read LOCAL CONFIG (==> /boot/samplerbox/configuration.txt) for generic use,
#           reading LOCAL CONFIG can be done elsewhere as well if it's one-time or local/optional.
gv.cp=configparser.ConfigParser()
gv.cp.read(gv.CONFIG_LOC + "configuration.txt")

gv.SAMPLES_ONUSB    = gv.cp.get(gv.cfg,"USB_MOUNTPOINT".lower())
gv.SAMPLES_INBOX    = "samples/"
USE_HTTP_GUI        = gv.cp.getboolean(gv.cfg,"USE_HTTP_GUI".lower())
gv.USE_SMFPLAYER    = gv.cp.getboolean(gv.cfg,"USE_SMFPLAYER".lower())
gv.CHAN_AFTOUCH     = gv.cp.getboolean(gv.cfg,"CHANNEL_AFTERTOUCH".lower())
gv.POLY_AFTOUCH     = gv.cp.getboolean(gv.cfg,"POLYPHONIC_AFTERTOUCH".lower())
gv.AFTERTOUCH       = gv.CHAN_AFTOUCH or gv.POLY_AFTOUCH

x=gv.cp.get(gv.cfg,"MULTI_TIMBRALS".lower()).split(',')
gv.MULTI_TIMBRALS={}
for i in range(len(x)):
    gv.MULTI_TIMBRALS[ x[i].strip() ] = [0]*16  # init program=voice per channel#
gv.MULTI_WITHMASTER=gv.cp.get(gv.cfg,"MULTI_WITHMASTER".lower()).split(',')
for i in range(len(gv.MULTI_WITHMASTER)):
    gv.MULTI_TIMBRALS[ gv.MULTI_WITHMASTER[i].strip() ] = [0]*16  # init program=voice per channel#
gv.MIDI_CHANNEL     = gv.cp.getint(gv.cfg,"MIDI_CHANNEL".lower())
gv.MASTER_MESSAGES  = [8,9,11,12,14]
DRUMPAD_CHANNEL     = gv.cp.getint(gv.cfg,"DRUMPAD_CHANNEL".lower())
DRUMPAD_MESSAGES    = [8,9]
if (gv.cp.getboolean(gv.cfg,"DRUMPAD_CONTROLCHANGE".lower())):
    DRUMPAD_MESSAGES.append(11)
if (gv.cp.getboolean(gv.cfg,"DRUMPAD_PROGRAMCHANGE".lower())):
    DRUMPAD_MESSAGES.append(12)

gv.NOTES_CC         = gv.cp.getint(gv.cfg,"NOTES_CC".lower())
gv.PRESET           = gv.cp.getint(gv.cfg,"PRESET".lower())
gv.PRESETBASE       = gv.cp.getint(gv.cfg,"PRESETBASE".lower())
gv.volumeCC         = gv.cp.getfloat(gv.cfg,"volumeCC".lower())
MAX_MEMLOAD         = gv.cp.getint(gv.cfg,"MAX_MEMLOAD".lower())

BOXSAMPLE_MODE      = gv.cp.get(gv.cfg,"BOXSAMPLE_MODE".lower())
BOXVELMODE          = gv.cp.get(gv.cfg,"BOXVELOCITY_MODE".lower())
BOXVELOLEVS         = gv.cp.getint(gv.cfg,"BOXVELOCITY_LEVELS".lower())
BOXSTOP127          = gv.cp.getint(gv.cfg,"BOXSTOP127".lower())
BOXRELEASE          = gv.cp.getint(gv.cfg,"BOXRELEASE".lower())
BOXDAMP             = gv.cp.getint(gv.cfg,"BOXDAMP".lower())
BOXDAMPNOISE        = gv.cp.getboolean(gv.cfg,"BOXDAMPNOISE".lower())
BOXRETRIGGER        = gv.cp.get(gv.cfg,"BOXRETRIGGER".lower())
BOXRELSAMPLE        = gv.cp.get(gv.cfg,"BOXRELSAMPLE".lower())
BOXXFADEOUT         = gv.cp.getint(gv.cfg,"BOXXFADEOUT".lower())
BOXXFADEIN          = gv.cp.getint(gv.cfg,"BOXXFADEIN".lower())
BOXXFADEVOL         = gv.cp.getfloat(gv.cfg,"BOXXFADEVOL".lower())
BOXGAIN             = gv.cp.getfloat(gv.cfg,"BOXGAIN".lower())

########## Initialize other internal globals

gv.GPIO=False
gv.samplesdir = gv.SAMPLES_INBOX
gv.stop127 = BOXSTOP127
gv.sample_mode = BOXSAMPLE_MODE

########## read CONFIGURABLE TABLES from config dir

# Definition of notes, chords and scales
import NotesChordsScales
NotesChordsScales.getdefs()

# Midi controllers, keyboard definition and menu
getcsv.readcontrollerCCs(gv.CONFIG_LOC + CTRLCCS_DEF)
getcsv.readkeynames(gv.CONFIG_LOC + KEYNAMES_DEF)
getcsv.readmenu(gv.CONFIG_LOC + MENU_DEF)

#########################################
# Setup UI and display routine (if any..)
#########################################
import UI

try:
    import display

except:
    print("Error activating requested display routine")
    gp.GPIOcleanup()
    gv.display=gp.NoProc      # set display to dummy

UI.display=gv.display      # announce resulting proc to modules

###########################################
# Audio Effects/Filters
###########################################

# Arpeggiator (play chordnotes sequentially, ie open chords)
# Process replaces the note-on/off logic, so rather cheap
#
import arp

# Reverb, Moogladder, Wah (envelope, lfo, pedal), Delay (echo, flanger), Overdrive and PeakLimiter
# Based on changing the audio output which requires heavy processing
#
import Cpp

# Vibrato, tremolo, pan and rotate (poor man's single speaker leslie)
# Being input based, these effects are cheap: less than 1% CPU on PI3
#
import LFO      # take notice: part of process in audio callback

# Chorus (add pitch modulated and delayed copies of notes)
# Process incorporated in the note-on logic, so rather cheap as well
#
import chorus   # take notice: part of process in midi callback and ARP

# Aftertouch capabilities (if supported by device),
# real time enabling is done depending on definitions
#
if gv.AFTERTOUCH:
    import AfterTouch

# SMFplayer for limited playing and recording standard MIDI files
# Parallel process of sending midinotes to samplerbox midi-in channels
#
if gv.USE_SMFPLAYER:
    import smfplayer

# Now we can finalize the controllerCC's assignments
# (above virtual controllers can be set).
#
gv.CCmapBox = getcsv.readCCmap(gv.CONFIG_LOC + gv.CTRLMAP_DEF)

###########################################
# Audio including Effects/Filters/SMFplayer
###########################################

# Sounddevice setup (detect/determine/check soundcard etc) & callback routine (the actual sound generator)
# Alsamixer setup for volume control (optional)
#
import audio    # import after effects settings to avoid unassigned pointers.
UI.USE_ALSA_MIXER=audio.USE_ALSA_MIXER

getcsv.readFXpresets(gv.CONFIG_LOC + FXPRESETS_DEF)

############################################################
##  SLIGHT MODIFICATION OF PYTHON'S WAVE MODULE
##  TO READ CUE MARKERS & LOOP MARKERS if applicable in mode
############################################################

class waveread(wave.Wave_read):
#class waveread():
    def initfp(self, file):
        s="%s" %file
        wavname = s.split("'")[1]
        self._convert = None
        self._soundpos = 0
        self._cue = []
        self._loops = []
        self._ieee = False
        self._file = Chunk(file, bigendian=0)
        if self._file.getname() != b'RIFF':
            print('%s does not start with RIFF id' % (wavname))
            raise Error('%s does not start with RIFF id' % (wavname))
        if self._file.read(4) != b'WAVE':
            print('%s is not a WAVE file' % (wavname))
            raise Error('%s is not a WAVE file' % (wavname))
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
                    print("Read %s with errors" % (wavname))
                    break   # we have sufficient data so leave the error as is
                else:
                    print("Skipped %s because of chunk.skip error" %file)
                    raise Error("Error in chunk.skip in %s" % (wavname))
            chunkname = chunk.getname()
            if chunkname == b'fmt ':
                try:
                    self._read_fmt_chunk(chunk)
                    self._fmt_chunk_read = 1
                except:
                    print("Invalid fmt chunk in %s, please check: max sample rate = 44100, max bit rate = 24" % (wavname))
                    break
            elif chunkname == b'data':
                if not self._fmt_chunk_read:
                    print('data chunk before fmt chunk in %s' % (wavname))
                else:
                    self._data_chunk = chunk
                    self._nframes = chunk.chunksize // self._framesize
                    self._data_seek_needed = 0
            elif chunkname == b'cue ':
                try:
                    numcue = struct.unpack('<i',chunk.read(4))[0]
                    for i in range(numcue):
                        id, position, datachunkid, chunkstart, blockstart, sampleoffset = struct.unpack('<ii4siii',chunk.read(24))
                        if (sampleoffset>self._cue): self._cue=sampleoffset     # we need the last one in the sample
                        #self._cue.append(sampleoffset)                         # so we don't collect them all anymore...
                except:
                    print("invalid cue chunk in %s" % (wavname))
            elif chunkname == b'smpl':
                manuf, prod, sampleperiod, midiunitynote, midipitchfraction, smptefmt, smpteoffs, numsampleloops, samplerdata = struct.unpack('<iiiiiiiii',chunk.read(36))
                #for i in range(numsampleloops):
                if numsampleloops > 0:      # we don't need the repeat loops...
                    cuepointid, type, start, end, fraction, playcount = struct.unpack('<iiiiii',chunk.read(24))
                    self._loops.append([start,end])
            try:
                chunk.skip()
            except:
                if self._fmt_chunk_read and self._data_chunk:
                    print("Read %s with errors" % (wavname))
                    break   # we have sufficient data so leave the error as is
                else:
                    print("Skipped %s because of chunk.skip error" %file)
                    raise Error("Error in chunk.skip in %s" % (wavname))
        if not self._fmt_chunk_read or not self._data_chunk:
            print('fmt chunk and/or data chunk missing in %s' % (wavname))
            raise Error('fmt chunk and/or data chunk missing in %s' % (wavname))

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
    elif mode==PLAYBACK2X or mode==PLAYLOOP2X:
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
    def __init__(self, sound, voice, playednote, note, velocity, pos, end, loop, stopnote, retune, channel=0):
        self.sound = sound
        self.pos = pos
        self.end = end
        self.loop = loop
        self.fadeoutpos = 0
        self.isfadeout = False
        if pos>0 or voice<0:
            self.isfadein = True
        else:
            self.isfadein = False
        self.voice = voice
        self.playednote = playednote
        self.note = note
        self.retune_played = retune
        self.retune = retune
        self.velocity = velocity
        self.vel = velocity * gv.globalgain
        self.stopnote = stopnote
        self.channel = channel

    def __str__(self):
        return "<PlayingSound note: '%i', velocity: '%i', vel: '%i'>" %(self.note, self.velocity, self.vel)
    def playingnote(self):
        return self.note
    def playingretune(self, upd=False, val=0):
        if upd:
            self.retune = self.retune_played + val
        return self.retune
    def playingvelocity(self):
        return self.velocity
    def playingvolume(self, upd=False, val=0):
        if upd:
            self.vel = val * gv.globalgain
        return (self.vel / gv.globalgain)
    def playingpan(self, upd=False, val=64, width=1):
        if upd:
            self.sound.lpan,self.sound.rpan = samplerbox_audio.splitpan(
                                                            self.sound.leftpan,
                                                            self.sound.rightpan,
                                                            1 - (width * (2*val) / 128)
                                                            )
        return self.sound.pan
    def playingstopnote(self):
        return self.stopnote
    def playingmutegroup(self):
        return self.sound.mutegroup
    def playingstopmode(self):
        return self.sound.stopmode
    def playingrelsample(self):
        return self.sound.relsample
    def playingvoice(self):
        return self.sound.voice
    def playingchannel(self):
        return self.channel
    def playingdampnoise(self):
        return self.sound.dampnoise
    def playing2end(self):
        if self.loop==-1:
            self.fadeout()
        else:
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
    def __init__(self,filename,voice,midinote,rnds,velocity,velmode,mode,release,damp,dampnoise,
                    retrigger,gain,mutegroup,relsample,xfadeout,xfadein,xfadevol,fractions,pan):
        read = False
        for m in gv.samples:
            for i in range(len(gv.samples[m])):
                if gv.samples[m][i].fname==filename:
                    read=True
                    self.loops=gv.samples[m][i].loops
                    self.relmark=gv.samples[m][i].relmark
                    self.eof=gv.samples[m][i].eof
                    self.sampwidth=gv.samples[m][i].sampwidth
                    self.nchannels=gv.samples[m][i].nchannels
                    self.data=gv.samples[m][i].data
        if not read:
            wf = waveread(filename)
            self.loops = wf.getloops()
            self.relmark = wf.getmarkers()
            self.eof = wf.getnframes()
            self.sampwidth = wf.getsampwidth()
            self.nchannels = wf.getnchannels()
            self.data = self.frames2array(wf.readframes(self.eof), self.sampwidth, self.nchannels)
            wf.close()

        self.fname = filename
        self.voice = voice
        self.rnds = rnds
        self.midinote = midinote
        self.velocity = velocity
        self.velsample = True if velmode==VELSAMPLE else False
        self.stopmode = GetStopmode(mode)
        self.release = release
        self.damp = damp
        self.dampnoise = dampnoise
        self.retrigger = retrigger
        self.gain = gain
        self.mutegroup = mutegroup
        self.relsample = relsample
        self.xfadein = xfadein
        self.xfadeout = xfadeout
        self.xfadevol = xfadevol
        self.fractions = fractions
        # panrange 1-127 (so 64=center)
        self.pan = pan              # can be changed real time
        self.leftpan,self.rightpan = samplerbox_audio.splitpan( 1.0, 1.0, 1-2*pan/128 )
        # prevent calculation loop in samplerbox_audio when playing
        self.lpan = self.leftpan    # can be changed real time
        self.rpan = self.rightpan   # can be changed real time
        self.loop = GetLoopmode(mode)       # if no loop requested it's useless to check the wav's capability
        if voice<0:
            self.loop=-1                    # release samples (belong to relsample="S") don't loop
        else:
            self.loop = GetLoopmode(mode)   # if no loop requested it's useless to check the wav's capability
        if self.loop > 0 and self.loops:
            self.loop = self.loops[0][0]         # Yes! the wav can loop
            endloop = self.loops[0][1]
            self.nframes = endloop + 2
            if self.relmark < endloop:
                self.relmark = self.nframes # a potential release marker before loop-end cannot be right
                if relsample == "E":        # if embedded sample was configured, notify this is impossible
                    print("Release of %s set to normal as release marker was not present or invalid" %(filename))
            else:
                if relsample == "E":        # we have found valid release marker with embedded release processing requested
                    self.release=damp if dampnoise else xfadeout # so we can confirm and setup this to operation !!
        else:
            self.loop = -1
            if relsample == "E":            # a release marker without loop is unpredictable, so forget it
                print("Release of %s set to normal as embedded samples require loop" %(filename))
        if self.loop == -1:
            self.relmark = self.eof         # no extra release processing
            self.nframes = self.eof         # and use full length (with default samplerbox release processing)

    def play(self, playednote, note, velocity, startparm, retune, channel=0):
        if self.velsample: velocity=127
        if startparm < 0:       # playing of sampled release is requested
            loop = -1           # a release sample does not loop
            end = self.eof      # and it ends on sample end
            stopnote = 128      # don't react on any artificial note-off's anymore
            velocity = velocity*self.xfadevol # apply the defined volume correction
            if startparm==-1:       # the release sample is embedded
                pos = self.relmark  # so it starts at embed start = the marker
            if startparm==-2:       # the release sample is separate
                pos=0               # starting at its beginning
        else:
            pos = startparm     # normally 0, chorus needs small displacement
            end = self.nframes  # play till end of loop/file as 
            loop = self.loop    # we loop if possible by the sample
            if arp.active or channel>0:     # arpeggiator and sequencer are keyboard robots
                stopnote=128    # ..so force keyboardmode
            else:
                stopnote=self.stopmode  # use stopmode to determine possible stopnote
                if stopnote==2 or stopnote==3:
                    stopnote = playednote     # let autochordnotes be turned off by their trigger only
                elif stopnote==127:
                    stopnote = 127-note
        if self.mutegroup > 0 and len(gv.playingsounds) > 0: #mute all sounds with same mutegroup of triggering/played key
            for ps in gv.playingsounds:
                if self.mutegroup==ps.playingmutegroup() and playednote!=ps.playednote: # don't mute notes played by ourself (like chords & chorus)
                    ps.fadeout(False)   # fadeout the mutegroup sound(s) and cleanup admin where possible
                    try:
                        gv.playingnotes[ps.playednote]=[]
                    except:
                        pass
                    if ps.playednote>=gv.BTNOTES and ps.playednote<gv.MTCHNOTES:
                        gv.playingbacktracks-=1
                    try:
                        gv.triggernotes[ps.note]=128
                        gv.playingnotes[ps.note]=[]
                        for triggerednote in range(128):   # also mute chordnotes triggered by this muted note
                            if gv.triggernotes[triggerednote] == ps.note:   # did we make this one play ?
                                if triggerednote in gv.playingnotes:
                                    for m in gv.playingnotes[triggerednote]:
                                        m.fadeout()
                                        gv.playingnotes[triggerednote] = []
                                        gv.triggernotes[triggerednote] = 128  # housekeeping
                    except: pass
        snd = PlayingSound(self, self.voice, playednote, note, velocity, pos, end, loop, stopnote, retune, channel)
        gv.playingsounds.append(snd)
        return snd

    def frames2array(self, data, sampwidth, numchan):
        if sampwidth == 2:
            npdata = numpy.frombuffer(data, dtype = numpy.int16)
        elif sampwidth == 3:    # convert 24bit to 16bit
            npdata = samplerbox_audio.binary24_to_int16(data, len(data)/3)
        if numchan == 1:        # make a left and right track from a mone sample
            npdata = numpy.repeat(npdata, 2)
        return npdata

#########################################
##  MIDI
##   - general routines
##   - CALLBACK
#########################################

def ControlChange(CCnum, CCval):
    mc=False
    for m in gv.CCmap:    # look for mapped controllers
        j=m[0]
        if (gv.controllerCCs[j][1]==CCnum
        and (gv.controllerCCs[j][2]==-1 or gv.controllerCCs[j][2]==CCval or gv.MC[m[1]][1]==3)):
            if m[2]!=None: CCval=m[2]
            #print ("Recognized %d:%d<=>%s related to %s" %(CCnum, CCval, gv.controllerCCs[j][0], gv.MC[m[1]][0]) )
            gv.MC[m[1]][2](CCval,gv.MC[m[1]][0])
            mc=True
            break
    if not mc and (CCnum==120 or CCnum==123):   # "All sounds off" or "all notes off"
        AllNotesOff()
def AllNotesOff(scope=-1,*z):
    # scope: see EffectsOff below
    # stop the robots first
    if gv.USE_SMFPLAYER:
        smfplayer.loopit=False
        smfplayer.stopit=True
    if scope>-1: scope=-1
    arp.power(False)
    gv.playingbacktracks = 0
    # empty all queues
    gv.playingsounds = []
    gv.playingnotes = {}
    gv.sustainplayingnotes = []
    gv.triggernotes = [128]*128     # fill with unplayable note
    # turn off effects & reset display
    EffectsOff(scope)
    CallbackState()
    gv.display("")
def EffectsOff(scope=-1,*z):
    # scope:
    #   -1 = switch off effects without affecting parameters
    #   -2 = reset effects parameters to system default
    #   -3 = reset effects parameters to set default
    #   -4 = reset effects parameters to voice default
    #   - other values controlled by the subroutines, usually fallback to -1: just turn off
    Cpp.ResetAll(scope)
    LFO.reset(scope)
    chorus.reset(scope)
    #AutoChordOff()
def ProgramUp(CCval,*z):
    x=gp.getindex(gv.PRESET,gv.presetlist)+1
    if x>=len(gv.presetlist): x=0
    gv.PRESET=gv.presetlist[x][0]
    gv.LoadSamples()
def ProgramDown(CCval,*z):
    x=gp.getindex(gv.PRESET,gv.presetlist)-1
    if x<0: x=len(gv.presetlist)-1
    gv.PRESET=gv.presetlist[x][0]
    gv.LoadSamples()
def MidiVolume(CCval,*z):
    gv.volumeCC = CCval / 127.0
def AutoChordOff(x=0,*z):
    gv.currchord = 0
    gv.currscale = 0
    gv.display("")
def PitchWheel(LSB,MSB=0,*z):   # This allows for single and double precision.
    try: MSB+=0 # If mapped to a double precision pitch wheel, it should work.
    except:     # But the use/result of double precision controllers does not
        MSB=LSB # justify the complexity it will introduce in the mapping.
        LSB=0   # So I ignore them here. If you want to try, plse share with me.
    gv.PITCHBEND=(((128*MSB+LSB)/gv.pitchdiv)-gv.pitchneutral)*gv.pitchnotes
def PitchSens(CCval,*z):
    gv.pitchnotes = (24*CCval+100)/127
sustain=False
def Sustain(CCval,*z):
    global sustain
    if gv.sample_mode==PLAYLIVE:
        if (CCval == 0):    # sustain off
            sustain = False
            for n in gv.sustainplayingnotes:
                n.fadeout()
                PlayRelSample(n.playingrelsample(),n.playingvoice(),n.playingnote(),n.playingvolume(),n.playingretune(),n.playingchannel())
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
                        DampNoise(m)
    else: damp = False
def DampNew(CCval,*z):
    global damp
    damp=True if (CCval>0) else False
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
            DampNoise(m)
        gv.sustainplayingnotes = []
def DampNoise(m):
    if m.playingdampnoise():
        PlayRelSample(m.playingrelsample(),m.playingvoice(),m.playingnote(),m.playingvolume(),m.playingretune(),m.playingchannel(),True)
def PlayRelSample(relsample,voice,playnote,velocity,retune,channel=0,play_as_is=False):
    if relsample in "ES":
        if relsample=='E':
            startparm=-1
        else:
            startparm=-2
            voice=-voice
        PlaySample(playnote,playnote,voice,velocity,startparm,retune,channel,play_as_is)
lastrnds = {}
def PlaySample(midinote,playnote,voice,velocity,startparm,retune,channel=0,play_as_is=False):
    global lastrnds
    velolevs=gv.voicelist[gp.getindex(voice,gv.voicelist)][4]
    velidx=int(1.0*(velocity*velolevs)/128+.9999)   # roundup without math
    if (playnote,velidx,voice) not in gv.samples:
        print("Note not loaded or filled")
        return
    if startparm==-1:
        sample=lastrnds[playnote][0][lastrnds[playnote][1]]      # use the same sample for the release sample
    else:
        notesamples=gv.samples[playnote,velidx,voice]   # Get the list of available samples for this note/velocity/voice
        gotcha=False
        if startparm==-2:   # try to find corresponding release sample
            rnds=lastrnds[playnote][0][lastrnds[playnote][1]].rnds
            for sample in notesamples:  # the order may not be the same
                if sample.rnds==rnds:   # so pick the right entry
                    gothcha=True
                    break
        if not gotcha:      # for note-on's and absent separate release sample
            rnd=random.randint(0,len(notesamples))      # no duplicates checking as David did, because we use random from NumPy
            sample=notesamples[rnd]                     # still we need to save the choice for a possible release sample
            lastrnds[playnote]=[notesamples,rnd]
    #print "About to play note: %d=>%d, rnds: %s, relsamples: %s, play_as_is: %s, voice: %d, file: %s" % (midinote,playnote, sample.rnds, sample.relsample, play_as_is, sample.voice, sample.fname)
    if play_as_is:
        sample.play(midinote,playnote,velocity,startparm,retune,channel)
    else:
        gv.playingnotes.setdefault(channel*gv.MTCHNOTES+playnote,[]).append(sample.play(midinote,playnote,velocity,startparm,retune,channel))
gv.playingbacktracks=0
def playBackTrack(x,*z):
    playnote=int(x)+gv.BTNOTES
    if playnote in gv.playingnotes and gv.playingnotes[playnote]!=[]: # is the track playing?
        gv.playingbacktracks-=1
        for m in gv.playingnotes[playnote]:
            m.playing2end()         # let it finish
    else:
        try:
            PlaySample(playnote,playnote,0,127,0,0)
            gv.playingbacktracks+=1
        except:
            print('Unassigned/unfilled track or other exception for backtrack %s->%d' % (x,playnote))

    # announce the procs to modules, except for the note related (~polyphonic aftertouch)
gv.setMC(gv.PANIC,AllNotesOff)
gv.setMC(gv.EFFECTSOFF,EffectsOff)
gv.setMC(gv.PROGUP,ProgramUp)
gv.setMC(gv.PROGDN,ProgramDown)
gv.setMC(gv.VOLUME,MidiVolume)
gv.setMC(gv.AUTOCHORDOFF,AutoChordOff)
gv.setMC(gv.PITCHWHEEL,PitchWheel)
gv.setMC(gv.PITCHSENS,PitchSens)
gv.setMC(gv.SUSTAIN,Sustain)
gv.setMC(gv.DAMP,Damp)
gv.setMC(gv.DAMPNEW,DampNew)
gv.setMC(gv.DAMPLAST,DampLast)
gv.DampNoise=DampNoise
gv.PlayRelSample=PlayRelSample
gv.PlaySample=PlaySample
gv.setMC(gv.BACKTRACKS,playBackTrack)

gv.CallbackActive = False
def CallbackState(state=False):
    gv.CallbackActive = state

def CallbackIsolateMT(MT_in, turnon=True):
    # save/restore voice and some effects, set/reset voice according channel
    if turnon:
            gv.sqsav_chord=gv.currchord
            gv.sqsav_chorus=chorus.effect
            chorus.setType(False)
            gv.sqsav_voice=gv.currvoice
            setVoice(MT_in,-2)
    else:
            gv.currchord=gv.sqsav_chord
            chorus.effect=gv.sqsav_chorus
            setVoice(gv.sqsav_voice,-2)
    
def MidiCallback(mididev, imessage, time_stamp):
    global CallbackActive
    # -------------------------------------------------------
    # Deal with midi-thru and check state before continuing
    # -------------------------------------------------------
    #print ( 'MidiCallback: %s -> %s = Channel %d, message %d' \
    #    % (mididev, imessage, (imessage[0]&0xF)+1 , imessage[0]>>4) )

    for outport in gv.outports:
        if mididev != gv.outports[outport][0]:  # don't return to sender
            #print ( " ... forwarding to '%s'" %( gv.outports[outport][0]) )
            gv.outports[outport][1].send_raw(*imessage)

    qcount = 0
    while gv.CallbackActive:
        # Poor man's solution for RTmidi, serialMIDI and SBplayer competing for Callback
        qcount += 1
        if qcount > 5:
            print ("Callback queing killed")
            CallbackState()
        else:
            msleep(1)
    CallbackState(True)

    message = imessage
    # -------------------------------------------------------
    # Filter on supported messages and do some inits
    # and deal recording
    # -------------------------------------------------------
    messagetype = message[0] >> 4
    messagechannel = (message[0]&0xF)   # get channel#

    if messagetype == 0xFF:     # "realtime" reset has to reset all activity & settings
        AllNotesOff()           # (..other realtime will be ignored below..)
        return CallbackState()
    if messagetype not in gv.MASTER_MESSAGES:
        return CallbackState()                  # skip things we can't deal with anyway
 
    if gv.MidiRecorder:         # Record remaining interesting stuff if needed
        gv.MidiRecorder( mididev, (mididev in gv.MULTI_TIMBRALS),
                        messagechannel, messagetype, message )

    MIDIchannel = messagechannel + 1    # make channel# human..
    keyboardarea = True
    # ----------------------------------------------------------------
    # Multitimbrals identification and "hardware remap" of the drumpad
    # ----------------------------------------------------------------
    MT_in=False
    if mididev in gv.MULTI_TIMBRALS:
        MT_in = True
    elif MIDIchannel == gv.MIDI_CHANNEL:
        MIDIchannel = 0
    else:
        if mididev in gv.MULTI_WITHMASTER:
            MT_in = True

    if MT_in:
        if messagetype in [8,9,12]: # we only accept note on/off and program change commands from the sequencers and other multitimbrals
            if messagetype==12:
                gv.MULTI_TIMBRALS[mididev][messagechannel]=setMTvoice(mididev,MIDIchannel,message[1]+1)
                return CallbackState()
            if gv.MULTI_TIMBRALS[mididev][messagechannel]==0:     # if a channel hasn't sent a programchange, assume voice=channel. This is not uncommon from drumchannel=10
                gv.MULTI_TIMBRALS[mididev][messagechannel]=setMTvoice(mididev,MIDIchannel,MIDIchannel)
            MT_in=gv.MULTI_TIMBRALS[mididev][messagechannel]

    elif MIDIchannel==DRUMPAD_CHANNEL:
        if messagetype in DRUMPAD_MESSAGES:
            MIDIchannel=0
            if messagetype==8 or messagetype==9:        # Remap notes if necessary
                for i in range(len(gv.drumpadmap)):
                    if gv.drumpadmap[i][0]==message[1]:
                        message[1]=gv.drumpadmap[i][1]
                        break       # found it, stop wasting time
    # -------------------------------------------------------
    # Then process channel commands if not muted
    # -------------------------------------------------------
    if ((MIDIchannel==0) or MT_in) and (gv.midi_mute==False) and len(message)>1:
        midinote = message[1]
        mtchnote = MIDIchannel*gv.MTCHNOTES+midinote
        velocity = message[2] if len(message) > 2 else None

        if messagetype==8 or messagetype==9:           # We may have a note on/off
            retune=0
            if not MT_in:
                i=gp.getindex(midinote,gv.notemapping)
                if i>-1:        # do we have a mapped note ?
                    if gv.notemapping[i][2]==-2:      # This key is actually a CC = control change
                        if velocity==0 or messagetype==8: midinote=0
                        ControlChange(gv.NOTES_CC, midinote)
                        return CallbackState()
                    midinote=gv.notemapping[i][2]
                    mtchnote=midinote
                    retune=gv.notemapping[i][3]
                    if gv.notemapping[i][4]>0:
                        setVoice(gv.notemapping[i][4],-1)
            if velocity==0: messagetype=8           # prevent complexity in the rest of the checking
            if MT_in or (midinote>(127-gv.stop127) and midinote<gv.stop127):
                keyboardarea=True
            else:
                keyboardarea=False
            #if gv.triggernotes[midinote]==midinote and velocity==64: # Older MIDI implementations
            #    messagetype=8                                        # (like Roland PT-3100)
            if arp.active and keyboardarea and not MT_in:
                arp.note_onoff(messagetype, midinote, velocity)
                return CallbackState()
            if messagetype==8 and not MT_in:                # should this note-off be ignored?
                if midinote in gv.playingnotes and gv.triggernotes[midinote]<128:
                       for m in gv.playingnotes[midinote]:
                           if m.playingstopnote() < 128:    # are we in a special mode
                               return CallbackState()                       # if so, then ignore this note-off
                else:
                    return CallbackState()                                  # nothing's playing, so there is nothing to stop
            if MT_in:               # save voice and some effects, set voice according channel and reset those effects
                CallbackIsolateMT(MT_in)
            if messagetype == 9:    # is a note-off hidden in this note-on ?
                if mtchnote in gv.playingnotes:     # this can only be if the note is already playing
                    for m in gv.playingnotes[mtchnote]:
                        xnote=m.playingstopnote()   # yes, so check it's stopnote
                        if xnote>-1 and xnote<128:  # not in once or keyboard mode (covers "not MT_in")
                            if midinote==xnote:     # could it be a push-twice stop?
                                if m.playingstopmode()==3:  # backtracks end on sample end
                                    m.playing2end()         # so just let it finish
                                    gv.playingbacktracks-=1
                                    return CallbackState()
                                else:
                                    messagetype = 8                     # all the others have an instant end
                            elif midinote >= gv.stop127:   # could it be mirrored stop?
                                if (midinote-127) in gv.playingnotes:  # is the possible mirror note-on active?
                                    for m in gv.playingnotes[midinote-127]:
                                        if midinote==m.playingstopnote():   # and has it mirrored stop?
                                            messagetype = 8

            if messagetype == 9:    # Note on
                try:
                    gv.last_midinote=midinote      # save original midinote for the webgui
                    if keyboardarea and not MT_in:
                        gv.last_musicnote=midinote-12*int(midinote/12) # do a "remainder midinote/12" without having to import the full math module
                        if gv.currscale>0:               # scales require a chords mix
                            gv.currchord = gv.scalechord[gv.currscale][gv.last_musicnote]
                        playchord=gv.currchord
                        layers = gv.currlayers  # master keyboard area can be layered
                        gv.lastvel = velocity   # reference for the aftertouch
                    else:
                        gv.last_musicnote=12 # Set musicnotesymbol to "effects" in webgui
                        playchord=0       # no chords outside keyboardrange / in effects channel.
                        layers = [ [gv.currvoice, 1] ] # no layering either
                    for n in range (len(gv.chordnote[playchord])):
                        playnote=midinote+gv.chordnote[playchord][n]
                        if sustain:   # don't pile up sustain
                            for n in gv.sustainplayingnotes:
                                if n.playingnote() == playnote:
                                    n.fadeout(True)         # gracefully drop it
                        if gv.triggernotes[playnote]<128 and not MT_in: # cleanup in case of retrigger
                            if playnote in gv.playingnotes: # occurs in once/loops modes and chords
                                for m in gv.playingnotes[playnote]:
                                    if m.sound.retrigger!='Y':  # playing double notes not allowed
                                        if m.sound.retrigger=='R':
                                            m.fadeout(True)     # ..either release
                                        else:
                                            m.fadeout(False)    # ..or damp without optional dampnoise (considered unsuitable, based on current knowledge)
                                    #gv.playingnotes[playnote]=[]   # unnecessary housekeeping as we will refill it immediately..
                        #voice=gv.currvoice
                        for layer in layers:
                            voice = layer[0]
                            layvel = layer[1] * velocity
                            if layvel>127:
                                layvel = 127    # prevent distortion
                            #print "start playingnotes playnote %d, velocity %d, voice %d, retune %d" %(playnote, velocity, voice, retune)
                            if chorus.effect:
                                PlaySample(midinote,playnote,voice,layvel*chorus.gain,0,retune,MIDIchannel)
                                PlaySample(midinote,playnote,voice,layvel*chorus.gain,2,retune-(chorus.depth/2+1),MIDIchannel)
                                PlaySample(midinote,playnote,voice,layvel*chorus.gain,5,retune+chorus.depth,MIDIchannel)
                            else:
                                PlaySample(midinote,playnote,voice,layvel,0,retune,MIDIchannel)
                            if not MT_in and playnote in gv.playingnotes:
                                for m in gv.playingnotes[playnote]:
                                    stopmode = m.playingstopmode()
                                    if stopmode == 3:
                                        gv.playingbacktracks+=1
                                    else:
                                        gv.triggernotes[playnote]=midinote   # we are last playing this one
                                    if keyboardarea and damp:
                                        if stopmode!= 3:    # don't damp backtracks
                                            if sustain:  # damplast (=play untill pedal released
                                                gv.sustainplayingnotes.append(m)
                                            else:           # damp+dampnew (=damp played notes immediately)
                                                m.fadeout(False)
                                                DampNoise(m)
                                            gv.triggernotes[playnote]=128
                                            gv.playingnotes[playnote]=[]
                        # hier stopt de layer iteratie, gaat er iets fout met de except??
                except:
                    err = 'Unassigned note or other exception in note %d, voice %d' % (midinote,voice)
                    if MT_in:               # restore previous saved voice and some effects
                        err = '%s, MT channel %d' %MIDIchannel
                        CallbackIsolateMT(MT_in, False)
                    print(err)
                    return CallbackState()

            elif messagetype == 8:  # Note off
                if MT_in:
                    if mtchnote in gv.playingnotes:
                        for m in gv.playingnotes[mtchnote]:
                            velmixer = m.playingvelocity()  # save org value for release sample
                            m.fadeout()
                            gv.playingnotes[mtchnote] = []
                            PlayRelSample(m.playingrelsample(),m.playingvoice(),m.playingnote(),m.playingvolume(),m.playingretune(),m.playingchannel())
                else:
                    for playnote in range(128):
                        if gv.triggernotes[playnote] == midinote:   # did we make this one play ?
                            gv.triggernotes[playnote] = 128  # housekeeping
                            if playnote in gv.playingnotes:
                                for m in gv.playingnotes[playnote]:
                                    stopmode = m.playingstopmode()
                                    if stopmode == 3:
                                        m.playing2end()
                                    elif sustain and stopmode==128 and keyboardarea:    # sustain only works for mode=keyb notes in the keyboard area
                                        gv.sustainplayingnotes.append(m)
                                        gv.playingnotes[playnote] = []
                                    else:
                                        m.fadeout()
                                        gv.playingnotes[playnote] = []
                                        PlayRelSample(m.playingrelsample(),m.playingvoice(),m.playingnote(),m.playingvolume(),m.playingretune(),m.playingchannel())
                                        gv.playingnotes[playnote] = []

            if MT_in:               # restore previous saved voice and some effects
                CallbackIsolateMT(MT_in, False)

        elif messagetype == 10: # Polyphonic aftertouch
            done = False
            if midinote in gv.playingnotes:
                for playnote in range(128):
                    if gv.triggernotes[playnote] == midinote:   # did we make this one play ?
                        done = True
                        AfterTouch.Polyphonic(playnote,velocity)    # velocity=pressure
            if not done:
                # deal with notepair followers missing the master
                AfterTouch.Polyphonic(midinote,velocity)    # velocity=pressure

        elif messagetype == 11: # control change (CC = Continuous Controllers)
            ControlChange(midinote,velocity)    # midinote=CCnum, velocity=CCval

        elif messagetype == 12: # Program change
            UI.Preset(midinote+gv.PRESETBASE)   # midinote=program#

        elif messagetype == 13: # Channel aftertouch
            AfterTouch.Channel(midinote)        # midinote=pressure

        elif messagetype == 14: # Pitch Bend (note contains MSB, velocity contains 0 or LSB if supported by controller)
            PitchWheel(midinote,velocity)       # midinote=MSB, velocity=LSB

        CallbackState()

gv.MidiCallback = MidiCallback

#########################################
##  LOAD SAMPLES
#########################################

LoadingThread = None
LoadingInterrupt = False

def LoadSamples():
    global LoadingThread
    global LoadingInterrupt

    gv.ActuallyLoading=True     # bookkeeping as quick as possible
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
    gv.ActuallyLoading=True     # bookkeeping for safety
    gv.currbase = gv.basename

    gv.samplesdir = gv.SAMPLES_INBOX
    try:
        if os.listdir(gv.SAMPLES_ONUSB):
            for f in os.listdir(gv.SAMPLES_ONUSB):
                if re.match(r'[0-9]* .*', f):
                    if os.path.isdir(os.path.join(gv.SAMPLES_ONUSB,f)):
                        gv.samplesdir = gv.SAMPLES_ONUSB
                        break
            if gv.samplesdir == gv.SAMPLES_INBOX:
                print ("USB device on %s has no samplesets, using SD space on %s" %(gv.SAMPLES_ONUSB, gv.SAMPLES_INBOX) )
    except:
        print ("Error reading USB device mounted on %s" %gv.SAMPLES_ONUSB)

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
        print("Error reading %s" %gv.samplesdir)
    gv.presetlist=presetlist
    if gv.basename=="None":
        if len(gv.presetlist)>0:
            gv.PRESET=gv.presetlist[0][0]
            gv.basename=gv.presetlist[0][1]
            print("Missing default preset=0, first available is %d" %gv.PRESET)
        else: print("No sample sets found")

    print("We have %s, we want %s" %(gv.currbase, gv.basename))
    if gv.basename:
        if gv.basename == gv.currbase:      # don't waste time reloading a patch
            gv.ActuallyLoading=False
            gv.display("")
            return
        dirname = os.path.join(gv.samplesdir, gv.basename)
        if not os.path.isdir(dirname):      # and don't switch to a non-existing dir
            gv.ActuallyLoading=False
            gv.display("")
            print ("%s does not exist, ignored" % dirname)
            return

    midi_mute = gv.midi_mute        # go temporarily forced on mute
    gv.midi_mute = True
    AllNotesOff(-3)                 # reset to set defaults
    #mode=[]
    gv.globalgain = BOXGAIN
    gv.currvoice = 0
    gv.currnotemap=""
    gv.notemapping=[]
    gv.CCmap = list(gv.CCmapBox)
    gv.sample_mode=BOXSAMPLE_MODE   # fallback to the samplerbox default
    PREVELMODE=BOXVELMODE           # fallback to the samplerbox default
    gv.stop127=BOXSTOP127           # fallback to the samplerbox default
    gv.pitchnotes=gv.PITCHRANGE     # fallback to the samplerbox default
    PREVELOLEVS=BOXVELOLEVS         # fallback to the samplerbox default
    PRERELEASE=BOXRELEASE           # fallback to the samplerbox default
    PREDAMP=BOXDAMP                 # fallback to the samplerbox default
    PREDAMPNOISE="Y" if BOXDAMPNOISE else "N"       # fallback to the samplerbox default
    PRERETRIGGER=BOXRETRIGGER       # fallback to the samplerbox default
    PREXFADEOUT=BOXXFADEOUT         # fallback to the samplerbox default
    PREXFADEIN=BOXXFADEIN           # fallback to the samplerbox default
    PREXFADEVOL=BOXXFADEVOL         # fallback to the samplerbox default
    PRERELSAMPLE=BOXRELSAMPLE       # fallback to the samplerbox default
    PREFRACTIONS=1                  # 1 midinote for 1 semitone for note filling; fractions=2 fills Q-notes = the octave having 24 notes in equal intervals
    PREQNOTE = "N"                  # The midinotes mapping the quarternotes (No/Yes/Even/Odd)
    PRENOTEMAP=""
    PREFXPRESET=""
    PRETRANSPOSE=0
    PREMUTEGROUP=0
    PREFILLNOTE = 'Y'
    PRELAYERS = ''
    if gv.POLY_AFTOUCH:
        AfterTouch.fillpairs(init=True)
    PREPAFPAIR = ''
    for dev in gv.MULTI_TIMBRALS:
        gv.MULTI_TIMBRALS[dev] = [0]*16     # init program=voice per channel#
    gv.samples = {}
    gv.smfseqs = {}
    gv.currsmf = 0
    gv.smfdrums={}
    fillnotes = {}
    gv.btracklist=[]
    tracknames  = []
    for backtrack in range(128):
        tracknames.append([False, "", ""])
    gv.voicelist = []        # voicenumber, description, mode, notemap, velocitylevels, fxpreset, layers
    voicenames  = []
    gv.DefinitionTxt = ''
    gv.DefinitionErr = ''

    if not gv.basename: 
        print('Preset empty: %s' % gv.PRESET)
        gv.ActuallyLoading=False
        gv.basename = "%d Empty preset" %gv.PRESET
        gv.display("","E%03d" % gv.PRESET)
        gv.midi_mute = midi_mute    # restore mute status
        return

    #print 'Preset loading: %s ' % gv.basename
    gv.display("Loading %s" % gv.basename,"L%03d" % gv.PRESET)
    getcsv.readnotemap(os.path.join(dirname, gv.NOTEMAP_DEF))
    gv.CCmapSet=getcsv.readCCmap(os.path.join(dirname, gv.CTRLMAP_DEF), True)
    getcsv.readMTchannelmap(os.path.join(dirname, gv.VOICEMAP_DEF))
    getcsv.readFXpresets(os.path.join(dirname, FXPRESETS_DEF), True)
    gp.setFXpresets("Default")
    getcsv.readlayers( os.path.join(dirname, LAYERS_DEF) )

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
                            print("Stopnotes start of %d invalid, set to %d" % (gv.stop127, BOXSTOP127))
                            gv.stop127 = BOXSTOP127
                        continue
                    if r'%%release' in pattern:
                        PRERELEASE = (int(pattern.split('=')[1].strip()))
                        #127#if PRERELEASE > 127:
                        #    print("Release of %d limited to %d" % (PRERELEASE, 127))
                        #    PRERELEASE = 127
                        continue
                    if r'%%dampnoise' in pattern:
                        m = pattern.split('=')[1].strip().title()
                        if m in ['Y','N']:
                            PREDAMPNOISE = m
                        continue
                    if r'%%damp' in pattern:
                        PREDAMP = (int(pattern.split('=')[1].strip()))
                        #127#if PREDAMP > 127:
                        #    print("Damp of %d limited to %d" % (PREDAMP, 127))
                        #    PREDAMP = 127
                        continue
                    if r'%%retrigger' in pattern:
                        m = pattern.split('=')[1].strip().title()
                        if m in ['R','D','Y']:
                            PRERETRIGGER = m
                        continue
                    if r'%%xfadeout' in pattern:
                        PREXFADEOUT = (int(pattern.split('=')[1].strip()))
                        #127#if PREXFADEOUT > 127:
                        #    print("xfadeout of %d limited to %d" % (PREXFADEOUT, 127))
                        #    PREXFADEOUT = 127
                        continue
                    if r'%%xfadein' in pattern:
                        PREXFADEIN = (int(pattern.split('=')[1].strip()))
                        #127#if PREXFADEIN > 127:
                        #    print("xfadein of %d limited to %d" % (PREXFADEIN, 127))
                        #    PREXFADEIN = 127
                        continue
                    if r'%%xfadevol' in pattern:
                        PREXFADEVOL = abs(float(pattern.split('=')[1].strip()))
                        continue
                    if r'%%fillnote' in pattern:
                        m = pattern.split('=')[1].strip().title()
                        if m in ['Y','N','F']:
                            PREFILLNOTE = m
                        continue
                    if r'%%qnote' in pattern:
                        m = pattern.split('=')[1].strip().title()
                        if m in ['Y','O','E']:
                            PREQNOTE = m
                            PREFRACTIONS = 2
                        continue
                    if r'%%pafpair' in pattern:
                        if gv.POLY_AFTOUCH:
                            m = pattern.split('=')[1].strip().title()
                            AfterTouch.fillpairs(0,PREFRACTIONS,m)
                    if r'%%pitchbend' in pattern:
                        gv.pitchnotes = abs(int(pattern.split('=')[1].strip()))
                        if gv.pitchnotes > 12:
                            print("Pitchbend of %d limited to 12" % gv.pitchnotes)
                            gv.pitchnotes = 12
                        gv.pitchnotes *= 2     # actually it is 12 up and 12 down
                        continue
                    if r'%%mode' in pattern:
                        m = pattern.split('=')[1].strip().title()
                        if m == "Loo2": m = "Loop"  # compatibility..
                        if (GetStopmode(m)>-2): gv.sample_mode = m
                        continue
                    if r'%%velmode' in pattern:
                        m = pattern.split('=')[1].strip().title()
                        if m in [VELSAMPLE,VELACCURATE]: PREVELMODE = m
                        continue
                    if r'%%velolevs' in pattern:
                        m = abs(int(pattern.split('=')[1].strip()))
                        if m not in VELOSTEPS:
                            print("velolevs %d, should be one of %s" %(m, VELOSTEPS))
                        else:
                            PREVELOLEVS=m
                        continue
                    if r'%%relsample' in pattern:
                        m = pattern.split('=')[1].strip().title()
                        if m in ['E','S','N']:
                            PRERELSAMPLE = m
                        continue
                    if r'%%backtrack' in pattern:
                        m = pattern.split(':')[1].strip()
                        v,m=m.split("=")
                        if int(v)>127:
                            print("Backtrackname %m ignored" %m)
                        else:
                            tracknames[int(v)][1]=m
                        continue
                    if r'%%voice' in pattern:
                        m = pattern.split(':')[1].strip()
                        v,m=m.split("=")
                        voicenames.append([int(v),v+" "+m])
                        continue
                    if r'%%notemap' in pattern:
                        PRENOTEMAP = pattern.split('=')[1].strip().title()
                        continue
                    if r'%%fxpreset' in pattern:
                        PREFXPRESET = pattern.split('=')[1].strip().title()
                        continue
                    if r'%%layers' in pattern:
                        PRELAYERS = pattern.split('=')[1].strip().title()
                        continue
                    defaultparams = { 'midinote':'-128', 'velocity':'-1', 'gain':'1', 'notename':'', 'voice':'1', 'velolevs':PREVELOLEVS, 'mode':gv.sample_mode, 'velmode':PREVELMODE,\
                                      'transpose':PRETRANSPOSE, 'release':PRERELEASE, 'damp':PREDAMP, 'dampnoise':PREDAMPNOISE, 'retrigger':PRERETRIGGER, 'mutegroup':PREMUTEGROUP,\
                                      'relsample':PRERELSAMPLE, 'xfadeout':PREXFADEOUT, 'xfadein':PREXFADEIN, 'xfadevol':PREXFADEVOL, 'qnote':PREQNOTE, 'notemap':PRENOTEMAP, 'pan':'64',\
                                      'fxpreset':PREFXPRESET, 'layers':PRELAYERS, 'pafpair':PREPAFPAIR, 'fillnote':PREFILLNOTE, 'rnds':'1', 'smfseq':'1', 'voicemap':"", 'backtrack':'-1'}
                    if len(pattern.split(',')) > 1:
                        defaultparams.update(dict([item.split('=') for item in pattern.split(',', 1)[1].replace(' ','').replace('%', '').split(',')]))
                    pattern = pattern.split(',')[0]
                    pattern = re.escape(pattern.strip())
                    pattern = pattern.replace(r"%midinote", r"(?P<midinote>\d+)").replace(r"%velocity", r"(?P<velocity>\d+)").replace(r"%gain", r"(?P<gain>[-+]?\d*\.?\d+)")\
                                    .replace(r"%voice", r"(?P<voice>\d+)").replace(r"%velolevs", r"(?P<velolevs>\d+)").replace(r"%mutegroup", r"(?P<mutegroup>\d+)")\
                                    .replace(r"%fillnote", r"(?P<fillnote>[YNFynf])").replace(r"%mode", r"(?P<mode>[A-Za-z0-9])").replace(r"%velmode", r"(?P<velmode>[A-Za-z])")\
                                    .replace(r"%transpose", r"(?P<transpose>\d+)").replace(r"%release", r"(?P<release>\d+)").replace(r"%damp", r"(?P<damp>\d+)").replace(r"%pan", r"(?P<pan>\d+)")\
                                    .replace(r"%dampnoise", r"(?P<dampnoise>\[YNyn])").replace(r"%retrigger", r"(?P<retrigger>[YyRrDd])").replace(r"%relsample", r"(?P<relsample>[NnSsEe])")\
                                    .replace(r"%xfadeout", r"(?P<xfadeout>\d+)").replace(r"%xfadein", r"(?P<xfadein>\d+)").replace(r"%xfadevol", r"(?P<xfadevol>\d+)")\
                                    .replace(r"%rnds", r"(?P<rnds>[1-9])").replace(r"%qnote", r"(?P<qnote>[YyNnOoEe])").replace(r"%notemap", r"(?P<notemap>[A-Za-z0-9]\_\-\&)")\
                                    .replace(r"%fxpreset", r"(?P<fxpreset>[A-Za-z0-9]\_\-\&)").replace(r"%smfseq", r"(?P<smfseq>\d+)").replace(r"%voicemap", r"(?P<voicemap>[A-Za-z0-9]\_\-\&)")\
                                    .replace(r"%backtrack", r"(?P<backtrack>\d+)").replace(r"%layers", r"(?P<layers>[A-Za-z0-9]\_\-\&)").replace(r"%pafpair", r"(?P<pafpair>[A-Ga-gks#\-0-9();])")\
                                    .replace(r"%notename", r"(?P<notename>[A-Ga-g][#ks]?[0-9])").replace(r"\*", r".*?").strip()    # .*? => non greedy
                    for fname in os.listdir(dirname):
                        if LoadingInterrupt:
                            print('Loading % s interrupted...' % dirname)
                            gv.ActuallyLoading=False
                            return
                        m = re.match(pattern, fname)
                        if m:
                            #print ('Processing %s in %s' %(fname,dirname))
                            mem=psutil.virtual_memory()
                            if mem.percent>MAX_MEMLOAD:
                                print("'%s' skipped because memory reached %d%%" %(fname,mem.percent))
                                continue
                            info = m.groupdict()
                            if os.path.splitext(fname)[1].lower()=='.mid':
                                if gv.USE_SMFPLAYER:
                                    smfplayer.load(i+1, dirname, fname,
                                                    int( info.get('smfseq',defaultparams['smfseq']) ),
                                                    abs(float( info.get('gain', defaultparams['gain']) )),
                                                    info.get( 'voicemap',defaultparams['voicemap'] ).strip().title()
                                                    )
                                else:
                                    print("Skipped midifile %s as the SMFplayer is not activated" %(fname))
                                continue
                            midinote = int(info.get('midinote', defaultparams['midinote']))
                            notename = info.get('notename', defaultparams['notename']).rstrip()
                            rnds = int(info.get('rnds', defaultparams['rnds']))
                            mode = info.get('mode', defaultparams['mode']).strip().title().rstrip()
                            retrigger = info.get('retrigger', defaultparams['retrigger']).strip().title().rstrip()
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
                                    print("Backtrack %s ignored" %fname)
                                    continue
                            else:
                                voice=int(info.get('voice', defaultparams['voice']))
                            if voice == 0:          # the override / special effects voice cannot fill
                                fillnote = 'N' # so we ignore whatever the user wants (RTFM)
                            else:
                                fillnote = (info.get('fillnote', defaultparams['fillnote'])).title().rstrip()
                            voicex=gp.getindex(voice,gv.voicelist)
                            if voicex<0:
                                gv.voicelist.append([voice,"","","",PREVELOLEVS,PREFXPRESET,PRELAYERS])
                                voicex=len(gv.voicelist)-1
                            qnote = info.get('qnote', defaultparams['qnote']).title()[0][:1]
                            if qnote == 'Y': qnote = 'O'    # the default for qnotes is on odd midi notes (60=C).
                            fractions = PREFRACTIONS        # not yet implemented for user change (future??)
                            if qnote != 'N':
                                fractions=2             # for now always true
                            else:
                                fractions=1
                            gv.voicelist[voicex][3] = info.get('notemap', defaultparams['notemap']).strip().title().rstrip()   # pick the latest; we can't check everything, RTFM :-)
                            gv.voicelist[voicex][5] = info.get('fxpreset', defaultparams['fxpreset']).strip().title().rstrip()   # pick the latest; we can't check everything, RTFM :-)
                            gv.voicelist[voicex][6] = info.get('layers', defaultparams['layers']).strip().title().rstrip()   # pick the latest; we can't check everything, RTFM :-)
                            if notename:
                                midinote=gv.notename2midinote(notename,fractions)
                                if midinote < 0:
                                    print("%s: ignored notename in voice %d: '%s'" %(fname, voice, notename))
                                    continue
                            transpose = int(info.get('transpose', defaultparams['transpose']))
                            if voice != 0:          # the override / special effects voice cannot transpose
                                midinote-=transpose
                            if (midinote < 0 or midinote > 127):
                                if backtrack >0:    # Keep the backtrackknob when note is unplayable
                                    midinote=-1
                                else:
                                    print("%s: ignored notename / midinote in voice %d: '%s'/%d" %(fname, voice, notename, midinote))
                                    continue
                            if gv.POLY_AFTOUCH:
                                pafpair = (info.get('pafpair', defaultparams['pafpair'])).rstrip()
                                AfterTouch.fillpairs(voice,fractions,pafpair)
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
                            velmode = info.get('velmode', defaultparams['velmode']).title().rstrip()
                            if velmode not in [VELSAMPLE,VELACCURATE]:
                                print("%s: velmode %s, should be one of %s" %(fname, velmode, [VELSAMPLE,VELACCURATE]))
                                velmode=PREVELMODE
                            velolevs=1 if voice==0 else int(info.get('velolevs', defaultparams['velolevs']))
                            if velolevs in VELOSTEPS:
                                if velolevs!=127:
                                    if velolevs>gv.voicelist[voicex][4] or gv.voicelist[voicex][4]==127:
                                        gv.voicelist[voicex][4]=velolevs
                                    elif velolevs<gv.voicelist[voicex][4]:
                                        print("%s: velolevs %d smaller than earlier defined %d, ignored" %(fname,velolevs,gv.voicelist[voicex][4]))
                            else:
                                print("%s: velolevs %d, should be one of %s, set to %d" %(fname, velolevs, VELOSTEPS,gv.voicelist[voicex][4]))
                            velolevs=gv.voicelist[voicex][4]
                            velocity = int(info.get('velocity', defaultparams['velocity']))
                            if velocity==-1: velocity=velolevs
                            if velocity>velolevs:
                                print("%s: ignored sample as velocity %d higher than velolevs %d for voice %d" %(fname, velocity, velolevs, voice))
                                continue
                            mutegroup = int(info.get('mutegroup', defaultparams['mutegroup']))
                            gain = abs(float((info.get('gain', defaultparams['gain']))))
                            pan = int(info.get('pan', defaultparams['pan']))
                            if not (0 < pan < 128):
                                pan = 64
                                print("%s: ignored %pan=%d" %(fname, pan))
                            release = int(info.get('release', defaultparams['release']))
                            ##if (release>127): release=127
                            damp = int(info.get('damp', defaultparams['damp']))
                            ##if (damp>127): damp=127
                            dampnoise = True if info.get('dampnoise', defaultparams['dampnoise']).title()[0][:1]=="Y" else False
                            relsample = info.get('relsample', defaultparams['relsample']).title()[0][:1]
                            if relsample=="S" and voice<1:
                                relsample="N"   # Release samples are only possible for playable voices, but OK to define for release samples themselves
                                if voice==0:    # But the effects channel is special, so player needs to be notified
                                    print("%s: ignored release sample ('S') for voice 0 as effects channel doesn't support this" %fname)
                            xfadeout = int(info.get('xfadeout', defaultparams['xfadeout']))
                            ##if (xfadeout>127): xfadeout=127
                            xfadein = int(info.get('xfadein', defaultparams['xfadein']))
                            ##if (xfadein>127): xfadein=127
                            xfadevol = abs(float(info.get('xfadevol', defaultparams['xfadevol'])))
                            #
                            # Replace inconsistent/impossible combinations with something workable
                            #
                            if (mode == "Loo2"):
                                mode = "Loop";
                            elif (GetStopmode(mode)<-1) or (GetStopmode(mode)==127 and midinote>(127-gv.stop127)):
                                print("invalid mode '%s' or note %d out of range, set to keyboard mode." % (mode, midinote))
                                mode=PLAYLIVE
                            if ( mutegroup>0 and retrigger=="Y" and mode!=PLAYLIVE):
                                retrigger = 'N'
                                print ( "%s: Mutegroup and retrigger are mutually exclusive in special modes, set to retrigger=N" %fname )
                            try:
                                if backtrack>-1:    # Backtracks are intended for start/stop via controller, so we can use unplayable notes
                                    if (gv.BTNOTES+backtrack, velocity, voice) in gv.samples:
                                        gv.samples[gv.BTNOTES+backtrack, velocity, voice].append(Sound(os.path.join(dirname, fname), voice, gv.BTNOTES+backtrack, rnds, velocity, velmode, mode, release, damp, dampnoise, retrigger, gain, mutegroup, relsample, xfadeout, xfadein, xfadevol, fractions, pan))
                                    else:
                                        gv.samples[gv.BTNOTES+backtrack, velocity, voice] = [Sound(os.path.join(dirname, fname), voice, gv.BTNOTES+backtrack, rnds, velocity, velmode, mode, release, damp, dampnoise, retrigger, gain, mutegroup, relsample, xfadeout, xfadein, xfadevol, fractions, pan)]
                                if midinote>-1:
                                    if (midinote, velocity, voice) in gv.samples:
                                        gv.samples[midinote, velocity, voice].append(Sound(os.path.join(dirname, fname), voice, midinote, rnds, velocity, velmode, mode, release, damp, dampnoise, retrigger, gain, mutegroup, relsample, xfadeout, xfadein, xfadevol, fractions, pan))
                                    else:
                                        gv.samples[midinote, velocity, voice] = [Sound(os.path.join(dirname, fname), voice, midinote, rnds, velocity, velmode, mode, release, damp, dampnoise, retrigger, gain, mutegroup, relsample, xfadeout, xfadein, xfadevol, fractions, pan)]
                                        fillnotes[midinote, voice] = fillnote
                                        if gv.voicelist[voicex][2] == "":
                                            gv.voicelist[voicex][2] = mode
                                        elif gv.voicelist[voicex][2] != mode:
                                            gv.voicelist[voicex][2] = "Mixed"
                            except: pass    # Error should be handled & communicated in subprocs
                except:
                    m=i+1
                    print("Error in definition file, skipping line %d." % (m))
                    v=", " if gv.DefinitionErr != "" else ""
                    gv.DefinitionErr="%s%s%d" %(gv.DefinitionErr,v,m)
    else:
        for midinote in range(128):
            if LoadingInterrupt:
                gv.ActuallyLoading=False
                gv.midi_mute = midi_mute    # restore mute status
                return
            file = os.path.join(dirname, "%d.wav" % midinote)
            #print "Trying " + file
            if os.path.isfile(file):
                gv.samples[midinote,1,1] = [Sound(file, 1, midinote, 1, PREVELOLEVS, PREVELMODE, gv.sample_mode, PRERELEASE, PREDAMP, PREDAMPNOISE, PRERETRIGGER, gv.globalgain, PREMUTEGROUP, BOXRELSAMPLE, PREXFADEOUT, PREXFADEIN, PREXFADEVOL, PREFRACTIONS, 64)]
                fillnotes[midinote,1] = PREFILLNOTE
        voicenames=[[1,"Default"]]
        # 0=voice#, 1=descr, 2=mode, 3=notemap, 4=velocitylevels, 5=fxpreset, 6=layers
        gv.voicelist=[[1, '', 'Keyb', '', 1, '', [] ]]

    if gv.USE_SMFPLAYER:
        if len(gv.smfseqs)>0:
            smfplayer.drumlist()
    initial_keys = set(gv.samples.keys())
    if len(initial_keys) > 0:
        # We have found useful samples, so expanding to full instrument can be done
        gv.voicelist.sort(key=operator.itemgetter(0))
        #
        # Validate the separate release samples including dampnoise definitions and if ok, prepare fadeout
        for m in gv.samples:
            if gv.samples[m][0].relsample=="S" and gv.samples[m][0].voice>0:
                xd="&dampnoise" if gv.samples[m][0].dampnoise else ""
                voice=gp.getindex(-gv.samples[m][0].voice,gv.voicelist)
                if voice<0:
                    gv.samples[m][0].relsample="N"
                    print("Release%s of voice %d set to normal as voice %d was not found" %(xd,gv.samples[m][0].voice,-gv.samples[m][0].voice))
                elif fillnotes[gv.samples[m][0].midinote, gv.samples[m][0].voice] == 'N' and gv.samples[m][0].voice>0:
                    y=False
                    velolevs=gv.voicelist[gp.getindex(gv.samples[m][0].voice,gv.voicelist)][4]
                    for velocity in range(1,velolevs+1):
                        try:
                            x=gv.samples[gv.samples[m][0].midinote, velocity, -gv.samples[m][0].voice]
                            y=True
                            gv.samples[m][0].release=gv.samples[m][0].damp if gv.samples[m][0].dampnoise else gv.samples[m][0].xfadeout
                        except: pass
                        x=None
                    if not y:
                        gv.samples[m][0].relsample="N"
                        print("Release%s of %s set to normal as release sample was not found" %(xd,gv.samples[m][0].fname))
                else:
                    gv.samples[m][0].release=gv.samples[m][0].damp if gv.samples[m][0].dampnoise else gv.samples[m][0].xfadeout
        #
        # Complete all voices plus related notes
        for voicex in range(len(gv.voicelist)):
            voice=gv.voicelist[voicex][0]
            v=gp.getindex(voice, voicenames)
            if v<0: gv.voicelist[voicex][1]=str(voice)
            else:   gv.voicelist[voicex][1]=voicenames[v][1]
            if gv.currvoice==0 and voice>0:
                setVoice(voice,1)   # make sure to start with a playable non-empty voice
                ok=False            # also make sure to have a sound when switching to undefined (MT)voice
                for v in gv.voicemap:
                    if v[0]=="0" and v[1]==0:
                        ok=True
                if not ok:
                    gv.voicemap.insert(0, ["0", 0, 0, gv.currvoice] )
            #
            # ==> in next two fill routines sequences of random selection are not treated separately, this has pros and cons..
            #     you can avoid the cons by using balanced random samples = each wav has its counterpart in the other rnds's
            #
            # Fill missing velocity levels in found normal notes
            velolevs=gv.voicelist[voicex][4]
            for midinote in range(128):
                lastvelocity = None
                last=0
                for velocity in range(1,velolevs+1):
                    if (midinote, velocity, voice) in initial_keys:
                        if not lastvelocity:
                            for v in range(1,velocity):
                                gv.samples[midinote, v, voice] = gv.samples[midinote, velocity, voice]
                        last=velocity
                        lastvelocity = gv.samples[midinote, velocity, voice]
                    else:
                        if lastvelocity:
                            gv.samples[midinote, velocity, voice] = lastvelocity
            initial_keys = set(gv.samples.keys())  # we got more keys, but not enough yet
            lastlow = -130                      # force lowest unfilled notes to be filled with the nexthigh
            nexthigh = None                     # nexthigh not found yet, and start filling the missing notes
            #
            # Fill missing notes where notefilling is required
            for midinote in range(128-gv.stop127, gv.stop127):    # only fill the keyboard area.
                if (midinote, 1, voice) in initial_keys:
                    if fillnotes[midinote, voice] != 'N':   # can we use this note for filling?
                        nexthigh = None                     # passed nexthigh
                        lastlow = midinote                  # but we got fresh low info
                else:
                    if not nexthigh:
                        nexthigh=260    # force highest unfilled notes to be filled with the lastlow
                        for m in range(midinote+1, 128):
                            if (m, 1, voice) in initial_keys:
                                if fillnotes[m, voice] != 'N':  # can we use this note for filling?
                                    if m < nexthigh: nexthigh=m
                    if (nexthigh-lastlow) > 260:    # did we find a note valid for filling?
                        break                       # no, stop trying
                    m=lastlow if midinote <= 0.5+(nexthigh+lastlow)/2 else nexthigh
                    #print "Note %d will be generated from %d" % (midinote, m)
                    for velocity in range(1,velolevs+1):
                        gv.samples[midinote, velocity, voice] = gv.samples[m, velocity, voice]
                        if fillnotes[m, voice] == 'F':  # sample should be played without adjusting pitch,
                            gv.samples[midinote, velocity, voice].midinote=midinote     # so fool the audiomodule...
        #
        # Fill overrides in the voices prepare above
        if gp.getindex(0,gv.voicelist)>-1:             # do we have the override / special effects voice ?
            for midinote in range(128):
                if (midinote, 0) in fillnotes:
                    for voicex in range(len(gv.voicelist)):
                        voice=gv.voicelist[voicex][0]
                        if voice>0:
                            velolevs=gv.voicelist[voicex][4]
                            for velocity in range(1,velolevs+1):
                                gv.samples[midinote, velocity, voice] = gv.samples[midinote, 1, 0]
        #
        # Inventorize the found backtracks
        for track in range(128):
            if tracknames[track][0]:
                gv.btracklist.append([track, tracknames[track][1], tracknames[track][2]])
        if gv.currvoice!=0: gv.sample_mode=gv.voicelist[gp.getindex(gv.currvoice,gv.voicelist)][2]

        #
        # Indicate we're ready and give memory status
        gv.ActuallyLoading=False
        mem=psutil.virtual_memory()
        print("Loaded '%s', %d%% free memory left" %(gv.basename, 100-mem.percent))
        gv.display("","%04d" % gv.PRESET)

    else:
        gv.ActuallyLoading=False
        print('Preset empty: ' + str(gv.PRESET))
        gv.basename = "%d Empty preset" %gv.PRESET
        gv.display("","E%03d" % gv.PRESET)

    gv.midi_mute = midi_mute    # restore mute status

#########################################
##  LOAD FIRST SOUNDBANK
#########################################

LoadSamples()

#########################################
##      O P T I O N A L S
##  - BUTTONS via GPIO
##  - WebGUI thread
##  - MIDI IN via SERIAL PORT
#########################################

try:

    if gv.cp.getboolean(gv.cfg,"USE_BUTTONS".lower()):     # applies to hardware GPIO buttons, the button menu is always available for others
        import buttons  # actual availablity of the optional buttons is tested in the module
        if buttons.numbuttons: gv.GPIO=True    # found some :-)
        else: USE_BUTTONS=False

    if USE_HTTP_GUI:
        import http_gui

    serialout=False
    if gv.cp.getboolean(gv.cfg,"USE_SERIALPORT_MIDI".lower()):
        import serialMIDI
        midiserial = serialMIDI.IO(midicallback=MidiCallback,
                                realtime=gv.cp.getboolean(gv.cfg,"SERIALPORT_REALTIME".lower()),
                                sysex=gv.cp.getboolean(gv.cfg,"SERIALPORT_SYSEX".lower()),
                                timeout=gv.cp.getfloat(gv.cfg,"SERIALPORT_TIMEOUT".lower()))
        serialout = midiserial.out

except:
    print("Error loading optionals (either buttons, http-gui or serial-midi)")
    time.sleep(0.5)
    gp.GPIOcleanup()
    exit(1)

#########################################
##  MIDI DEVICES DETECTION
##  and MAIN LOOP
#########################################

x=gv.cp.get(gv.cfg,"MIDI_THRU".lower()).split(',')
thru_ports = []
embedded = "EMBEDDED"
for i in range(len(x)):
    v = x[i].lower().strip()
    if v:
        if ( v == "all" ):
            thru_ports.append("All")
        if re.search( v, "embedded" ):
            thru_ports.append(embedded)
        elif v!='' and v not in thru_ports:
            thru_ports.append(v)

gv.outports = {}
if (len(thru_ports) > 0):
    i=1
    allvalid = "All" in thru_ports

    if serialout:
        dev = ''
        if embedded in thru_ports:
            gv.outports[embedded] = [midiserial.uart, midiserial]
            dev = '" as %s' %embedded
        elif allvalid:
            gv.outports[midiserial.uart] = [midiserial.uart, midiserial]
            dev = '"'
        else:
            for v in thru_ports:
                if re.search ( v.lower(), midiserial.uart.lower()):
                    gv.outports[midiserial.uart] = [midiserial.uart, midiserial]
                    dev = '"'
                    break
        if dev:
            print ( 'Opened output "%s%s' %(midiserial.uart, dev) )

    for port in rtmidi2.get_out_ports():
        if ('Midi Through' not in port
	    and 'rtmidi' not in port.lower()):  # just a precaution
            valid = allvalid
            for v in thru_ports:
                if valid:
                    break
                valid = re.search( v.lower(), port.lower() )
                # Examples showing it's use:
                #  "MIDI_THRU = ^MIDI4x4.*3$" matches "MIDI4x4 28:3"
                #   which is helpful as device number (28 here) may vary
                #  For all MIDI4x4 output ports: "MIDI_THRU = ^MIDI4x4.*"
            if valid:
                outport = "MIDI_OUT_%d" %i
                gv.outports[outport] = [port, None]
                try:
                    gv.outports[outport][1] = rtmidi2.MidiOut()
                    gv.outports[outport][1].open_port(port)
                    print ( 'Opened output "%s"' % (port) )
                    i += 1
                except:
                    print ( 'No active device on "%s"' % (port) )
                    del gv.outports[outport]

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
        UI.mididevs = []
        i=1
        for port in curr_inports:
            if ('rtmidi' in port.lower()
            or 'smfplayer' in port.lower()
            or ('Midi Through' in port
                and not gv.USE_SMFPLAYER)
                ): continue
            v = '"%s"'%port if 'Midi Through' not in port else '"%s" as SMFplayer' %port
            midi_in.open_ports(port)
            print ( 'Opened input %s' %(v) )
            if 'Midi Through' not in port and 'SMFplayer' not in port:
                UI.mididevs.append(str(port))   # skip internal / automatically added devices
            i+=1
        curr_inports = rtmidi2.get_in_ports()   # we do this indirect to catch
        prev_inports = curr_inports             # auto opened virtual ports
    time.sleep(2)

except KeyboardInterrupt:
    print("\nstopped by user via ctrl-c\n")
    if USE_BUTTONS:
        buttons.stop
except:
    print("\nstopped by unexpected error")
finally:
    gv.display('Stopped')
    time.sleep(0.5)
    gp.GPIOcleanup()
    exit(0)
