###############################################################
#   Interfacing with C++ coding in the filters directory.
#   Inspired by Erik Nieuwlands (www.nickyspride.nl/sb2/)
#   Using C++ is necessary to enable CPU intensive effects.
#   Their impact still remains visible, see percentages below.
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
#
import gv
import ctypes
from ctypes import *
c_float_p = ctypes.POINTER(ctypes.c_float)
c_short_p = ctypes.POINTER(ctypes.c_short)
c_filters = cdll.LoadLibrary('./filters/interface.so')

#
# Reverb based on Freeverb by Jezar at Dreampoint
# Reverb is about 11% on PI3
#
c_filters.fvsetroomsize.argtypes = [c_float]
c_filters.fvsetdamp.argtypes = [c_float]
c_filters.fvsetwet.argtypes = [c_float]
c_filters.fvsetdry.argtypes = [c_float]
c_filters.fvsetwidth.argtypes = [c_float]
FVtypes=["Off","On"]
FVtype=0
def FVsetType(x,*z):
    global FVtype
    c_filters.fvmute()
    FVtype=x
def FVsetReverb(*z):
    global FVtype
    if FVtype==1: FVtype=0
    else: FVsetType(1)
FVroomsize=0.2
def FVsetroomsize(x,*z):
    global FVroomsize
    FVroomsize=1.0*x/127.0
    c_filters.fvsetroomsize(FVroomsize)
FVdamp=0.5
def FVsetdamp(x,*z):
    global FVdamp
    FVdamp=1.0*x/127.0
    c_filters.fvsetdamp(FVdamp)
FVlevel=0.3
def FVsetlevel(x,*z):
    global FVlevel
    FVlevel=1.0*x/127.0
    c_filters.fvsetwet(FVlevel)
    c_filters.fvsetdry(1-FVlevel)
FVwidth=1.0
def FVsetwidth(x,*z):
    global FVwidth
    FVwidth=1.0*x/127.0
    c_filters.fvsetwidth(FVwidth)
def FVreset():
    FVsetType(0)
    FVsetroomsize(gv.cp.getfloat(gv.cfg,"FVroomsize".lower())*127)
    FVsetdamp(gv.cp.getfloat(gv.cfg,"FVdamp".lower())*127)
    FVsetlevel(gv.cp.getfloat(gv.cfg,"FVlevel".lower())*127)
    FVsetwidth(gv.cp.getfloat(gv.cfg,"FVwidth".lower())*127)
FVreset()
gv.setMC(gv.REVERB,FVsetReverb)      # announce to CCmap
gv.setMC(gv.REVERBLVL,FVsetlevel)
gv.setMC(gv.REVERBROOM,FVsetroomsize)
gv.setMC(gv.REVERBDAMP,FVsetdamp)
gv.setMC(gv.REVERBWIDTH,FVsetwidth)

#
# AutoWah (envelope & LFO) and Wah-Wah (pedal) based on
# autowah by Daniel Zanco: https://github.com/dangpzanco/autowah
# Reverb is about 6% on PI3
#
c_filters.awsetMinMaxFreq.argtypes = [c_float, c_float]
c_filters.awsetQualityFactor.argtypes = [c_float]
c_filters.awsetMixing.argtypes = [c_float]
c_filters.awsetAttack.argtypes = [c_float]
c_filters.awsetRelease.argtypes = [c_float]
c_filters.awsetSpeed.argtypes = [c_float]
c_filters.awsetCCval.argtypes = [c_float]
c_filters.awsetLVLrange.argtypes = [c_float]
#def AWsetMinMaxFreq(minval,maxval): # in Hz
AWminfreq=0.0  # avoid undefined vars
AWmaxfreq=0.0
def AWsetMinFreq(x,*z):         # 20-500
    global AWminfreq,AWmaxfreq
    if x<4: x=4
    AWminfreq=500.0*x/127.0
    if AWminfreq>(AWmaxfreq-100): AWmaxfreq=AWminfreq+100
    c_filters.awsetMinMaxFreq(AWminfreq,AWmaxfreq)
