#
#  Global variables for samplerbox
#  most variables are defined by the respective procedures
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
#   see docs at  http://homspace.xs4all.nl/homspace/samplerbox
#   changelog in changelist.txt
#

# Literals
cfg="config"
SAMPLESDEF="definition.txt"
CTRLMAP_DEF="CCmap.csv"
NOTEMAP_DEF="notemap.csv"
HTTP_ROOT="webgui"
FIXED="Fixed"
VOICES="Voices"
NOTEMAPS="Notemaps"
BACKTRACKS="BackTracks"
CHORDS="Chords"
SCALES="Scales"
PITCHWHEEL="PitchWheel"
MODWHEEL="ModWheel"
PROGUP="ProgramUp"
PROGDN="ProgramDown"
VOLUME="Volume"
SUSTAIN="Sustain"
DAMP="Damp"
DAMPNEW="DampNew"
DAMPLAST="DampLast"
REVERB="Reverb"
REVERBLVL="ReverbLvl"
REVERBROOM="ReverbRoom"
REVERBDAMP="ReverbDamp"
REVERBWIDTH="ReverbWidth"
AUTOWAHENV="EnvelopeWah"
AUTOWAHLFO="LFOwah"
AUTOWAHMAN="ManualWah"
AUTOWAHLVL="WahLvl"
AUTOWAHMIN="WahMin"
AUTOWAHMAX="WahMax"
AUTOWAHQ="WahQ"
AUTOWAHATTACK="WahAttack"
AUTOWAHRELEASE="WahRelease"
AUTOWAHSPEED="WahSpeed"
AUTOWAHLVLRNGE="WahLvlRange"
AUTOWAHPEDAL="WahPedal"
ECHO="Echo"
FLANGER="Flanger"
DELAYFB="DelayFeedbackVol"
DELAYFW="DelayWet"
DELAYMIX="DelayDry"
DELAYTIME="DelayTime"
DELAYSTEEP="DelaySteep"
DELAYSTEPLEN="DelaySteplen"
DELAYMIN="DelayMin"
DELAYMAX="DelayMax"
LADDER="Moog"
LADDERLVL="MoogLvl"
LADDERRES="MoogResonance"
LADDERCUTOFF="MoogCutoff"
LADDERDRIVE="MoogDrive"
LADDERGAIN="MoogGain"
PITCHSENS="PitchSens"
VIBRATO="Vibrato"
TREMOLO="Tremolo"
PANNING="Panning"
ROTATE="Rotate"
PANWIDTH="PanWidth"
PANSPEED="PanSpeed"
TREMDEPTH="TremDepth"
TREMSPEED="TremSpeed"
TREMTRILL="TremTrill"
VIBRDEPTH="VibrDepth"
VIBRSPEED="VibrSpeed"
VIBRTRILL="VibrTrill"
LFOSPEED="LFOspeed"
CHORUS="Chorus"
CHORUSDEPTH="ChorusDepth"
CHORUSGAIN="ChorusGain"
EFFECTSOFF="EffectsOff"
AUTOCHORDOFF="AutoChordOff"
PANIC="Panic"
ARP="Arpeggiator"
ARPTEMPO="ArpTime"
ARPSUSTAIN="ArpSustain"
ARPUP="ArpUp"
ARPDOWN="ArpDown"
ARPUPDOWN="ArpUpDown"
ARPRANDOM="ArpRandom"
ARPRNDLIN="ArpRndLin"
ARPFADE="ArpFadeout"
ARPLOOP="ArpLoop"
ARP2END="ArpPlay2end"
UA="UA"

# Internal vars
ConfigErr=False
LEDblink=False
buttfunc=0
button_disp=[""]
ActuallyLoading=False
basename="None"
DefinitionTxt=""
DefinitionErr=""
samplesdir=""
samples={}
playingnotes={}
sustainplayingnotes=[]
triggernotes=[]
playingsounds=[]
presetlist=[]
btracklist=[]
voicelist=[]
currvoice=1
currchord=0         # single note, "normal play"
currscale=0         # single note sequences, "normal play"
currfilter=0
last_musicnote=-1
last_midinote=-1
midi_mute=False
globalgain=1        # the input volume correction, change per set in definition.txt
stop127=0
sample_mode=""
PITCHBEND=0
pitchnotes=0
pitchneutral=0
pitchdiv=0
chordname=[]
chordnote=[]
scalesymbol=[]
scalename=[]
scalechord=[]
controllerCCs=[]
CCmap=[]
CCmapSet=[]
CCmapBox=[]
keynames=[]
drumpadmap=[]
drumpad=False
notemap=[]
notemaps=[]
currnotemap=""
notemapping=[]
SB_nm_inote=-1
SB_nm_onote=None
SB_nm_Q=None
SB_nm_retune=None
SB_nm_voice=None
SB_nm_map=None
SB_nm_actmap="%$@"

