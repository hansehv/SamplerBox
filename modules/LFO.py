##################################################################################
# Simple LFO routine used for
#    - vibrato (pitch modulation)
#    - tremolo (volume modulation)
#    - rotate (poor man's single speaker leslie)
# Being input based, these effects are cheap: less than 1% CPU on PI3
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
##################################################################################

#       Poor man's Low Frequency Oscillator (LFO)
# Clock can be via call in AudioCallback, on PI3 approx once per 11msec's
# for a saw=(128 up) or triangle=(128 up+down) a stepsize of 14 gives ~10Hz/5Hz respectively

LFOblock=0          # index values for readability
LFOsaw=1
LFOinvsaw=2
LFOtriangle=3

class plfo:
    def __init__(self, step=14, block=127, saw=127):
        self.step=step; 
        self.values=[0.0,0.0,0.0,0.0]
        if block<64:self.values[LFOblock]=-1
        else: self.values[LFOblock]=1
        self.values[LFOsaw]=saw
        self.values[LFOinvsaw]=127-self.values[LFOsaw]
        if self.values[LFOblock]>1: LFOself.values[LFOtriangle]=self.values[LFOsaw]
        else: self.values[LFOtriangle]=127-self.values[LFOsaw]
    def process(self):
        self.values[LFOsaw]+=self.step
        if self.values[LFOsaw]<-1: self.values[LFOsaw]=128 # stop infinite loop due to impossible values
        if self.values[LFOsaw]>127:
            self.values[LFOblock]*=-1
            self.values[LFOsaw]=0
        self.values[LFOinvsaw]=127-self.values[LFOsaw]
        if self.values[LFOblock]>0:
            self.values[LFOtriangle]=self.values[LFOsaw]
        else:
            self.values[LFOtriangle]=self.values[LFOinvsaw]
    def setstep(self,x):
        if x>0: self.step=x
    def setblock(self,x):
        if x<64: self.values[LFOblock]=-1
        else: self.values[LFOblock]=1
    def setsaw(self,x):
        self.values[LFOsaw]=x
    def setinvsaw(self,x):
        self.values[LFOsaw]=(127-x)
    def settriangle(self,x):     # -127 to 127, values below 0 mean the second=decreasing stage
        if x<0:
            self.values[LFOblock]=-1
            self.values[LFOsaw]=(127+x)
        else:
            self.values[LFOblock]=1
            self.values[LFOsaw]=x
    def getblock(self):
        return (self.values[LFOblock]+1)*64     # so return 0 or 127
    def getsaw(self):
        return self.values[LFOsaw]
    def getinvsaw(self):
        return self.values[LFOinvsaw]
    def gettriangle(self):
        return self.values[LFOtriangle]

#
#  Effects based on above
#
import gv

VibrLFO=plfo()
VIBRvalue=0         # Value 0 gives original note
VIBRpitch=0         # declare
VIBRspeed=0         # declare
VIBRtrill=False     # declare
def VibrProc(*z):
    global VIBRvalue,VIBRpitch,VIBRtrill
    VibrLFO.process()
    if VIBRtrill:
        VIBRvalue=(( (128*(VibrLFO.getblock())) /gv.pitchdiv)-gv.pitchneutral)*VIBRpitch
    else:
        VIBRvalue=(( (128*(VibrLFO.gettriangle())) /gv.pitchdiv)-gv.pitchneutral)*VIBRpitch
def VibrTidy(TurnOn):
    global VIBRvalue,VIBRspeed
    if TurnOn:
        VibrLFO.settriangle(63)     # start about neutral, going up
        VibrLFO.setstep(VIBRspeed)  # and with correct speed
    else:
        VIBRvalue=0              # tune the note
def VibrSetpitch(CCval,*z):
    global VIBRpitch
    VIBRpitch=1.0*CCval/32   # steps of 1/32th, range like GUI
def VibrSetspeed(CCval,*z):
    global VIBRspeed
    VIBRspeed=1.0*CCval/4    # range=32
    VibrLFO.setstep(VIBRspeed)
def VibrToggletrill(CCval,*z):
    global VIBRtrill
    VIBRtrill=not(VIBRtrill)
gv.setMC(gv.VIBRDEPTH,VibrSetpitch)
gv.setMC(gv.VIBRSPEED,VibrSetspeed)
gv.setMC(gv.VIBRTRILL,VibrToggletrill)
#gv.VibrSetspeed=VibrSetspeed

TremLFO=plfo()
TREMvalue=1.0       # Full volume
TREMampl=0          # declare
TREMspeed=0         # declare
TREMtrill=False     # declare
def TremProc(*z):
    global VIBRspeed,TREMtrill,TREMvalue,TREMampl
    if effect==4:
        TremLFO.setstep(VIBRspeed)
    TremLFO.process()
    if TREMtrill:
        TREMvalue=1-(TREMampl*TremLFO.getinvsaw()/127)
    else:
        TREMvalue=1-(TREMampl*TremLFO.gettriangle()/127)
def TremTidy(TurnOn):
    global TREMspeed,TREMvalue
    if TurnOn:
        TremLFO.settriangle(0)      # start at max
        TremLFO.setstep(TREMspeed)  # and with correct speed
    else:
        TREMvalue=1                 # restore volume