def AWsetMaxFreq(x,*z):         # 1000-10000
    global AWminfreq,AWmaxfreq
    AWmaxfreq=10000.0*x/127.0
    if AWminfreq>(AWmaxfreq-100): AWmaxfreq=AWminfreq+100
    c_filters.awsetMinMaxFreq(AWminfreq,AWmaxfreq)
AWqfactor=0.0
def AWsetQualityFactor(x,*z):   #
    global AWqfactor
    if x==0: x=1
    AWqfactor=10.0*x/127.0
    c_filters.awsetQualityFactor(AWqfactor)
AWmixing=.5
def AWsetMixing(x,*z):          # 0-1, where 0=dry and 1 is wet
    global AWmixing
    AWmixing=1.0*x/127.0
    c_filters.awsetMixing(AWmixing)
AWtypes=["Off",gv.AUTOWAHENV,gv.AUTOWAHLFO,gv.AUTOWAHMAN]
AWtype=0
def AWsetType(x,*z):         # 0,1,2,3 = off,envelope,LFO,CC
    global AWtype
    c_filters.awmute()
    c_filters.awsetWahType(x)
    AWtype=x
def AWtoggle(x):
    global AWtype
    if AWtype==x: AWtype=0
    else: AWsetType(x)
def AWsetENV(*z):
    AWtoggle(1)
def AWsetLFO(*z):
    AWtoggle(2)
def AWsetMAN(*z):
    AWtoggle(3)
AWattack=0.05
def AWsetAttack(x,*z):          # 0.5-0.005
    global AWattack
    if x==0: x=1
    AWattack=.5*x/127.0
    c_filters.awsetAttack(AWattack)
AWrelease=0.005
def AWsetRelease(x,*z):
    global AWrelease
      # 0.05-0.0005
    if x==0: x=1
    AWrelease=.05*x/127.0
    c_filters.awsetRelease(AWrelease)
AWspeed=500
def AWsetSpeed(x,*z):           # 100-1100 (?)
    global AWspeed
    AWspeed=100+1000*x/127.0
    c_filters.awsetSpeed(AWspeed)
AWccval=0
def AWsetCCval(x,*z):           # 0-127
    global AWccval
    AWccval=x
    c_filters.awsetCCval(AWccval)
AWlvlrange=100
def AWsetLVLrange(x,*z):           # 0-100
    global AWlvlrange
    AWlvlrange=100.0*x/127.0
    c_filters.awsetLVLrange(AWlvlrange)
def AWreset():
    AWsetType(0)
    AWsetCCval(0)   # pedal back to base
    AWsetQualityFactor(gv.cp.getfloat(gv.cfg,"AWqfactor".lower())/25*127)
    AWsetMixing(gv.cp.getfloat(gv.cfg,"AWmixing".lower())*127)
    AWsetMinFreq(gv.cp.getfloat(gv.cfg,"AWminfreq".lower())/500*127)
    AWsetMaxFreq(gv.cp.getfloat(gv.cfg,"AWmaxfreq".lower())/10000*127)
    AWsetAttack(gv.cp.getfloat(gv.cfg,"AWattack".lower())/0.5*127)
    AWsetRelease(gv.cp.getfloat(gv.cfg,"AWrelease".lower())/0.05*127)
    AWsetSpeed((gv.cp.getfloat(gv.cfg,"AWspeed".lower())-100)/1000*127)
    AWsetLVLrange(gv.cp.getfloat(gv.cfg,"AWlvlrange".lower())/100*127)
AWreset()
gv.setMC(gv.AUTOWAHENV,AWsetENV)     # announce to CCmap
gv.setMC(gv.AUTOWAHLFO,AWsetLFO)
gv.setMC(gv.AUTOWAHMAN,AWsetMAN)
gv.setMC(gv.AUTOWAHMIN,AWsetMinFreq)
gv.setMC(gv.AUTOWAHMAX,AWsetMaxFreq)
gv.setMC(gv.AUTOWAHQ,AWsetQualityFactor)
gv.setMC(gv.AUTOWAHLVL,AWsetMixing)
gv.setMC(gv.AUTOWAHATTACK,AWsetAttack)
gv.setMC(gv.AUTOWAHRELEASE,AWsetRelease)
gv.setMC(gv.AUTOWAHSPEED,AWsetSpeed)
gv.setMC(gv.AUTOWAHPEDAL,AWsetCCval)
gv.setMC(gv.AUTOWAHLVLRNGE,AWsetLVLrange)