def NoProc(*vals):      # Dummy
    pass
def safeguard (*vals):  # dedicated proc for MC-table
    arr=[]
    for val in vals :
        arr.append(val)
    print "gv.Safeguard: call to unset procedure for %s:%s" %(arr[1],arr[0])
def setMC(mc,proc):
    MC[getindex(mc,MC)][2]=proc
MC=[              # name, type(0=continuous,1=switch,2=switchtable,3=2valswitch),procedure)
[PROGUP,1,safeguard],
[PROGDN,1,safeguard],
[PITCHWHEEL,0,safeguard],
[PITCHSENS,0,safeguard],
[MODWHEEL,0,safeguard],
[VOLUME,0,safeguard],
[SUSTAIN,3,safeguard],
[DAMP,3,safeguard],
[DAMPNEW,3,safeguard],
[DAMPLAST,3,safeguard],
[ROTATE,1,safeguard],
[VIBRATO,1,safeguard],
[TREMOLO,1,safeguard],
[PANNING,1,safeguard],
[LFOSPEED,0,safeguard],
[TREMDEPTH,0,safeguard],
[TREMSPEED,0,safeguard],
[TREMTRILL,0,safeguard],
[VIBRDEPTH,0,safeguard],
[VIBRSPEED,0,safeguard],
[VIBRTRILL,0,safeguard],
[PANWIDTH,0,safeguard],
[PANSPEED,0,safeguard],
[CHORUS,1,safeguard],
[CHORUSDEPTH,0,safeguard],
[CHORUSGAIN,0,safeguard],
[REVERB,1,safeguard],
[REVERBLVL,0,safeguard], 
[REVERBROOM,0,safeguard],
[REVERBDAMP,0,safeguard],
[REVERBWIDTH,0,safeguard],
[AUTOWAHENV,1,safeguard],
[AUTOWAHLFO,1,safeguard],
[AUTOWAHMAN,1,safeguard],
[AUTOWAHLVL,0,safeguard],
[AUTOWAHMIN,0,safeguard],
[AUTOWAHMAX,0,safeguard],
[AUTOWAHQ,0,safeguard],
[AUTOWAHATTACK,0,safeguard],
[AUTOWAHRELEASE,0,safeguard],
[AUTOWAHSPEED,0,safeguard],
[AUTOWAHLVLRNGE,0,safeguard],
[AUTOWAHPEDAL,0,safeguard],
[ECHO,1,safeguard],
[FLANGER,1,safeguard],
[DELAYFB,0,safeguard],
[DELAYFW,0,safeguard],
[DELAYMIX,0,safeguard],
[DELAYTIME,0,safeguard],
[DELAYSTEEP,0,safeguard],
[DELAYSTEPLEN,0,safeguard],
[DELAYMIN,0,safeguard],
[DELAYMAX,0,safeguard],
[LADDER,1,safeguard],
[LADDERLVL,0,safeguard],
[LADDERRES,0,safeguard],
[LADDERCUTOFF,0,safeguard],
[LADDERDRIVE,0,safeguard],
[LADDERGAIN,0,safeguard],
[ARP,1,safeguard],
[ARPUP,1,safeguard],
[ARPDOWN,1,safeguard],
[ARPRANDOM,1,safeguard],
[ARPUPDOWN,1,safeguard],
[ARPRNDLIN,1,safeguard],
[ARPTEMPO,0,safeguard],
[ARPSUSTAIN,0,safeguard],
[ARPFADE,0,safeguard],
[ARPLOOP,0,safeguard],
[ARP2END,0,safeguard],
[EFFECTSOFF,1,safeguard],
[PANIC,1,safeguard],
[AUTOCHORDOFF,1,safeguard],
[CHORDS,2,safeguard],
[SCALES,2,safeguard],
[VOICES,2,safeguard],
[BACKTRACKS,2,safeguard],
[NOTEMAPS,2,safeguard]
]
