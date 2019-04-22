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
gv.VIBRvalue=0         # Value 0 gives original note
def VibrProc(*z):
    VibrLFO.process()
    if gv.VIBRtrill:
        gv.VIBRvalue=(( (128*(VibrLFO.getblock())) /gv.pitchdiv)-gv.pitchneutral)*gv.VIBRpitch
    else:
        gv.VIBRvalue=(( (128*(VibrLFO.gettriangle())) /gv.pitchdiv)-gv.pitchneutral)*gv.VIBRpitch
def VibrTidy(TurnOn):
    if TurnOn:
        VibrLFO.settriangle(63)     # start about neutral, going up
        VibrLFO.setstep(gv.VIBRspeed)  # and with correct speed
    else:
        gv.VIBRvalue=0              # tune the note
def VibrSetpitch(CCval,*z):
        gv.VIBRpitch=1.0*CCval/32   # steps of 1/32th, range like GUI
def VibrSetspeed(CCval,*z):
        gv.VIBRspeed=1.0*CCval/4    # range=32
        VibrLFO.setstep(gv.VIBRspeed)
gv.MC[gv.getindex(gv.VIBRDEPTH,gv.MC)][2]=VibrSetpitch
gv.MC[gv.getindex(gv.VIBRSPEED,gv.MC)][2]=VibrSetspeed
#gv.VibrSetspeed=VibrSetspeed

TremLFO=plfo()
gv.TREMvalue=1.0       # Full volume
def TremProc(*z):
    if gv.LFOtype==4:
        TremLFO.setstep(gv.VIBRspeed)
    TremLFO.process()
    if gv.TREMtrill:
        gv.TREMvalue=1-(gv.TREMampl*TremLFO.getinvsaw()/127)
    else:
        gv.TREMvalue=1-(gv.TREMampl*TremLFO.gettriangle()/127)
def TremTidy(TurnOn):
    if TurnOn:
        TremLFO.settriangle(0)      # start at max
        TremLFO.setstep(gv.TREMspeed)  # and with correct speed
    else:
        gv.TREMvalue=1              # restore volume
def TremSetampl(CCval,*z):
    gv.TREMampl=1.0*CCval/127.0 # values 0-1, range like GUI
def TremSetspeed(CCval,*z):
    gv.TREMspeed=1.0*CCval/4    # align with GUI
    TremLFO.setstep(gv.TREMspeed)
gv.MC[gv.getindex(gv.TREMDEPTH,gv.MC)][2]=TremSetampl
gv.MC[gv.getindex(gv.TREMSPEED,gv.MC)][2]=TremSetspeed
#gv.TremSetspeed=TremSetspeed

PanLFO=plfo()
gv.PANvalue=0.0        # Center
def PanProc(*z):
    if gv.LFOtype==4:
        PanLFO.setstep(gv.VIBRspeed)
    PanLFO.process()
    gv.PANvalue=1-2.0*gv.PANwidth*PanLFO.gettriangle()/127
def PanTidy(TurnOn):
    if TurnOn:
        PanLFO.settriangle(63)      # start centered (don't care anyway)
        PanLFO.setstep(gv.PANspeed)  # and with correct speed
    else:
        gv.PANvalue=1              # restore center
def PanSetwidth(CCval,*z):
    gv.PANwidth=2.0*CCval/127.0 # values 0-1, both left & right
def PanSetspeed(CCval,*z):
    gv.PANspeed=1.0*CCval/4    # align with GUI
    PanLFO.setstep(gv.PANspeed)
gv.MC[gv.getindex(gv.PANWIDTH,gv.MC)][2]=PanSetwidth
gv.MC[gv.getindex(gv.PANSPEED,gv.MC)][2]=PanSetspeed
#gv.PanSetspeed=PanSetspeed

def RotaProc(*z):
    VibrProc()
    TremProc()
    PanProc()
def RotaTidy(TurnOn):
    if TurnOn:
        VibrLFO.settriangle(-63)    # start about neutral, going down (=going away)
        VibrLFO.setstep(gv.VIBRspeed)  # and with correct speed
        gv.VIBRtrill=False
        TremLFO.settriangle(0)      # start at max (so it will go away too)
        gv.TREMtrill=False
        PanLFO.settriangle(63)      # start in the middle
    else:
        gv.VIBRvalue=0              # tune the note
        gv.TREMvalue=1              # restore volume
        gv.PANvalue=1               # restore center

def LFOspeed(CCval,*z):
    if gv.LFOtype==3:
        PanSetspeed(CCval)
    elif gv.LFOtype==2:
        TremSetspeed(CCval)
    else:
        VibrSetspeed(CCval)
gv.MC[gv.getindex(gv.LFOSPEED,gv.MC)][2]=LFOspeed

gv.LFOtypes=["Off",gv.VIBRATO,gv.TREMOLO,gv.PANNING,gv.ROTATE]
process=[gv.NoProc,VibrProc,TremProc,PanProc,RotaProc]
tidy=[gv.NoProc,VibrTidy,TremTidy,PanTidy,RotaTidy]
gv.LFOtype=0   # 0 = no vibrato/tremolo/pan/rotate
def setType(x,*z):
    if x!=gv.LFOtype:
        tidy[gv.LFOtype](False)
        tidy[x](True)
        gv.LFOtype=x
def Vibrato(*z):
    setProc(1)
def Tremolo(*z):
    setProc(2)
def Panning(*z):
    setProc(3)
def Rotate(*z):
    setProc(4)
#gv.LFOsetType=setProc
gv.MC[gv.getindex(gv.TREMOLO,gv.MC)][2]=Tremolo
gv.MC[gv.getindex(gv.VIBRATO,gv.MC)][2]=Vibrato
gv.MC[gv.getindex(gv.PANNING,gv.MC)][2]=Panning
gv.MC[gv.getindex(gv.ROTATE,gv.MC)][2]=Rotate

def LFOreset():
    setType(0)
    gv.VIBRpitch=gv.cp.getfloat(gv.cfg,"VIBRpitch".lower())
    gv.VIBRspeed=gv.cp.getint(gv.cfg,"VIBRspeed".lower())
    gv.VIBRtrill=gv.cp.getboolean(gv.cfg,"VIBRtrill".lower())
    gv.TREMampl=gv.cp.getfloat(gv.cfg,"TREMampl".lower())
    gv.BOXTREMspeed=gv.cp.getint(gv.cfg,"TREMspeed".lower())
    gv.TREMspeed=gv.BOXTREMspeed
    gv.TREMtrill=gv.cp.getboolean(gv.cfg,"TREMtrill".lower())
    gv.PANwidth=gv.cp.getfloat(gv.cfg,"PANwidth".lower())
    gv.PANspeed=gv.cp.getint(gv.cfg,"PANspeed".lower())
LFOreset()
