###############################################################
#   Interfacing with C++ coding in the filters directory.
#   Inspired by Erik Nieuwlands (www.nickyspride.nl/sb2/)
#   Using C++ is necessary to enable CPU intensive effects.
#   Their impact still remains visible, see percentages below.
#
#   Functions are written to communicate with MIDI controllers,
#   either toggles, switches or variable inputs ranging 0-127.
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
#
import gv
import ctypes,operator
from ctypes import *
c_float_p = ctypes.POINTER(ctypes.c_float)
c_double_p = ctypes.POINTER(ctypes.c_double)
c_short_p = ctypes.POINTER(ctypes.c_short)
c_filters = cdll.LoadLibrary('./filters/interface.so')

#
#   O V E R A L L    R O U T I N E S
#
REVERB = "Reverb"
WAH = "Wah"
DELAY = "Delay"
MOOG = "Moog"
OVERDRIVE = "Overdrive"
LIMITER = "Limiter"

def ResetAll(scope=-1):
    FVreset(scope)
    AWreset(scope)
    DLYreset(scope)
    LFreset(scope)
    ODreset(scope)
    PLreset(scope)

def newprocess():
    global active
    tmp = []
    for m in effects:
        if effects[m][1]:
            tmp.append([effects[m][0],effects[m][2]])
    tmp.sort(key=operator.itemgetter(0))
    active = tmp

def process(inS, frame_count):
    i=0
    while True:
        if i >= len(active):     # test in advance for safeguard
            break
        active[i][1](inS.ctypes.data_as(c_float_p), inS.ctypes.data_as(c_float_p), frame_count)
        i += 1

def seteffect(effect, state):
    global effects
    oldstate = effects[effect][1]
    effects[effect][1] = state
    if ( (state and not oldstate) or
         (oldstate and not state) ):
        newprocess()

def setprio (effect, newprio):
    if effects[effect][0] != newprio and newprio in range(1,len(effects)+1):
        oldprio = effects[effect][0]
        if oldprio < newprio:
            for m in effects:
                if  effects[m][0] > oldprio and effects[m][0] <= newprio:
                    effects[m][0] -= 1
        else:
            for m in effects:
                if  effects[m][0] < oldprio and effects[m][0] >= newprio:
                    effects[m][0] += 1
        effects[effect][0] = newprio
        newprocess()

#
#   = = =   R E V E R B   = = =
#
# Reverb based on Freeverb by Jezar at Dreampoint
# Reverb takes about 11% on PI3
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
    seteffect(REVERB, x)
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
def FVreset(scope=-1):
    FVtype = 0      # -1 turns of the effect, undefined values cover midi controller turn off
    if scope in [-2, -3, -4]:       # also reset values
        FVtype = gv.getindex( gv.cp.get(gv.cfg,"Reverb".lower()), FVtypes, True, False )
        if FVtype < 0 :
            FVtype = 0
        #if scope == -3:         # load sample set default
        #    load sample set default
        #else:                   # system default
        FVsetroomsize(gv.cp.getfloat(gv.cfg,"FVroomsize".lower())*127)
        FVsetdamp(gv.cp.getfloat(gv.cfg,"FVdamp".lower())*127)
        FVsetlevel(gv.cp.getfloat(gv.cfg,"FVlevel".lower())*127)
        FVsetwidth(gv.cp.getfloat(gv.cfg,"FVwidth".lower())*127)
    FVsetType(FVtype)
gv.setMC(gv.REVERB,FVsetReverb)      # announce to CCmap
gv.setMC(gv.REVERBLVL,FVsetlevel)
gv.setMC(gv.REVERBROOM,FVsetroomsize)
gv.setMC(gv.REVERBDAMP,FVsetdamp)
gv.setMC(gv.REVERBWIDTH,FVsetwidth)

