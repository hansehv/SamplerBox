#!python
#cython: language_level=3
#
#  SamplerBox 
#
#  author:    Joseph Ernest (twitter: @JosephErnest, mail: contact@samplerbox.org)
#  url:       http://www.samplerbox.org/
#  license:   Creative Commons ShareAlike 3.0 (http://creativecommons.org/licenses/by-sa/3.0/)
#
#  samplerbox_audio.pyx: Audio engine (Cython) 
#
#  Original version adapted extended by HansEhv (https://github.com/hansehv):
#
#  June 18 2016:
#      - implemented velocity fix by Erik Nieuwlands (http://www.nickyspride.nl/sb2/) of april 30.
#  October 28 2016:
#      - implemented pitch-bend and related to that:
#      - changed note filling from 0-7 octaves to -4 - +4 octaves (keep in line py-script!)
#        So you can get full 88 keyboard by supplying only a middle note (not recommended though)
#        If limits are exceeded, the highest/lowest possible note will be returned instead of requested one.
#  December 2016
#      - implemented variable release
#  July 2017
#      - implemented release sample via marker in wav ("GrandOrgue method")
#  March 2018
#      - implemented gain /sample
#  July 2018
#      - implemented vibrato (varying pitch)
#  October 2018
#      - Excluded effects track (voice 0) from pitchbend/vibrato
#  December 2018
#      - Included possibility to "retune" per note
#      - Included note filling in fractions: 1=semitones, 2=half-of-that= q-notes in equal intervals
#  January 2019
#      - implemented damp (= short release)
#  April 2019
#      - moved global variables from call to import gv
#      - implemented panning
#  July 2019
#      - removed the %retune value
#  December 2019
#      - Excluded sequencer channels from pitchbend/vibrato/panning
#  December 2021
#      - Adapted quarternote calculation after python2.7 -> python3 conversion
#        Intermediate rounding of formulas with mixed int/float variables changed
#
#  Rebuild with "python setup.py build_ext --inplace"



import cython
import numpy
cimport numpy
import sys
sys.path.append('./modules')
import gv

