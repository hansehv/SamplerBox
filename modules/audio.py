###############################################################
#   AUDIO stuff
#   CALLBACK routine
#   OPEN AUDIO DEVICE   org frames_per_buffer = 512
#   Setup the sound card's volume control (if possible)
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################

import time,numpy,re,sounddevice,configparser
import samplerbox_audio,gv,Cpp,arp,LFO

AUDIO_DEVICE_ID = gv.cp.getint(gv.cfg,"AUDIO_DEVICE_ID".lower())
AUDIO_DEVICE_NAME = gv.cp.get(gv.cfg,"AUDIO_DEVICE_NAME".lower())
mixer_control = gv.cp.get(gv.cfg,"MIXER_CONTROL".lower())
SAMPLERATE = gv.cp.getint(gv.cfg,"SAMPLERATE".lower())
USE_48kHz = gv.cp.getboolean(gv.cfg,"USE_48kHz".lower())
BLOCKSIZE = gv.cp.get(gv.cfg,"BLOCKSIZE".lower())
BLOCKSIZES=[]
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
SPEED = numpy.power(2, numpy.arange(-1.0*SPEEDRANGE*PITCHSTEPS,
                                    1.0*SPEEDRANGE*PITCHSTEPS)/(12*PITCHSTEPS)).astype(numpy.float32)
countdown=0
counting=1
sd=None

def AudioCallback(outdata, frame_count, time_info, status):
    global counting,countdown
    p=len(gv.playingsounds)-MAX_POLYPHONY
    if p>0:
        #print ( "MAX_POLYPHONY %d exceeded with %d notes" %(MAX_POLYPHONY,p) )
        for i in range(p+gv.playingbacktracks-1):
            if gv.playingsounds[i].playingstopmode()!=3:    # let the backtracks be
                del gv.playingsounds[i]     # get it out of the system
    # Handle arpeggiator before soundgen to reduce timing issues at chord/sequence changes
    if arp.active and not counting: arp.process()
    # audio-module:
    rmlist = []
    b = samplerbox_audio.mixaudiobuffers(rmlist, frame_count,
                                        FADEOUT, FADEOUTLENGTH,
                                        SPEED, SPEEDRANGE,
                                        gv.PITCHBEND+LFO.VIBRvalue+PITCHCORR,
                                        PITCHSTEPS)
    for e in rmlist:
        try:
            if e.sound.stopmode==3:     # keep track of backtrack status
                gv.playingnotes[e.note+(e.channel*gv.MTCHNOTES)]=[]
            gv.playingsounds.remove(e)
        except: pass
    # volume control and audio effects/filters
    if not counting: LFO.process[LFO.effect]()
    b *= ( 10**( LFO.TREMvalue*gv.volumeCC)-1 ) /9     # linear doesn't sound natural, this may be to complicated too though...
    Cpp.process(b, frame_count)
    outdata[:] = b.reshape(outdata.shape)
    # Use this module as timer for ledblinks
    if gv.LEDblink and not counting:
        gv.LEDsblink()
    if counting:
        counting-=1
    else:
        counting=countdown

def OpenDevice(f):
    global sd,countdown, BLOCKSIZE, BLOCKSIZES
    latency_org=0.03482993197278    # original samplerbox. As this is clock of the LFO, it poses extra requirements=restrictions.
    blocksize_org=384       # original samplerbox (source states 512 but that was corrected by sounddevice to default_high=384).
    blocksize_min=16        # just a value (org/24) as long as it's a divider of blocksize_org=max
    devprops=sounddevice.query_devices(AUDIO_DEVICE_ID)
    blocksize_low=int( blocksize_org * devprops["default_low_output_latency"] / latency_org)
    for i in range(1, 1 + int(blocksize_org/blocksize_min) ):
        if i*blocksize_min >= blocksize_low:
            blocksize_low = i * blocksize_min
            break
    blocksize_high=int(blocksize_org * devprops["default_high_output_latency"] / latency_org)
    if blocksize_high>blocksize_org:
        blocksize_high=blocksize_org
    freqcorr = float( f / 44100 )
    blocksize_high = blocksize_high * freqcorr
    blocksize_low = blocksize_low * freqcorr
    for i in range( int(blocksize_high / blocksize_low) ):
        BLOCKSIZES.append( int( blocksize_low *(i+1) ) )
    blocksize_low=BLOCKSIZES[0]     # don't confuse the user with rounding/float issues,
    blocksize_high=BLOCKSIZES[i]    # as the buffers will be filled anyway..
    try:
        x=int(BLOCKSIZE)
        if x<blocksize_low: BLOCKSIZE=blocksize_low     # makes sure request is within boundaries
        elif x>blocksize_high: BLOCKSIZE=blocksize_high
        else:                                           # as well as having an aligned value
            for i in BLOCKSIZES:
                if i>=x:
                    BLOCKSIZE=i
                    break
    except:
        BLOCKSIZE=BLOCKSIZE.lower()
        if BLOCKSIZE=="low": BLOCKSIZE=blocksize_low
        else: BLOCKSIZE=blocksize_high      # high is safe for sound generation, though it may suffer from latency...
    countdown=blocksize_high/BLOCKSIZE-1
    sd = sounddevice.OutputStream(device=AUDIO_DEVICE_ID, blocksize=BLOCKSIZE,
                                    samplerate=f, channels=2,
                                    dtype='int16', callback=AudioCallback)
    sd.start()
    print ( 'Opened audio device #%i %s\n  samplerate %iHz, blocksize=%d, LFOcycle=%d\n  valid blocksizes: %s' %(AUDIO_DEVICE_ID,AUDIO_DEVICE_NAME,f,BLOCKSIZE,countdown+1,BLOCKSIZES) )
    Cpp.c_filters.setSampleRate(f)   # align the filters

