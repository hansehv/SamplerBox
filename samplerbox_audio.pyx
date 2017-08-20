#
#  SamplerBox 
#
#  author:    Joseph Ernest (twitter: @JosephErnest, mail: contact@samplerbox.org)
#  url:       http://www.samplerbox.org/
#  license:   Creative Commons ShareAlike 3.0 (http://creativecommons.org/licenses/by-sa/3.0/)
#
#  samplerbox_audio.pyx: Audio engine (Cython) 
#
#  Original version adapted extended by https://www.facebook.com/hanshom
#                          see docs at  http://homspace.xs4all.nl/homspace/samplerbox
#  June 18 2016:
#      - implemented velocity fix by Erik Nieuwlands (http://www.nickyspride.nl/sb2/) of april 30.
#  October 28 2016:
#      - implemented pitch-bend and related to that:
#      - changed note filling from 0-7 octaves to -4 - +4 octaves (keep in line py-script!)
#        So you can get full 88 keyboard by supplying only a middle note (not recommended though)
#        If limits are exceeded, the highest/lowest possible note will be returned instead of requested one.
#  December 2016
#      - implemented variable release
#
#  Rebuild with "python setup.py build_ext --inplace"



import cython
import numpy
cimport numpy

def mixaudiobuffers(list playingsounds, list rmlist, int frame_count, numpy.ndarray FADEOUT, int FADEOUTLENGTH, int PRERELEASE, numpy.ndarray SPEED, int SPEEDRANGE, int PITCHBEND, int PITCHSTEPS):

    cdef int i, ii, k, l, N, length, looppos, fadeoutpos
    cdef float speed, newsz, pos, j
    cdef numpy.ndarray b = numpy.zeros(2 * frame_count, numpy.float32)      # output buffer
    cdef float* bb = <float *> (b.data)                                     # and its pointer
    cdef numpy.ndarray z
    cdef float vel, pitchbend
    cdef short* zz
    cdef float* fadeout = <float *> (FADEOUT.data)

    for snd in playingsounds:
        pos = snd.pos               # some translations to direct variables for speed
        fadeoutpos = snd.fadeoutpos
        looppos = snd.sound.loop
        length = snd.sound.nframes
        vel = snd.vel / 127.0
        release = snd.sound.release
        if release > 127:
            release = PRERELEASE
        if release == 0:
            relstep = FADEOUTLENGTH
        else:
            relstep = <int> (((FADEOUTLENGTH+release*500)/(release*1000)))  # rounding without math

            # Below overflow protection values correspond with hard-coded values in samplerbox.py
        i = (SPEEDRANGE+snd.note-snd.sound.midinote) * PITCHSTEPS + PITCHBEND
        if i < 0:                                # below zero is out of limits
            i = 0                                # save the program by ruining the pitch :-(
        else:
            speedrange=2*SPEEDRANGE              # save a multiply and indirect addressing
            if i >= speedrange*PITCHSTEPS:       # 2*48=96 and higher is out of limits
                i = (speedrange-1) * PITCHSTEPS  # save the program by ruining the pitch :-(
        speed = SPEED[i]
        newsz = frame_count * speed
        z = snd.sound.data
        zz = <short *> (z.data)

        N = frame_count

        if (pos + frame_count * speed > length - 4) and (looppos == -1):
            rmlist.append(snd)          # if we're not looping: restrict the time to end-of-wav and stop the sound
            N = <int> ((length - 4 - pos) / speed)

        if snd.isfadeout:     # this way of coding is longer, but faster. Optimizing leads to cripled fadeout
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
                bb[2 * i] += (zz[2 * k] + (j - k) * (zz[2 * k + 2] - zz[2 * k])) * vel * fadevol   # linear interpolation
                bb[2 * i + 1] += (zz[2 * k + 1] + (j - k) * (zz[2 * k + 3] - zz[2 * k + 1])) * vel *fadevol
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
                bb[2 * i] += (zz[2 * k] + (j - k) * (zz[2 * k + 2] - zz[2 * k])) * vel   # linear interpolation
                bb[2 * i + 1] += (zz[2 * k + 1] + (j - k) * (zz[2 * k + 3] - zz[2 * k + 1])) * vel

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
