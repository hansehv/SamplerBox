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
cfg="config"

#
# Reverb based on Freeverb by Jezar at Dreampoint
# Reverb is about 11% on PI3
#
c_filters.fvsetroomsize.argtypes = [c_float]
c_filters.fvsetdamp.argtypes = [c_float]
c_filters.fvsetwet.argtypes = [c_float]
c_filters.fvsetdry.argtypes = [c_float]
c_filters.fvsetwidth.argtypes = [c_float]
#gv.FVtypes=["Off","On"]
def FVsetType(x,*z):
    c_filters.fvmute()
    gv.FVtype=x
def FVsetReverb(*z):
    if gv.FVtype==1: gv.FVtype=0
    else: FVsetType(1)
def FVsetroomsize(x,*z):
    gv.FVroomsize=1.0*x/127.0
    c_filters.fvsetroomsize(gv.FVroomsize)
def FVsetdamp(x,*z):
    gv.FVdamp=1.0*x/127.0
    c_filters.fvsetdamp(gv.FVdamp)
def FVsetlevel(x,*z):
    gv.FVlevel=1.0*x/127.0
    c_filters.fvsetwet(gv.FVlevel)
    c_filters.fvsetdry(1-gv.FVlevel)
def FVsetwidth(x,*z):
    gv.FVwidth=1.0*x/127.0
    c_filters.fvsetwidth(gv.FVwidth)
def FVreset():
    FVsetType(0)
    FVsetroomsize(gv.cp.getfloat(cfg,"FVroomsize".lower())*127)
    FVsetdamp(gv.cp.getfloat(cfg,"FVdamp".lower())*127)
    FVsetlevel(gv.cp.getfloat(cfg,"FVlevel".lower())*127)
    FVsetwidth(gv.cp.getfloat(cfg,"FVwidth".lower())*127)
FVreset()
gv.MC[gv.getindex(gv.REVERB,gv.MC)][2]=FVsetReverb      # announce to CCmap
gv.MC[gv.getindex(gv.REVERBLVL,gv.MC)][2]=FVsetlevel
gv.MC[gv.getindex(gv.REVERBROOM,gv.MC)][2]=FVsetroomsize
gv.MC[gv.getindex(gv.REVERBDAMP,gv.MC)][2]=FVsetdamp
gv.MC[gv.getindex(gv.REVERBWIDTH,gv.MC)][2]=FVsetwidth

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
gv.AWminfreq=0  # avoid undefined vars
gv.AWmaxfreq=0
def AWsetMinFreq(x,*z):         # 20-500
    if x<4: x=4
    gv.AWminfreq=500.0*x/127.0
    if gv.AWminfreq>(gv.AWmaxfreq-100): gv.AWmaxfreq=gv.AWminfreq+100
    c_filters.awsetMinMaxFreq(gv.AWminfreq,gv.AWmaxfreq)
def AWsetMaxFreq(x,*z):         # 1000-10000
    gv.AWmaxfreq=10000.0*x/127.0
    if gv.AWminfreq>(gv.AWmaxfreq-100): gv.AWmaxfreq=gv.AWminfreq+100
    c_filters.awsetMinMaxFreq(gv.AWminfreq,gv.AWmaxfreq)
def AWsetQualityFactor(x,*z):   # 0.25-25
    if x==0: x=1
    gv.AWqfactor=25.0*x/127.0
    c_filters.awsetQualityFactor(gv.AWqfactor)
def AWsetMixing(x,*z):          # 0-1, where 0=dry and 1 is wet
    gv.AWmixing=1.0*x/127.0
    c_filters.awsetMixing(gv.AWmixing)
gv.AWtypes=["Off",gv.AUTOWAHENV,gv.AUTOWAHLFO,gv.AUTOWAHMAN]
def AWsetType(x,*z):         # 0,1,2,3 = off,envelope,LFO,CC
    c_filters.awmute()
    c_filters.awsetWahType(x)
    gv.AWtype=x
def AWtoggle(x):
    if gv.AWtype==x: gv.AWtype=0
    else: AWsetType(x)
def AWsetENV(*z):
    AWtoggle(1)
def AWsetLFO(*z):
    AWtoggle(2)
def AWsetMAN(*z):
    AWtoggle(3)
def AWsetAttack(x,*z):          # 0.5-0.005
    if x==0: x=1
    gv.AWattack=.5*x/127.0
    c_filters.awsetAttack(gv.AWattack)
def AWsetRelease(x,*z):
      # 0.05-0.0005
    if x==0: x=1
    gv.AWrelease=.05*x/127.0
    c_filters.awsetRelease(gv.AWrelease)
def AWsetSpeed(x,*z):           # 100-1100 (?)
    gv.AWspeed=100+1000*x/127.0
    c_filters.awsetSpeed(gv.AWspeed)