"""
	I N I T     L O G I C
"""
try:
    f=SAMPLERATE
    if USE_48kHz:
        if PITCHBITS < 7:
            print ( "==> Can't tune to 48kHz, please set PITCHBITS to 7 or higher <==" )
        else:
            PITCHCORR = -147 *( 2**(PITCHBITS-7) )
        f=48000
    i=0
    device_found=False
    for d in sounddevice.query_devices():
        if (AUDIO_DEVICE_NAME in d['name'] or AUDIO_DEVICE_ID==i):  # does the device match the config requested one?
            AUDIO_DEVICE_ID=i
            AUDIO_DEVICE_NAME=d['name']
            if d['max_output_channels']==0 or re.search('\(hw:(.*),', AUDIO_DEVICE_NAME)!=None:
                try:
                    OpenDevice(f)
                    device_found = True         # found device requested by configuration.txt can be started
                except: pass
            if not device_found:
                print ( 'Ignored requested audio device #%i %s' %(AUDIO_DEVICE_ID,AUDIO_DEVICE_NAME) )
            break
        i+=1
    if not device_found:
        if not(AUDIO_DEVICE_ID<0 and AUDIO_DEVICE_NAME.title()=="Detect"):
            print ( 'Audio device #%i "%s" not found or invalid' %(AUDIO_DEVICE_ID,AUDIO_DEVICE_NAME) )
        print ( "Available audio devices:" )
        print ( sounddevice.query_devices() )
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
        if 'bcm2835' in AUDIO_DEVICE_NAME: BLOCKSIZE="high"   # force the PI sound device to sound OK
        OpenDevice(f)
except:
    gv.display("Invalid audiodev")
    print ( 'Invalid audio device #%i %s' %(AUDIO_DEVICE_ID,AUDIO_DEVICE_NAME) )
    try:
        print ( 'Available audio devices' )
        print(sounddevice.query_devices())
    except:
        print ( '** sounddevice returns error! **' )
    time.sleep(0.5)
    gv.GPIOcleanup()
    exit(1)

device_found=False
if mixer_control.title()!="None":
    import alsaaudio
    try:
        mixer_card_index = re.search('\(hw:(.*),', AUDIO_DEVICE_NAME) # get x from (hw:x,y) in device name
        mixer_card_index = int(mixer_card_index.group(1))
    except: mixer_card_index =  AUDIO_DEVICE_ID
    mixer_controls = alsaaudio.mixers(mixer_card_index)
    #print ( "Available mixer controls: %s" %mixer_controls )
    mixer_controls.insert(0,mixer_control)
    for mixer_control in mixer_controls:
        try:
            amix = alsaaudio.Mixer(cardindex=mixer_card_index,control=mixer_control)
            if "Playback Volume" in amix.volumecap():   # it can set some form of playback volume
                amix.setvolume(50)
                if int(amix.getvolume()[0]) == 50:      # can it set the right volume ?
                    device_found=True                   # indicate OK
                    print ('Opened Alsamixer: card (hw:%i,x), control %s' % (mixer_card_index,mixer_control) )
                    break
                else:
                    amix=None
        except:
            pass
if device_found:
    USE_ALSA_MIXER=True
    import math
    def getvolume():
        vol = int(round(amix.getvolume()[0]))
        gv.volume = 10**(0.02*vol)
    def setvolume(volume):
        if volume==0: volume=1
        amix.setvolume( int( math.log(volume,10) *50 ))
        getvolume()
    setvolume(gv.cp.getint(gv.cfg,"volume".lower()))
    gv.getvolume=getvolume
    gv.setvolume=setvolume
else:
    print ( 'Alsamixer not setup, so no hardware volume control' )
    USE_ALSA_MIXER=False
    gv.getvolume=gp.NoProc
    gv.setvolume=gp.NoProc
