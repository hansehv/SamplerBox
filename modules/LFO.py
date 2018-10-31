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
# Clock can be via (filter)call in AudioCallback, on PI3 approx once per 11msec's
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
def Vibrato(x,y,z):     # Soundstream parms are dummy; proc affects sound generation
    VibrLFO.process()
    if gv.VIBRtrill:
        gv.VIBRvalue=(( (128*(VibrLFO.getblock())) /gv.pitchdiv)-gv.pitchneutral)*gv.VIBRpitch
    else:
        gv.VIBRvalue=(( (128*(VibrLFO.gettriangle())) /gv.pitchdiv)-gv.pitchneutral)*gv.VIBRpitch
def VibratoTidy(TurnOn):
    if TurnOn:
        VibrLFO.settriangle(63)     # start about neutral, going up
        VibrLFO.setstep(gv.VIBRspeed)  # and with correct speed
    else:
        gv.VIBRvalue=0              # tune the note
def VibrSetpitch(CCval,*z):
        gv.VIBRpitch=1.0*CCval/32   # steps of 1/32th, range like GUI
def VibrSetspeed(CCval,*z):
        gv.VIBRspeed=1.0*CCval/4    # align with GUI
        VibrLFO.setstep(gv.VIBRspeed)
        if gv.Filterkeys[gv.currfilter]==gv.ROTATE:
            gv.TREMspeed=gv.VIBRspeed
            TremLFO.setstep(gv.TREMspeed)
gv.MC[gv.getindex(gv.VIBRDEPTH,gv.MC)][2]=VibrSetpitch
gv.MC[gv.getindex(gv.VIBRSPEED,gv.MC)][2]=VibrSetspeed

TremLFO=plfo()
def Tremolo(x,y,z):     # Soundstream parms are dummy; proc affects sound generation
    TremLFO.process()
    if gv.TREMtrill:
        gv.TREMvalue=1-(gv.TREMampl*TremLFO.getinvsaw()/127)
    else:
        gv.TREMvalue=1-(gv.TREMampl*TremLFO.gettriangle()/127)
def TremoloTidy(TurnOn):
    if TurnOn:
        TremLFO.settriangle(0)      # start at max
        TremLFO.setstep(gv.TREMspeed)  # and with correct speed
    else:
        gv.TREMvalue=1              # restore volume
        gv.VIBRvalue=0              # tune the note
def TremSetampl(CCval,*z):
    gv.TREMampl=1.0*CCval/127.0 # values 0-1, range like GUI
def TremSetspeed(CCval,*z):
    gv.TREMspeed=1.0*CCval/4    # align with GUI
    TremLFO.setstep(gv.TREMspeed)
gv.MC[gv.getindex(gv.TREMDEPTH,gv.MC)][2]=TremSetampl
gv.MC[gv.getindex(gv.TREMSPEED,gv.MC)][2]=TremSetspeed

def Rotate(x,y,z):
    Vibrato(x,y,z)
    Tremolo(x,y,z)
def RotateTidy(TurnOn):
    if TurnOn:
        VibrLFO.settriangle(-63)    # start about neutral, going down (=going away)
        VibrLFO.setstep(gv.VIBRspeed)  # and with correct speed
        gv.VIBRtrill=False
        gv.TREMspeed=gv.VIBRspeed         # Take care: GUI or knobs must keep this relation !!
        TremLFO.settriangle(0)      # start at max (so it will go away too)
        TremLFO.setstep(gv.TREMspeed)  # and with correct speed
        gv.TREMtrill=False
    else:
        gv.VIBRvalue=0                 # tune the note
        gv.TREMvalue=1                 # restore volume
        gv.TREMspeed=gv.BOXTREMspeed      # set a default speed for normal tremolo

def LFOspeed(CCval,*z):
    if gv.Filterkeys[gv.currfilter]==gv.TREMOLO:
        TremSetspeed(CCval)
    else:
        VibrSetspeed(CCval)
gv.MC[gv.getindex(gv.LFOSPEED,gv.MC)][2]=LFOspeed