def AWsetCCval(x,*z):           # 0-127
    gv.AWccval=x
    c_filters.awsetCCval(gv.AWccval)
def AWsetLVLrange(x,*z):           # 0-100
    gv.AWlvlrange=100.0*x/127.0
    c_filters.awsetLVLrange(gv.AWlvlrange)
def AWreset():
    AWsetType(0)
    AWsetCCval(0)   # pedal back to base
    AWsetQualityFactor(gv.cp.getfloat(cfg,"AWqfactor".lower())/25*127)
    AWsetMixing(gv.cp.getfloat(cfg,"AWmixing".lower())*127)
    AWsetMinFreq(gv.cp.getfloat(cfg,"AWminfreq".lower())/500*127)
    AWsetMaxFreq(gv.cp.getfloat(cfg,"AWmaxfreq".lower())/10000*127)
    AWsetAttack(gv.cp.getfloat(cfg,"AWattack".lower())/0.5*127)
    AWsetRelease(gv.cp.getfloat(cfg,"AWrelease".lower())/0.05*127)
    AWsetSpeed((gv.cp.getfloat(cfg,"AWspeed".lower())-100)/1000*127)
    AWsetLVLrange(gv.cp.getfloat(cfg,"AWlvlrange".lower())/100*127)
AWreset()
gv.MC[gv.getindex(gv.AUTOWAHENV,gv.MC)][2]=AWsetENV     # announce to CCmap
gv.MC[gv.getindex(gv.AUTOWAHLFO,gv.MC)][2]=AWsetLFO
gv.MC[gv.getindex(gv.AUTOWAHMAN,gv.MC)][2]=AWsetMAN
gv.MC[gv.getindex(gv.AUTOWAHMIN,gv.MC)][2]=AWsetMinFreq
gv.MC[gv.getindex(gv.AUTOWAHMAX,gv.MC)][2]=AWsetMaxFreq
gv.MC[gv.getindex(gv.AUTOWAHQ,gv.MC)][2]=AWsetQualityFactor
gv.MC[gv.getindex(gv.AUTOWAHLVL,gv.MC)][2]=AWsetMixing
gv.MC[gv.getindex(gv.AUTOWAHATTACK,gv.MC)][2]=AWsetAttack
gv.MC[gv.getindex(gv.AUTOWAHRELEASE,gv.MC)][2]=AWsetRelease
gv.MC[gv.getindex(gv.AUTOWAHSPEED,gv.MC)][2]=AWsetSpeed
gv.MC[gv.getindex(gv.AUTOWAHPEDAL,gv.MC)][2]=AWsetCCval
gv.MC[gv.getindex(gv.AUTOWAHLVLRNGE,gv.MC)][2]=AWsetLVLrange

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
gv.DLYsteep=0   # avoid undefined vars
gv.DLYsteplen=0
gv.DLYmin=0
gv.DLYmax=0
gv.DLYtypes=["Off",gv.ECHO,gv.FLANGER]
def DLYsetType(x,*z):
    c_filters.dlymute()
    c_filters.dlysettype(x)
    if x==1: c_filters.dlysetmix(gv.DLYdry)
    if x==2: c_filters.dlysetmix(1-gv.DLYwet)
    gv.DLYtype=x
def DLYsetEcho(*z):      # in Hz, should be same as audiovalue
    if gv.DLYtype==1: gv.DLYtype=0
    else: DLYsettype(1)
def DLYsetFlanger(*z):
    if gv.DLYtype==2: gv.DLYtype=0
    else: DLYsettype(2)
def DLYsetfb(x,*z):     # 0-1
    gv.DLYfb=1.0*x/127.0
    c_filters.dlysetfb(gv.DLYfb)
def DLYsetwet(x,*z):    # 0-1
    gv.DLYwet=1.0*x/127.0
    c_filters.dlysetfw(gv.DLYwet)
    if gv.DLYtype==2: c_filters.dlysetmix(1-gv.DLYwet)
def DLYsetdry(x,*z):    # 0-1
    gv.DLYdry=1.0*x/127.0
    if gv.DLYtype==1: c_filters.dlysetmix(gv.DLYdry)
def DLYsettime(x,*z):   # 1000-61000 for echo
    gv.DLYtime=1000+60000*x/127
    c_filters.dlysetdelay(gv.DLYtime)
def DLYsetsteep(x,*z):    # 1-11
    gv.DLYsteep=1+x/12.7
    c_filters.dlysetsweep(gv.DLYsteep,gv.DLYsteplen)
def DLYsetsteplen(x,*z):   # 300-3300 for flanger
    gv.DLYsteplen=300.0+3000*x/127
    c_filters.dlysetsweep(gv.DLYsteep,gv.DLYsteplen)