#def mixaudiobuffers(list playingsounds, list rmlist, int frame_count, numpy.ndarray FADEOUT, int FADEOUTLENGTH, numpy.ndarray SPEED, int SPEEDRANGE, int PITCHBEND, int PITCHSTEPS, float PANvalue):
def mixaudiobuffers(list rmlist, int frame_count, numpy.ndarray FADEOUT, int FADEOUTLENGTH, numpy.ndarray SPEED, int SPEEDRANGE, int PITCHBEND, int PITCHSTEPS):

    cdef int i, ii, k, l, N, length, looppos, fadeoutpos
    cdef float speed, newsz, pos, j
    cdef numpy.ndarray b = numpy.zeros(2 * frame_count, numpy.float32)      # output buffer
    cdef float* bb = <float *> (b.data)                                     # and its pointer
    cdef numpy.ndarray z
    cdef float vel, pitchbend, lpan, rpan
    cdef short* zz
    cdef float* fadeout = <float *> (FADEOUT.data)

    for snd in gv.playingsounds:
        pos = snd.pos               # some translations to direct variables for speed
        fadeoutpos = snd.fadeoutpos
        looppos = snd.loop          # can be changed to -1 for release marker processing
        length = snd.end            # can be end-loop or eof, depending normal or release marker process
        vel = snd.sound.gain * snd.vel / 127.0
        fractions=snd.sound.fractions

        # Below overflow protection values correspond with tables in samplerbox.py
        # The way of coding is longer than necessary, but faster. Optimizing leads to crippled sounds
        if snd.channel>0:           # Exclude sequencer from pitchbend and panning
            i = (SPEEDRANGE+snd.note-snd.sound.midinote) * PITCHSTEPS + snd.retune
            if i < 0:                                # below zero is out of limits
                i = 0                                # save the program by ruining the pitch :-(
            else:
                speedrange=2*SPEEDRANGE              # save a multiply and indirect addressing
                if i >= speedrange*PITCHSTEPS:       # 2*48=96 and higher is out of limits
                    i = (speedrange-1) * PITCHSTEPS  # save the program by ruining the pitch :-(
            speed = SPEED[i]
            lpan = 1.0
            rpan = 1.0
        elif snd.sound.voice==0:    # Exclude FXtrack from notefill, pitchbend and panning
            speed = SPEED[SPEEDRANGE*PITCHSTEPS]
            lpan = 1.0
            rpan = 1.0
        else:
            i = (SPEEDRANGE+(snd.note-snd.sound.midinote)/fractions) * PITCHSTEPS + snd.retune + PITCHBEND
            if i < 0:                                # below zero is out of limits
                i = 0                                # save the program by ruining the pitch :-(
            else:
                speedrange=2*SPEEDRANGE              # save a multiply and indirect addressing
                if i >= speedrange*PITCHSTEPS:       # 2*48=96 and higher is out of limits
                    i = (speedrange-1) * PITCHSTEPS  # save the program by ruining the pitch :-(
            speed = SPEED[i]
            if gv.PANvalue > 0:
                lpan = 1.0-gv.PANvalue
                rpan = 1.0+gv.PANvalue/10
            else:
                lpan = 1.0-gv.PANvalue/10
                rpan = 1.0+gv.PANvalue
        newsz = frame_count * speed
        z = snd.sound.data
        zz = <short *> (z.data)

        N = frame_count

        if (pos + frame_count * speed > length - 4) and (looppos == -1):
            rmlist.append(snd)          # if we're not looping: restrict the time to end-of-wav and stop the sound
            N = <int> ((length - 4 - pos) / speed)

        if snd.isfadeout:     # this way of coding is longer, but faster. Optimizing leads to cripled fadeout
            if snd.isfadein:
                release = snd.sound.damp        # both true indicates = damp
            else:
                release = snd.sound.release     # this also covers the cross fadeout where applicable
            if release == 0:
                relstep = FADEOUTLENGTH
            else:
                relstep = <int> (((FADEOUTLENGTH+release*500)/(release*1000)))  # rounding without math
            if fadeoutpos > FADEOUTLENGTH: 
                rmlist.append(snd)   
            ii = 0   
            for i in range(N):
                if fadeoutpos > FADEOUTLENGTH:   # fadeout exhausted ?
                    fadevol = 0                  # yes: be quiet
                else:
                    fadevol = fadeout[fadeoutpos]
                    fadeoutpos += relstep
                j = pos + ii * speed
                ii += 1                  
                k = <int> j
                if k > length - 2:
                    pos = looppos + 1
                    snd.pos = pos
                    ii = 0
                    j = pos + ii * speed   
                    k = <int> j       
                bb[2 * i] += (zz[2 * k] + (j - k) * (zz[2 * k + 2] - zz[2 * k])) * vel * lpan * fadevol   # linear interpolation
                bb[2 * i + 1] += (zz[2 * k + 1] + (j - k) * (zz[2 * k + 3] - zz[2 * k + 1])) * vel * rpan *fadevol
            snd.fadeoutpos = fadeoutpos

        else:
            if snd.isfadein:
                release = snd.sound.xfadein   # we'll treat the crossfade-fade-in as an inverted release
                if release == 0:
                    relstep = FADEOUTLENGTH
                else:
                    relstep = <int> (((FADEOUTLENGTH+release*500)/(release*1000)))  # rounding without math
                if fadeoutpos == 0:
                    fadeoutpos = FADEOUTLENGTH
                ii = 0   
                for i in range(N):
                    if fadeoutpos <= 0:    # fadein exhausted ?
                        fadevol = 1        # yes: play normal
                    else:
                        fadevol = fadeout[fadeoutpos]
                        fadeoutpos -= relstep
                    j = pos + ii * speed
                    ii += 1                  
                    k = <int> j
                    if k > length - 2:
                        k = length - 2
                        ii -= 2
                        j = pos + ii * speed   
                        k = <int> j       
                    bb[2 * i] += (zz[2 * k] + (j - k) * (zz[2 * k + 2] - zz[2 * k])) * vel * lpan * fadevol   # linear interpolation
                    bb[2 * i + 1] += (zz[2 * k + 1] + (j - k) * (zz[2 * k + 3] - zz[2 * k + 1])) * vel * rpan *fadevol
                if fadeoutpos <= 0:
                    fadeoutpos = 0
                    snd.isfadein = False
                snd.fadeoutpos = fadeoutpos

            else:
                ii = 0   
                for i in range(N):
                    j = pos + ii * speed
                    ii += 1                  
                    k = <int> j
                    if k > length - 2:
                        pos = looppos + 1
                        snd.pos = pos
                        ii = 0
                        j = pos + ii * speed   
                        k = <int> j       
                    bb[2 * i] += (zz[2 * k] + (j - k) * (zz[2 * k + 2] - zz[2 * k])) * vel * lpan   # linear interpolation
                    bb[2 * i + 1] += (zz[2 * k + 1] + (j - k) * (zz[2 * k + 3] - zz[2 * k + 1])) * rpan * vel

        snd.pos += ii * speed

    return b

def binary24_to_int16(char *data, int length):
    cdef int i
    res = numpy.zeros(length, numpy.int16)
    b = <char *>((<numpy.ndarray>res).data)
    for i in range(length):
        b[2*i] = data[3*i+1]
        b[2*i+1] = data[3*i+2]
    return res
