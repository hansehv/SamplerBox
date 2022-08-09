###############################################################
# Source sounds handling
#  - read the wav's
#  - build the sound tables
#  - coordinate the sounds realtime use
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################

import wave, struct, numpy
from chunk import Chunk		# deprecated from 7.11: replaced by _Chunk class in wave
import samplerbox_audio, gv, arp

#########################################
##  Playmode identifiers
#########################################

def GetStopmode(mode):
    stopmode = -2
    if mode==gv.PLAYLIVE:
        stopmode = 128			# stop on note-off = release key
    elif mode==gv.PLAYBACK:
        stopmode = -1			# don't stop, play sample at full length (unless restarted)
    elif mode==gv.PLAYLOOP:
        stopmode = 127			# stop on 127-key
    elif mode==gv.PLAYBACK2X or mode==gv.PLAYLOOP2X:
        stopmode = 2			# stop on 2nd keypress
    elif mode==gv.BACKTRACK:
        stopmode = 3			# finish looping+outtro on 2nd keypress or defined midi controller
    return stopmode
def GetLoopmode(mode):
    if mode==gv.PLAYBACK or mode==gv.PLAYBACK2X:
        loopmode = -1
    else:
        loopmode = 1
    return loopmode

############################################################
##  SLIGHT MODIFICATION OF PYTHON'S WAVE MODULE,
##  to read cue & loop markers if applicable in mode
############################################################

class waveread(wave.Wave_read):
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

############################################################
##  Actual playing sounds
############################################################

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

############################################################
##  Loading sounds and initiate playing "play"
############################################################

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
        self.velsample = True if velmode==gv.VELSAMPLE else False
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
