#
#  SamplerBox 
#
#  author:    Joseph Ernest (twitter: @JosephErnest, mail: contact@samplerbox.org)
#  url:       http://www.samplerbox.org/
#  license:   Creative Commons ShareAlike 3.0 (http://creativecommons.org/licenses/by-sa/3.0/)
#
#  samplerbox_audio.pyx: Audio engine (Cython) 
#
#  Originel version adapted extended by https://www.facebook.com/hanshom
#                          see docs at  http://homspace.xs4all.nl/homspace/samplerbox
#  June 18 2016:
#      - implemented velocity fix by Erik Nieuwlands (http://www.nickyspride.nl/sb2/) of april 30.
#  October 28 2016:
#      - implemented pitch-bend and related to that:
#      - changed note filling from 0-7 octaves to -4 - +4 octaves (keep in line py-script!)
#        So you can get full 88 keyboard by supplying only a middle note (not recommended though)
#        If limits are exceeded, the highest/lowest possible note will be returned instead of requested one.
#
#  Rebuild with "python setup.py build_ext --inplace"



import cython
import numpy
cimport numpy

def mixaudiobuffers(list playingsounds, list rmlist, int frame_count, numpy.ndarray FADEOUT, int FADEOUTLENGTH, numpy.ndarray SPEED, int PITCHBEND, int PITCHSTEPS):
    cdef int i, ii, k, l, N, length, looppos, fadeoutpos
    cdef float speed, newsz, pos, j
    cdef numpy.ndarray b = numpy.zeros(2 * frame_count, numpy.float32)      # output buffer
    cdef float* bb = <float *> (b.data)                                     # and its pointer
    cdef numpy.ndarray z
    cdef float vel, pitchbend
    cdef short* zz
    cdef float* fadeout = <float *> (FADEOUT.data)

    for snd in playingsounds:
        pos = snd.pos
        fadeoutpos = snd.fadeoutpos
        looppos = snd.sound.loop
        length = snd.sound.nframes
        vel = snd.vel / 127.0
        i = (48+snd.note-snd.sound.midinote) * PITCHSTEPS + PITCHBEND
        if i < 0:                       # below zero is out of limits
            i = 0                       # save the program by ruining the pitch :-(
        else:                           #
            if i > 95 * PITCHSTEPS:     # 2*48=96 and higher is out of limits
                i = 95 * PITCHSTEPS     # save the program by ruining the pitch :-(
        speed = SPEED[i]
        newsz = frame_count * speed
        z = snd.sound.data
        zz = <short *> (z.data)

        N = frame_count

        if (pos + frame_count * speed > length - 4) and (looppos == -1):
            rmlist.append(snd)
            N = <int> ((length - 4 - pos) / speed)

        if snd.isfadeout:
            if fadeoutpos > FADEOUTLENGTH: 
                rmlist.append(snd)   
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
                bb[2 * i] += (zz[2 * k] + (j - k) * (zz[2 * k + 2] - zz[2 * k])) * fadeout[fadeoutpos + i] * vel                  # linear interpolation
                bb[2 * i + 1] += (zz[2 * k + 1] + (j - k) * (zz[2 * k + 3] - zz[2 * k + 1])) *fadeout[fadeoutpos + i] * vel        
            snd.fadeoutpos += i

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
                bb[2 * i] += (zz[2 * k] + (j - k) * (zz[2 * k + 2] - zz[2 * k])) * vel                                               # linear interpolation
                bb[2 * i + 1] += (zz[2 * k + 1] + (j - k) * (zz[2 * k + 3] - zz[2 * k + 1])) *vel 

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
