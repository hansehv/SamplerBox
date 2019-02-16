#
#  Global variables for samplerbox
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
#   see docs at  http://homspace.xs4all.nl/homspace/samplerbox
#   changelog in changelist.txt
#

# Loaded from configuration.txt
AUDIO_DEVICE_ID=0
USE_ALSA_MIXER=False
MIDI_CHANNEL=1
PRESET=0
PRESETBASE=0
BOXTREMspeed=0
volume=0
volumeCC=0
#globaltranspose=0   # to be deleted, obsoleted by transpose on sample level

# Literals
SAMPLESDEF="definition.txt"
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
REVERBLVL="ReverbLvl"
REVERBROOM="ReverbRoom"
REVERBDAMP="ReverbDamp"
REVERBWIDTH="ReverbWidth"
REVERB="Reverb"
PITCHSENS="PitchSens"
VIBRATO="Vibrato"
TREMOLO="Tremolo"
ROTATE="Rotate"
TREMDEPTH="TremDepth"
TREMSPEED="TremSpeed"
VIBRDEPTH="VibrDepth"
VIBRSPEED="VibrSpeed"
LFOSPEED="LFOspeed"
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
sustain=False       # only in midicallback
damp=False          # only in midicallback
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
FVroomsize=0
FVdamp=0
FVlevel=0
FVwidth=0
VIBRpitch=0
VIBRspeed=0
VIBRvalue=0         # Value 0 gives original note
VIBRtrill=0
TREMampl=0
TREMspeed=0
TREMvalue=1.0       # Full volume
TREMtrill=0
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
notemap=[]
notemaps=[]
currnotemap=""

# Pointers to recursive/cross-used procs and related vars
# All initialized in main script
getindex=None
notename2midinote=None
setVoice=None
display=None
cp=None
FVsetlevel=None
FVsetroomsize=None
FVsetdamp=None
FVsetwidth=None
FVinit=None
Filters=None
FilterTidy=None
Filterkeys=None
filterproc=None
setFilter=None
MidiCallback=None
setvolume=None
LoadSamples=None

def safeguard (*vals):  # dedicated proc for MC-table
    arr=[]
    for val in vals :
        arr.append(val)
    print "gv.Safeguard: call to unset procedure for %s:%s" %(arr[1],arr[0])
MC=[              # name, type(0=continuous,1=switch,2=switchtable,3=2valswitch),procedure)
[PROGUP,1,safeguard],
[PROGDN,1,safeguard],
[PITCHWHEEL,0,safeguard],
[MODWHEEL,0,safeguard],
[VOLUME,0,safeguard],
[SUSTAIN,3,safeguard],
[DAMP,3,safeguard],
[DAMPNEW,3,safeguard],
[DAMPLAST,3,safeguard],
[REVERBLVL,0,safeguard], 
[REVERBROOM,0,safeguard],
[REVERBDAMP,0,safeguard],
[REVERBWIDTH,0,safeguard],
[TREMDEPTH,0,safeguard],
[TREMSPEED,0,safeguard],
[VIBRDEPTH,0,safeguard],
[VIBRSPEED,0,safeguard],
[LFOSPEED,0,safeguard],
[PITCHSENS,0,safeguard],
[REVERB,1,safeguard],
[TREMOLO,1,safeguard],
[VIBRATO,1,safeguard],
[ROTATE,1,safeguard],
[EFFECTSOFF,1,safeguard],
[AUTOCHORDOFF,1,safeguard],
[PANIC,1,safeguard],
[VOICES,2,safeguard],
[NOTEMAPS,2,safeguard],
[BACKTRACKS,2,safeguard],
[CHORDS,2,safeguard],
[SCALES,2,safeguard],
[ARP,1,safeguard],
[ARPTEMPO,0,safeguard],
[ARPSUSTAIN,0,safeguard],
[ARPUP,1,safeguard],
[ARPDOWN,1,safeguard],
[ARPUPDOWN,1,safeguard],
[ARPRANDOM,1,safeguard],
[ARPRNDLIN,1,safeguard],
[ARPFADE,0,safeguard]
]