#
#   = = =   W A H   = = =
#
# AutoWah (envelope & LFO) and Wah-Wah (pedal) based on
# autowah by Daniel Zanco: https://github.com/dangpzanco/autowah
# Autowah takes about 6% on PI3
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
    seteffect(WAH, x)
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
def AWreset(scope=-1):
    AWtype = 0      # -1 turns of the effect, undefined values cover midi controller turn off
    if scope in [-2, -3, -4]:       # also reset values
        AWtype = gv.getindex( gv.cp.get(gv.cfg,"Wah".lower()), AWtypes, True, False )
        if AWtype < 0 :
            AWtype = 0
        #if scope == -3:         # load sample set default
        #    load sample set default
        #else:                   # system default
        AWsetQualityFactor(gv.cp.getfloat(gv.cfg,"AWqfactor".lower())/25*127)
        AWsetMixing(gv.cp.getfloat(gv.cfg,"AWmixing".lower())*127)
        AWsetMinFreq(gv.cp.getfloat(gv.cfg,"AWminfreq".lower())/500*127)
        AWsetMaxFreq(gv.cp.getfloat(gv.cfg,"AWmaxfreq".lower())/10000*127)
        AWsetAttack(gv.cp.getfloat(gv.cfg,"AWattack".lower())/0.5*127)
        AWsetRelease(gv.cp.getfloat(gv.cfg,"AWrelease".lower())/0.05*127)
        AWsetSpeed((gv.cp.getfloat(gv.cfg,"AWspeed".lower())-100)/1000*127)
        AWsetLVLrange(gv.cp.getfloat(gv.cfg,"AWlvlrange".lower())/100*127)
    AWsetType(AWtype)       
    AWsetCCval(0)   # pedal always back to base
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
#   = = =   D E L A Y   = = =
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
    seteffect(DELAY, x)
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
def DLYreset(scope=-1):
    DLYtype = 0  # -1 turns of the effect, undefined values cover midi controller turn off
    if scope in [-2, -3, -4]:       # also reset values
        DLYtype = gv.getindex( gv.cp.get(gv.cfg,"Delay".lower()), DLYtypes, True, False )
        if DLYtype < 0 :
            DLYtype = 0
        #if scope == -3:         # load sample set default
        #    load sample set default
        #else:                   # system default
        DLYsetfb(gv.cp.getfloat(gv.cfg,"DLYfb".lower())*127)
        DLYsetwet(gv.cp.getfloat(gv.cfg,"DLYwet".lower())*127)
        DLYsetdry(gv.cp.getfloat(gv.cfg,"DLYdry".lower())*127)
        DLYsettime((gv.cp.getfloat(gv.cfg,"DLYtime".lower())-1000)/60000*127)
        DLYsetsteep((gv.cp.getfloat(gv.cfg,"DLYsteep".lower())-1)/10*127)
        DLYsetsteplen((gv.cp.getfloat(gv.cfg,"DLYsteplen".lower())-300)/3000*127)
        DLYsetmin((gv.cp.getfloat(gv.cfg,"DLYmin".lower())-5)/20*127)
        DLYsetmax((gv.cp.getfloat(gv.cfg,"DLYmax".lower())-50)/100*127)
    DLYsetType(DLYtype)
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
#   = = =   M O O G   L A D D E R F I L T E R   = = =
#
# Moog lowpass ladderfilter based on algorithm developed by Stefano D'Angelo and Vesa Valimaki
# Code obtained via Dimitri Diakopoulos, https://github.com/ddiakopoulos/MoogLadders
# Filter takes about 9% on PI3
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
    seteffect(MOOG, x)
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
def LFreset(scope=-1):
    LFtype = 0
      # -1 turns of the effect, undefined values cover midi controller turn off
    if scope in [-2, -3, -4]:       # also reset values
        LFtype = gv.getindex( gv.cp.get(gv.cfg,"Moog".lower()), LFtypes, True, False )
        if LFtype < 0 :
            LFtype = 0
        #if scope == -3:         # load sample set default
        #    load sample set default
        #else:                   # system default
        LFsetResonance((gv.cp.getfloat(gv.cfg,"LFresonance".lower())/3.8)*127)
        LFsetCutoff((gv.cp.getfloat(gv.cfg,"LFcutoff".lower())-1000)/10000*127)
        LFsetDrive((gv.cp.getfloat(gv.cfg,"LFdrive".lower())-1)/20*127)
        LFsetLvl(gv.cp.getfloat(gv.cfg,"LFlvl".lower())*127)
        LFsetGain((gv.cp.getfloat(gv.cfg,"LFgain".lower())-1)/10*127)
    LFsetType(LFtype)
gv.setMC(gv.LADDER,LFsetLadder)      # announce to CCmap
gv.setMC(gv.LADDERRES,LFsetResonance)
gv.setMC(gv.LADDERLVL,LFsetLvl)
gv.setMC(gv.LADDERCUTOFF,LFsetCutoff)
gv.setMC(gv.LADDERDRIVE,LFsetDrive)
gv.setMC(gv.LADDERGAIN,LFsetGain)

#
#   = = =   O V E R D R I V E   = = =
#
# Overdrive effect inspired by various discussions
# Overdrive takes about 3.5% on PI3
#
c_filters.odsetboost.argtypes = [c_float]
c_filters.odsetdrive.argtypes = [c_float]
c_filters.odsettone.argtypes = [c_float]
c_filters.odsetwet.argtypes = [c_float]
c_filters.odsetdry.argtypes = [c_float]
ODtypes=["Off","On"]
ODtype=1
def ODsetType(x,*z):
    global ODtype
    ODtype=x
    seteffect(OVERDRIVE, x)
def ODsetOverdrive(*z):
    global ODtype
    if ODtype==1: ODtype=0
    else: ODsetType(1)
ODboost=3000
def ODsetBoost(x,*z):               # 15 - 65
    global ODboost
    ODboost=15.0+x*50/127
    c_filters.odsetboost(ODboost)
ODdrive=3.0
def ODsetDrive(x,*z):               # 1 - 11
    global ODdrive
    ODdrive=1.0+round(x*0.0787)     # =10/127
    c_filters.odsetdrive(ODdrive)