#
# Echo and flanger (delay line effects) based on codesnippets by
# Gabriel Rivas: https://www.dsprelated.com/code.php?submittedby=56840
# Delay is about 3% on PI3
#
c_filters.dlysetfb.argtypes = [c_float]
c_filters.dlysetfw.argtypes = [c_float]
c_filters.dlysetmix.argtypes = [c_float]
c_filters.dlysetdelay.argtypes = [c_float]
c_filters.dlysetsweep.argtypes = [c_float, c_float]
c_filters.dlysetrange.argtypes = [c_float, c_float]
DLYsteep=0   # avoid undefined vars
DLYsteplen=0
DLYmin=0
DLYmax=0
DLYtypes=["Off",gv.ECHO,gv.FLANGER]
DLYtype=0
def DLYsetType(x,*z):
    global DLYtype,DYdry,DLYwet
    c_filters.dlymute()
    c_filters.dlysettype(x)
    if x==1: c_filters.dlysetmix(DLYdry)
    if x==2: c_filters.dlysetmix(1-DLYwet)
    DLYtype=x
def DLYsetEcho(*z):      # in Hz, should be same as audiovalue
    global DLYtype
    if DLYtype==1: DLYtype=0
    else: DLYsetType(1)
def DLYsetFlanger(*z):
    global DLYtype
    if DLYtype==2: DLYtype=0
    else: DLYsetType(2)
DLYfb=0.5
def DLYsetfb(x,*z):     # 0-1
    global DLYfb
    DLYfb=1.0*x/127.0
    c_filters.dlysetfb(DLYfb)
DLYwet=0.5
def DLYsetwet(x,*z):    # 0-1
    global DLYwet
    DLYwet=1.0*x/127.0
    c_filters.dlysetfw(DLYwet)
    if DLYtype==2: c_filters.dlysetmix(1-DLYwet)
DLYdry=0.5
def DLYsetdry(x,*z):    # 0-1
    global DLYdry
    DLYdry=1.0*x/127.0
    if DLYtype==1: c_filters.dlysetmix(DLYdry)
DLYtime=40000
def DLYsettime(x,*z):   # 1000-61000 for echo
    global DLYtime
    DLYtime=1000+60000*x/127
    c_filters.dlysetdelay(DLYtime)
def DLYsetsteep(x,*z):    # 1-11
    global DLYsteep
    DLYsteep=1+x/12.7
    c_filters.dlysetsweep(DLYsteep,DLYsteplen)
def DLYsetsteplen(x,*z):   # 300-3300 for flanger
    global DLYsteplen
    DLYsteplen=300.0+3000*x/127
    c_filters.dlysetsweep(DLYsteep,DLYsteplen)
def DLYsetmin(x,*z):    # 5-25
    global DLYmin
    DLYmin=5.0+x/6.35
    c_filters.dlysetrange(DLYmin,DLYmax)
def DLYsetmax(x,*z):   # 50-150 for flanger
    global DLYmax
    DLYmax=50.0+x/1.27
    c_filters.dlysetrange(DLYmin,DLYmax)
def DLYreset():
    DLYsetType(0)
    DLYsetfb(gv.cp.getfloat(gv.cfg,"DLYfb".lower())*127)
    DLYsetwet(gv.cp.getfloat(gv.cfg,"DLYwet".lower())*127)
    DLYsetdry(gv.cp.getfloat(gv.cfg,"DLYdry".lower())*127)
    DLYsettime((gv.cp.getfloat(gv.cfg,"DLYtime".lower())-1000)/60000*127)
    DLYsetsteep((gv.cp.getfloat(gv.cfg,"DLYsteep".lower())-1)/10*127)
    DLYsetsteplen((gv.cp.getfloat(gv.cfg,"DLYsteplen".lower())-300)/3000*127)
    DLYsetmin((gv.cp.getfloat(gv.cfg,"DLYmin".lower())-5)/20*127)
    DLYsetmax((gv.cp.getfloat(gv.cfg,"DLYmax".lower())-50)/100*127)