def DLYsetmin(x,*z):    # 5-25
    gv.DLYmin=5.0+x/6.35
    c_filters.dlysetrange(gv.DLYmin,gv.DLYmax)
def DLYsetmax(x,*z):   # 50-150 for flanger
    gv.DLYmax=50.0+x/1.27
    c_filters.dlysetrange(gv.DLYmin,gv.DLYmax)
def DLYreset():
    DLYsetType(0)
    DLYsetfb(gv.cp.getfloat(cfg,"DLYfb".lower())*127)
    DLYsetwet(gv.cp.getfloat(cfg,"DLYwet".lower())*127)
    DLYsetdry(gv.cp.getfloat(cfg,"DLYdry".lower())*127)
    DLYsettime((gv.cp.getfloat(cfg,"DLYtime".lower())-1000)/60000*127)
    DLYsetsteep((gv.cp.getfloat(cfg,"DLYsteep".lower())-1)/10*127)
    DLYsetsteplen((gv.cp.getfloat(cfg,"DLYsteplen".lower())-300)/3000*127)
    DLYsetmin((gv.cp.getfloat(cfg,"DLYmin".lower())-5)/20*127)
    DLYsetmax((gv.cp.getfloat(cfg,"DLYmax".lower())-50)/100*127)
DLYreset()
gv.MC[gv.getindex(gv.ECHO,gv.MC)][2]=DLYsetEcho     # announce to CCmap
gv.MC[gv.getindex(gv.FLANGER,gv.MC)][2]=DLYsetFlanger
gv.MC[gv.getindex(gv.DELAYFB,gv.MC)][2]=DLYsetfb
gv.MC[gv.getindex(gv.DELAYFW,gv.MC)][2]=DLYsetwet
gv.MC[gv.getindex(gv.DELAYMIX,gv.MC)][2]=DLYsetdry
gv.MC[gv.getindex(gv.DELAYTIME,gv.MC)][2]=DLYsettime
gv.MC[gv.getindex(gv.DELAYSTEEP,gv.MC)][2]=DLYsetsteep
gv.MC[gv.getindex(gv.DELAYSTEPLEN,gv.MC)][2]=DLYsetsteplen
gv.MC[gv.getindex(gv.DELAYMIN,gv.MC)][2]=DLYsetmin
gv.MC[gv.getindex(gv.DELAYMAX,gv.MC)][2]=DLYsetmax

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
#gv.LFtypes=["Off","On"]
def LFsetType(x,*z):
    c_filters.lfmute()
    gv.LFtype=x
def LFsetLadder(*z):
    if gv.LFtype==1: gv.LFtype=0
    else: LFsetType(1)
def LFsetResonance(x,*z):       # 0 - 3.8
    gv.LFresonance=1.0*x*3.8/127
    c_filters.lfsetresonance(gv.LFresonance)
def LFsetCutoff(x,*z):          # 1000 - 11000
    gv.LFcutoff=1000.0+x*10000/127
    c_filters.lfsetcutoff(gv.LFcutoff)
def LFsetDrive(x,*z):           # 1 - 21 ?
    gv.LFdrive=1.0+x*0.1575     # =20/127
    c_filters.lfsetdrive(gv.LFdrive)
def LFsetLvl(x,*z):             # 0 - 1
    gv.LFlvl=x*1.0/127
    c_filters.lfsetwet(gv.LFlvl)
    c_filters.lfsetdry(1-gv.LFlvl)
def LFsetGain(x,*z):            # 1 - 11
    gv.LFgain=1.0+x*0.0787      # =10/127
    c_filters.lfsetgain(gv.LFgain)
def LFreset():
    LFsetType(0)
    LFsetResonance((gv.cp.getfloat(cfg,"LFresonance".lower())/3.8)*127)
    LFsetCutoff((gv.cp.getfloat(cfg,"LFcutoff".lower())-1000)/10000*127)
    LFsetDrive((gv.cp.getfloat(cfg,"LFdrive".lower())-1)/20*127)
    LFsetLvl(gv.cp.getfloat(cfg,"LFlvl".lower())*127)
    LFsetGain((gv.cp.getfloat(cfg,"LFgain".lower())-1)/10*127)
LFreset()
gv.MC[gv.getindex(gv.LADDER,gv.MC)][2]=LFsetLadder      # announce to CCmap
gv.MC[gv.getindex(gv.LADDERRES,gv.MC)][2]=LFsetResonance
gv.MC[gv.getindex(gv.LADDERLVL,gv.MC)][2]=LFsetLvl
gv.MC[gv.getindex(gv.LADDERCUTOFF,gv.MC)][2]=LFsetCutoff
gv.MC[gv.getindex(gv.LADDERDRIVE,gv.MC)][2]=LFsetDrive
gv.MC[gv.getindex(gv.LADDERGAIN,gv.MC)][2]=LFsetGain