def TremSetampl(CCval,*z):
    global TREMampl
    TREMampl=1.0*CCval/127.0 # values 0-1, range like GUI
def TremSetspeed(CCval,*z):
    global TREMspeed
    TREMspeed=1.0*CCval/4    # align with GUI
    TremLFO.setstep(TREMspeed)
def TremToggletrill(CCval,*z):
    global TREMtrill
    TREMtrill=not(TREMtrill)
gv.setMC(gv.TREMDEPTH,TremSetampl)
gv.setMC(gv.TREMSPEED,TremSetspeed)
gv.setMC(gv.TREMTRILL,TremToggletrill)

PanLFO=plfo()
gv.PANvalue=0.0     # Center, in gv for samplerbox_audio only
PANwidth=0          # declare
PANspeed=0          # declare
def PanProc(*z):
    global VIBRspeed,PANwidth
    if effect==4:
        PanLFO.setstep(VIBRspeed)
    PanLFO.process()
    gv.PANvalue=1-2.0*PANwidth*PanLFO.gettriangle()/127
def PanTidy(TurnOn):
    global PANspeed
    if TurnOn:
        PanLFO.settriangle(63)      # start centered (don't care anyway)
        PanLFO.setstep(PANspeed)    # and with correct speed
    else:
        gv.PANvalue=0               # restore center
def PanSetwidth(CCval,*z):
    global PANwidth
    PANwidth=CCval/127.0            # values 0-1, both left & right
def PanSetspeed(CCval,*z):
    global PANspeed
    PANspeed=1.0*CCval/4    # align with GUI
    PanLFO.setstep(PANspeed)
gv.setMC(gv.PANWIDTH,PanSetwidth)
gv.setMC(gv.PANSPEED,PanSetspeed)

def RotaProc(*z):
    VibrProc()
    TremProc()
    PanProc()
def RotaTidy(TurnOn):
    global VIBRvalue,VIBRspeed,VIBRtrill,TREMtrill,TREMvalue
    if TurnOn:
        VibrLFO.settriangle(-63)    # start about neutral, going down (=going away)
        VibrLFO.setstep(VIBRspeed)  # and with correct speed
        VIBRtrill=False
        TremLFO.settriangle(0)      # start at max (so it will go away too)
        TREMtrill=False
        PanLFO.settriangle(63)      # start in the middle
    else:
        VIBRvalue=0                 # tune the note
        TREMvalue=1                 # restore volume
        gv.PANvalue=0               # restore center

def LFOspeed(CCval,*z):
    if effect==3:
        PanSetspeed(CCval)
    elif effect==2:
        TremSetspeed(CCval)
    else:
        VibrSetspeed(CCval)
gv.setMC(gv.LFOSPEED,LFOspeed)

effects=["Off",gv.VIBRATO,gv.TREMOLO,gv.PANNING,gv.ROTATE]
process=[gv.NoProc,VibrProc,TremProc,PanProc,RotaProc]
tidy=[gv.NoProc,VibrTidy,TremTidy,PanTidy,RotaTidy]
effect=0   # 0 = no vibrato/tremolo/pan/rotate
def setType(x,*z):
    global effect
    if x!=effect:
        tidy[effect](False)
        tidy[x](True)
        effect=x
def toggleType(x):
    if x==effect:
        setType(0)
    else:
        setType(x)
def Vibrato(*z):
    toggleType(1)
def Tremolo(*z):
    toggleType(2)
def Panning(*z):
    toggleType(3)
def Rotate(*z):
    toggleType(4)
gv.setMC(gv.TREMOLO,Tremolo)
gv.setMC(gv.VIBRATO,Vibrato)
gv.setMC(gv.PANNING,Panning)
gv.setMC(gv.ROTATE,Rotate)

def reset(scope=-1):
    global VIBRpitch,VIBRspeed,VIBRtrill,TREMampl,BOXTREMspeed,TREMspeed,TREMtrill,PANwidth,PANspeed
    effect=0
    if scope in [-2, -4]:       # also reset values
        effect = gv.getindex( gv.cp.get(gv.cfg,"LFOeffect".lower()), effects, True, False )
        if effect < 0 :
            effect = 0
        #if scope == -2:         # load sample set default
        #    load sample set default
        #else:                   # system default
        VIBRpitch=gv.cp.getfloat(gv.cfg,"VIBRpitch".lower())
        VIBRspeed=gv.cp.getint(gv.cfg,"VIBRspeed".lower())
        VIBRtrill=gv.cp.getboolean(gv.cfg,"VIBRtrill".lower())
        TREMampl=gv.cp.getfloat(gv.cfg,"TREMampl".lower())
        BOXTREMspeed=gv.cp.getint(gv.cfg,"TREMspeed".lower())
        TREMspeed=BOXTREMspeed
        TREMtrill=gv.cp.getboolean(gv.cfg,"TREMtrill".lower())
        PANwidth=gv.cp.getfloat(gv.cfg,"PANwidth".lower())
        PANspeed=gv.cp.getint(gv.cfg,"PANspeed".lower())
    setType(effect)
reset(-2)