DLYreset()
gv.setMC(gv.ECHO,DLYsetEcho)     # announce to CCmap
gv.setMC(gv.FLANGER,DLYsetFlanger)
gv.setMC(gv.DELAYFB,DLYsetfb)
gv.setMC(gv.DELAYFW,DLYsetwet)
gv.setMC(gv.DELAYMIX,DLYsetdry)
gv.setMC(gv.DELAYTIME,DLYsettime)
gv.setMC(gv.DELAYSTEEP,DLYsetsteep)
gv.setMC(gv.DELAYSTEPLEN,DLYsetsteplen)
gv.setMC(gv.DELAYMIN,DLYsetmin)
gv.setMC(gv.DELAYMAX,DLYsetmax)

#
# Moog lowpass ladderfilter based on algorithm developed by Stefano D'Angelo and Vesa Valimaki
# They take about 9% on PI3
#
c_filters.lfsetresonance.argtypes = [c_float]
c_filters.lfsetcutoff.argtypes = [c_float]
c_filters.lfsetdrive.argtypes = [c_float]
c_filters.lfsetdry.argtypes = [c_float]
c_filters.lfsetwet.argtypes = [c_float]
c_filters.lfsetgain.argtypes = [c_float]
LFtypes=["Off","On"]
LFtype=0
def LFsetType(x,*z):
    global LFtype
    c_filters.lfmute()
    LFtype=x
def LFsetLadder(*z):
    global LFtype
    if LFtype==1: LFtype=0
    else: LFsetType(1)
LFresonance=1.5
def LFsetResonance(x,*z):       # 0 - 3.8
    global LFresonance
    LFresonance=1.0*x*3.8/127
    c_filters.lfsetresonance(LFresonance)
LFcutoff=5000.0
def LFsetCutoff(x,*z):          # 1000 - 11000
    global LFcutoff
    LFcutoff=1000.0+x*10000/127
    c_filters.lfsetcutoff(LFcutoff)
LFdrive=1.0
def LFsetDrive(x,*z):           # 1 - 20 ?
    global LFdrive
    LFdrive=1.0+x*0.1575     # =20/127
    if LFdrive>20: LFdrive=20
    c_filters.lfsetdrive(LFdrive)
LFlvl=0.5
def LFsetLvl(x,*z):             # 0 - 1
    global LFlvl
    LFlvl=x*1.0/127
    c_filters.lfsetwet(LFlvl)
    c_filters.lfsetdry(1-LFlvl)
LFgain=10.0
def LFsetGain(x,*z):            # 1 - 11
    global LFgain
    LFgain=1.0+x*0.0787      # =10/127
    c_filters.lfsetgain(LFgain)
def LFreset():
    LFsetType(0)
    LFsetResonance((gv.cp.getfloat(gv.cfg,"LFresonance".lower())/3.8)*127)
    LFsetCutoff((gv.cp.getfloat(gv.cfg,"LFcutoff".lower())-1000)/10000*127)
    LFsetDrive((gv.cp.getfloat(gv.cfg,"LFdrive".lower())-1)/20*127)
    LFsetLvl(gv.cp.getfloat(gv.cfg,"LFlvl".lower())*127)
    LFsetGain((gv.cp.getfloat(gv.cfg,"LFgain".lower())-1)/10*127)
LFreset()
gv.setMC(gv.LADDER,LFsetLadder)      # announce to CCmap
gv.setMC(gv.LADDERRES,LFsetResonance)
gv.setMC(gv.LADDERLVL,LFsetLvl)
gv.setMC(gv.LADDERCUTOFF,LFsetCutoff)
gv.setMC(gv.LADDERDRIVE,LFsetDrive)
gv.setMC(gv.LADDERGAIN,LFsetGain)