ODtone=0.3
def ODsetTone(x,*z):                # 0 - 100 (actually 0-95)
    global ODtone
    ODtone=x*1.0/1.27
    if ODtone>95.0: ODtone=95.0
    c_filters.odsettone(ODtone/100)
ODmix=1.0
def ODsetMix(x,*z):                 # 0 - 1
    global ODmix
    ODmix=x*1.0/127
    c_filters.odsetwet(ODmix*0.5)   # hardcoded correction of wet, make this adaptable too?
    c_filters.odsetdry(1-ODmix)
def ODreset(scope=-1):
    ODtype =0       # -1 turns of the effect, undefined values cover midi controller turn off
    if scope in [-2, -3, -4]:       # also reset values
        ODtype = gv.getindex( gv.cp.get(gv.cfg,"Overdrive".lower()), ODtypes, True, False )
        if ODtype < 0 :
            ODtype = 0
        #if scope == -3:         # load sample set default
        #    load sample set default
        #else:                   # system default
        ODsetBoost((gv.cp.getfloat(gv.cfg,"ODboost".lower())-15)/50*127)
        ODsetDrive((gv.cp.getfloat(gv.cfg,"ODdrive".lower())-1)/10*127)
        ODsetTone((gv.cp.getfloat(gv.cfg,"ODtone".lower()))*1.27)
        ODsetMix(gv.cp.getfloat(gv.cfg,"ODlvl".lower())*127)
    ODsetType(ODtype)
gv.setMC(gv.OVERDRIVE,ODsetOverdrive)      # announce to CCmap
gv.setMC(gv.ODRVBOOST,ODsetBoost)
gv.setMC(gv.ODRVDRIVE,ODsetDrive)
gv.setMC(gv.ODRVTONE,ODsetTone)
gv.setMC(gv.ODRVMIX,ODsetMix)

#
#   = = =   L I M I T E R   = = =
#
# Peaklimiter based on Simple Compressor class by Citizen Chunk
# https://www.musicdsp.org/en/latest/Effects/204-simple-compressor-class-c.html
# Limiter takes about 4% on PI3
#
c_filters.plsetthresh.argtypes = [c_float]
c_filters.plsetattack.argtypes = [c_float]
c_filters.plsetrelease.argtypes = [c_float]
PLtypes=["Off","On"]
PLtype=0
def PLsetType(x,*z):
    global PLtype
    c_filters.plinit()
    PLtype=x
    seteffect(LIMITER, x)
def LFsetLimiter(*z):
    global PLtype
    if PLtype==1: PLtype=0
    else: PLsetType(1)
PLthresh=90.0
def PLsetThresh(x,*z):              # 70 - 110
    global PLthresh
    PLthresh=70+round(x*0.31496)    # =40/127
    c_filters.plsetthresh(PLthresh)
PLattack=1.0
def PLsetAttack(x,*z):              # 1 - 11
    global PLattack
    PLattack=1.0+round(x*0.0787)    # =10/127
    c_filters.plsetattack(PLattack)
PLrelease=8.0
def PLsetRelease(x,*z):             # 5 - 25
    global PLrelease
    PLrelease=5.0+round(x*0.1575)   # =20/127
    c_filters.plsetrelease(PLrelease)
def PLreset(scope=-1):
    c_filters.plinit()
    PLtype =0       # -1 turns of the effect, undefined values cover midi controller turn off
    if scope in [-2, -3, -4]:       # also reset values
        PLtype = gv.getindex( gv.cp.get(gv.cfg,"Limiter".lower()), PLtypes, True, False )
        if PLtype < 0 :
            PLtype = 0
        #if scope == -3:         # load sample set default
        #    load sample set default
        #else:                   # system default
        PLsetThresh((gv.cp.getfloat(gv.cfg,"PLthresh".lower())-70)/40*127)
        PLsetAttack((gv.cp.getfloat(gv.cfg,"PLattack".lower())-1)/10*127)
        PLsetRelease((gv.cp.getfloat(gv.cfg,"PLrelease".lower())-5)/20*127)
    PLsetType(PLtype)
gv.setMC(gv.LIMITER,LFsetLimiter)      # announce to CCmap
gv.setMC(gv.LIMITTHRESH,PLsetThresh)
gv.setMC(gv.LIMITATTACK,PLsetAttack)
gv.setMC(gv.LIMITRELEASE,PLsetRelease)

#
#   = = =   I N I T I A L I Z E   = = =
#
effects = { REVERB: [5, 0, c_filters.reverb, FVsetType],
            WAH: [3 , 0, c_filters.autowah, PLsetType],
            DELAY: [4 , 0, c_filters.delay, DLYsetType],
            MOOG: [2 , 0, c_filters.moog, LFsetType],
            OVERDRIVE: [1 , 0, c_filters.overdrive, ODsetType],
            LIMITER: [6 , 0, c_filters.limiter, PLsetType]
        }
active = []

ResetAll(-2)
newprocess()
