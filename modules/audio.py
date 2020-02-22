###############################################################
#   AUDIO stuff
#   CALLBACK routine
#   OPEN AUDIO DEVICE   org frames_per_buffer = 512
#   Setup the sound card's volume control (if possible)
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################

import time,numpy,re,sounddevice,ConfigParser,ctypes
import samplerbox_audio,gv,Cpp,arp,LFO
c_float_p = ctypes.POINTER(ctypes.c_float)

AUDIO_DEVICE_ID = gv.cp.getint(gv.cfg,"AUDIO_DEVICE_ID".lower())
AUDIO_DEVICE_NAME = gv.cp.get(gv.cfg,"AUDIO_DEVICE_NAME".lower())
mixer_control = gv.cp.get(gv.cfg,"MIXER_CONTROL".lower())
USE_48kHz = gv.cp.getboolean(gv.cfg,"USE_48kHz".lower())
MAX_POLYPHONY = gv.cp.getint(gv.cfg,"MAX_POLYPHONY".lower())
gv.PITCHRANGE = gv.cp.getint(gv.cfg,"PITCHRANGE".lower())*2     # actually it is 12 up and 12 down
PITCHBITS = gv.cp.getint(gv.cfg,"PITCHBITS".lower())

gv.pitchnotes = gv.PITCHRANGE
PITCHSTEPS = 2**PITCHBITS
gv.pitchneutral = PITCHSTEPS/2
gv.pitchdiv = 2**(14-PITCHBITS)
PITCHCORR = 0       # This is the 44100 to 48000 correction / hack
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
        for i in xrange(p+gv.playingbacktracks-1):
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
                gv.playingnotes[e.note+(e.channel*MTCHNOTES)]=[]
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
    if gv.LEDblink: gv.LEDsblink()

try:
    f=44100
    if USE_48kHz:
        if PITCHBITS < 7:
            print "==> Can't tune to 48kHz, please set PITCHBITS to 7 or higher <=="
        else:
            PITCHCORR = -147*(2**(PITCHBITS-7))
        f=48000
    i=0
    device_found=False
    for d in sounddevice.query_devices():
        if (AUDIO_DEVICE_NAME in d['name'] or AUDIO_DEVICE_ID==i):  # does the device match the config requested one?
            AUDIO_DEVICE_ID=i
            AUDIO_DEVICE_NAME=d['name']
            if d['max_output_channels']==0 or re.search('\(hw:(.*),', AUDIO_DEVICE_NAME)!=None:
                try:
                    sd = sounddevice.OutputStream(device=AUDIO_DEVICE_ID, blocksize=512,samplerate=f,channels=2,dtype='int16',callback=AudioCallback)
                    sd.start()
                    device_found = True         # found device requested by configuration.txt
                except: pass
            if not device_found:
                print 'Ignored requested audio device #%i %s' %(AUDIO_DEVICE_ID,AUDIO_DEVICE_NAME)
            break
        i+=1
    if not device_found:
        i=0
        for d in sounddevice.query_devices():
            if d['max_output_channels'] > 0:
                if 'bcm2835' in d['name']:
                    if not device_found:    # keep the first PI sound device as a bypass
                        device_found = True
                        AUDIO_DEVICE_ID = i
                        AUDIO_DEVICE_NAME=d['name']
                elif 'default' not in d['name'] and 'dmix' not in d['name']:
                    AUDIO_DEVICE_ID = i
                    AUDIO_DEVICE_NAME=d['name']
                    break                   # found a valid non-builtin device
            i+=1
        sd = sounddevice.OutputStream(device=AUDIO_DEVICE_ID, blocksize=512,samplerate=f,channels=2,dtype='int16',callback=AudioCallback)
        sd.start()
    print 'Opened audio device #%i %s on %iHz' %(AUDIO_DEVICE_ID,AUDIO_DEVICE_NAME,f)
    Cpp.c_filters.setSampleRate(f)   # align the filters
except:
    gv.display("Invalid audiodev")
    print 'Invalid audio device #%i %s' %(AUDIO_DEVICE_ID,AUDIO_DEVICE_NAME)
    try:
        print 'Available audio devices'
        print(sounddevice.query_devices())
    except:
        print '** sounddevice returns error! **'
    time.sleep(0.5)
    gv.GPIOcleanup()
    exit(1)

device_found=False
if mixer_control.title()!="None":
    import alsaaudio
    mixer_card_index = re.search('\(hw:(.*),', AUDIO_DEVICE_NAME) # get x from (hw:x,y) in device name
    mixer_card_index = int(mixer_card_index.group(1))
    mixer_controls=alsaaudio.mixers(mixer_card_index)
    mixer_controls.insert(0,mixer_control)
    for mixer_control in mixer_controls:
        try:
            amix = alsaaudio.Mixer(cardindex=mixer_card_index,control=mixer_control)
            if "Playback Volume" in amix.volumecap():   # it can set some form of playback volume
                amix.setvolume(50)
                if int(amix.getvolume()[0])==50:        # can it set the right volume ?
                    device_found=True                   # indicate OK
                    print 'Opened Alsamixer: card (hw:%i,x), control %s' % (mixer_card_index,mixer_control)
                    break
                else:
                    amix=None
        except:
            pass
if device_found:
    gv.USE_ALSA_MIXER=True
    import math
    def getvolume():
        vol = int(amix.getvolume()[0])
        gv.volume = 10**(0.02*vol)
    def setvolume(volume):
        amix.setvolume(int(math.log(volume,10)*50))
        getvolume()
    setvolume(gv.cp.getint(gv.cfg,"volume".lower()))
    gv.getvolume=getvolume
    gv.setvolume=setvolume
else:
    gv.USE_ALSA_MIXER=False
    print 'Alsamixer not setup, so no hardware volume control'
    gv.getvolume=gv.NoProc
    gv.setvolume=gv.NoProc
