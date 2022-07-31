#
#  Global variables for samplerbox
#  most variables are defined by the respective procedures
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
#   see docs at  https://homspace.nl/samplerbox
#   changelog in changelist.txt
#

# ################################################################
# Literals connecting external configuration to internal variables
# ################################################################

cfg = "config"
CONFIG_LOC  =  "config/"
SAMPLESDEF = "definition.txt"
CTRLMAP_DEF = "CCmap.csv"
NOTEMAP_DEF = "notemap.csv"
VOICEMAP_DEF = "MTchannelmap.csv"
FXPRESETS_DEF = "FXpresets.csv"
LAYERS_DEF = "layers.csv"
FIXED = "Fixed"
VOICES = "Voices"
NOTEMAPS = "Notemaps"
FXPRESETS = "FXpresets"
BACKTRACKS = "BackTracks"
SMFS = "SMFs"
SMFTEMPO = "SMFtempo"
SMFLOOP = "SMFloop"
SMFSTOP = "SMFstop"
SMFRECSTART = "SMFrecstart"
SMFRECABORT = "SMFreccancel"
SMFRECSAVE = "SMFrecsave"
MENU_INCR = "Menu_Incr"
MENU_DECR = "Menu_Decr"
MENU_SEL = "Menu_Sel"
MENU_RET = "Menu_Ret"
AUTOCHORD = "AutoChord"
CHORDS = "Chords"
SCALES = "Scales"
AUTOCHORDOFF = "AutoChordOff"
PITCHWHEEL = "PitchWheel"
PROGUP = "ProgramUp"
PROGDN = "ProgramDown"
VOLUME = "Volume"
SUSTAIN = "Sustain"
# DSP effects start here
DAMP = "Damp"
DAMPNEW = "DampNew"
DAMPLAST = "DampLast"
REVERB = "Reverb"
REVERBLVL = "ReverbLvl"
REVERBROOM = "ReverbRoom"
REVERBDAMP = "ReverbDamp"
REVERBWIDTH = "ReverbWidth"
AUTOWAH = "Wah"
AUTOWAHTYPE = "WahType"
AUTOWAHENV = "EnvelopeWah"
AUTOWAHLFO = "LFOwah"
AUTOWAHMAN = "ManualWah"
AUTOWAHLVL = "WahLvl"
AUTOWAHMIN = "WahMin"
AUTOWAHMAX = "WahMax"
AUTOWAHQ = "WahQ"
AUTOWAHATTACK = "WahAttack"
AUTOWAHRELEASE = "WahRelease"
AUTOWAHSPEED = "WahSpeed"
AUTOWAHLVLRNGE = "WahLvlRange"
AUTOWAHPEDAL = "WahPedal"
DELAY = "Delay"
DELAYTYPE = "DelayType"
ECHO = "Echo"
FLANGER = "Flanger"
DELAYFB = "DelayFeedbackVol"
DELAYFW = "DelayWet"
DELAYMIX = "DelayDry"
DELAYTIME = "DelayTime"
DELAYSTEEP = "DelaySteep"
DELAYSTEPLEN = "DelaySteplen"
DELAYMIN = "DelayMin"
DELAYMAX = "DelayMax"
LADDER = "Moog"
LADDERLVL = "MoogLvl"
LADDERRES = "MoogResonance"
LADDERCUTOFF = "MoogCutoff"
LADDERDRIVE = "MoogDrive"
LADDERGAIN = "MoogGain"
OVERDRIVE = "Overdrive"
ODRVBOOST = "OverdriveBoost"
ODRVDRIVE = "OverdriveDrive"
ODRVTONE = "OverdriveTone"
ODRVMIX = "OverdriveLvl"
LIMITER = "Limiter"
LIMITTHRESH = "LimitThreshold"
LIMITATTACK = "LimitAttack"
LIMITRELEASE = "LimitRelease"
DSPPRIOTAB = "DSPpriority"
# DSP effects end here
PITCHSENS = "PitchSens"
LFO = "Oscillate"
LFOTYPE = "LFOtype"
VIBRATO = "Vibrato"
TREMOLO = "Tremolo"
PANNING = "Panning"
ROTATE = "Rotate"
PANWIDTH = "PanWidth"
PANSPEED = "PanSpeed"
TREMDEPTH = "TremDepth"
TREMSPEED = "TremSpeed"
TREMTRILL = "TremTrill"
VIBRDEPTH = "VibrDepth"
VIBRSPEED = "VibrSpeed"
VIBRTRILL = "VibrTrill"
LFOSPEED = "LFOspeed"
CHORUS = "Chorus"
CHORUSDEPTH = "ChorusDepth"
CHORUSGAIN = "ChorusGain"
EFFECTSOFF = "EffectsOff"
PANIC = "Panic"
ARP = "Arpeggiator"
ARPTEMPO = "ArpTime"
ARPSUSTAIN = "ArpSustain"
ARPUP = "ArpUp"
ARPDOWN = "ArpDown"
ARPUPDOWN = "ArpUpDown"
ARPRANDOM = "ArpRandom"
ARPRNDLIN = "ArpRndLin"
ARPFADE = "ArpFadeout"
ARPLOOP = "ArpLoop"
ARP2END = "ArpPlay2end"
AFTERTOUCH = "Aftertouch"
CHAFTOUCH = "ChannelAfterTouch"
CHAFREVERS = "chafReverse"
PAFTOUCH = "PolyAfterTouch"
PAFREVERS = "pafReverse"
PAFVOLUME = "pafVolume"
PAFPITCH = "pafPitchBend"
PAFPITCHRANGE = "pafPitchRange"
PAFPAN = "pafPan"
PAFPANWIDTH = "pafPanWidth"
PAFCHOKE = "pafChoke"
UA = "UA"

# #########################################################
# Internal variables
# #########################################################

ConfigErr = False
LEDblink = False
USE_ALSA_MIXER = False
BTNOTES = 130 	# Backtracknotes start
MTCHNOTES = 1024 # Multitimbral channel notes start:
                # so this leaves <1024 for main keyboard notes,
                # and next available is 17408 (theoretically)
ActuallyLoading = False
basename = "None"
DefinitionTxt = ""
DefinitionErr = ""
samplesdir = ""
samples = {}
playingnotes = {}
sustainplayingnotes = []
triggernotes = []
playingsounds = []
presetlist = []
btracklist = []
voicelist = []
currvoice = 1
currchord = 0   # single note, "normal play"
currscale = 0   # single note sequences, "normal play"
last_musicnote = -1
last_midinote = -1
midi_mute = False
globalgain = 1	# the input volume correction, change per set in definition.txt
PITCHBEND = 0
PANCORR  =  10
controllerCCs = []
CCmap = []
CCmapSet = []
CCmapBox = []
keynames = []
drumpadmap = []
notemap = []
notemaps = []
currnotemap = ""
notemapping = []
MidiRecorder = False

# #########################################################
# MidiControl(ler)s handling (core function, so not via UI)
# #########################################################

MCdevices = {
	 0 : 'button/(foot)switch', # NOTES_CC is special
	-1 : 'pot/bar/pedal',
	-2 : 'key-aftertouch',
	-3 : 'no midi controller'
	}
MCmodes = {	# pointer MCdevices and pointer to modename
	'continuous'	: [-1, 0],
	'toggle'		: [ 0, 1],
	'switch'		: [ 0, 2],
	'switchon'		: [ 0, 3],
	'switchoff'		: [ 0, 4],
	'paftouch'  	: [-2, 5],
	'nocontroller'  : [-3, 6]
	}
MCmodenames = [
	"Continuous",
	"Toggle",
	"Switch",
	"SwitchOn",
	"SwitchOff",
	"pAftouch",
	"NoController"
	]
MCtypes = {	# pointer to the MCdevices supporting the type
	0 : -1,
	1 :  0,
	2 :  0,
	3 : -1,
	4 : -2,
	5 : -3
    }

def safeguard (*vals):  # dedicated proc for debugging MC-table
	arr = []
	for val in vals :
		arr.append(val)
	print("gv.Safeguard: call to unset procedure for %s:%s" %(arr[1],arr[0]))
def nomidicontrol(*vals):
	safeguard(vals)
def setMC( mc, proc ):
	for x in range( len(MC) ):
		if mc == MC[x][0]:
			break
	if x < len(MC):
		MC[x][2] = proc
	else:
		print("gv.setMC: Can't set %s" %mc)
	return x

MC = [	# [name,type,procedure,familyindex,MCmodenameindex] where type can be
		#   - 0= continuous
		#   - 1= toggle (switches a value)
		#   - 2= select table value
		#   - 3= 2 range values switch (a special continuous)
		#   - 4= polyphonic (key-specific) aftertouch
		#   - 5= not for MidiControl
		# FamilyIndex is added icw controls.csv & supported names,
		# MCmodenameIndex is added in same getcsv.controls() routine.
	[PROGUP,1,safeguard],
	[PROGDN,1,safeguard],
	[PITCHWHEEL,0,safeguard],
	[PITCHSENS,0,safeguard],
	[VOLUME,0,safeguard],
	[SUSTAIN,3,safeguard],
	[DAMP,3,safeguard],
	[DAMPNEW,3,safeguard],
	[DAMPLAST,3,safeguard],
	[LFOTYPE,5,nomidicontrol],
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
	[AUTOWAHTYPE,5,nomidicontrol],
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
	[DELAYTYPE,5,nomidicontrol],
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
	[OVERDRIVE,1,safeguard],
	[ODRVBOOST,0,safeguard],
	[ODRVDRIVE,0,safeguard],
	[ODRVTONE,0,safeguard],
	[ODRVMIX,0,safeguard],
	[LIMITER,1,safeguard],
	[LIMITTHRESH,0,safeguard],
	[LIMITATTACK,0,safeguard],
	[LIMITRELEASE,0,safeguard],
	[ARP,1,safeguard],
	[ARPUP,1,safeguard],
	[ARPDOWN,1,safeguard],
	[ARPRANDOM,1,safeguard],
	[ARPUPDOWN,1,safeguard],
	[ARPRNDLIN,1,safeguard],
	[ARPTEMPO,0,safeguard],
	[ARPSUSTAIN,0,safeguard],
	[ARPFADE,0,safeguard],
	[ARPLOOP,1,safeguard],
	[ARP2END,1,safeguard],
	[EFFECTSOFF,1,safeguard],
	[PANIC,1,safeguard],
	[AUTOCHORDOFF,1,safeguard],
	[CHORDS,2,safeguard],
	[SCALES,2,safeguard],
	[VOICES,2,safeguard],
	[BACKTRACKS,2,safeguard],
	[SMFS,2,safeguard],
	[SMFLOOP,1,safeguard],
	[SMFSTOP,1,safeguard],
	[SMFTEMPO,0,safeguard],
	[SMFRECSTART,1,safeguard],
	[SMFRECABORT,1,safeguard],
	[SMFRECSAVE,1,safeguard],
	[MENU_INCR,1,safeguard],
	[MENU_DECR,1,safeguard],
	[MENU_SEL,1,safeguard],
	[MENU_RET,1,safeguard],
	[NOTEMAPS,2,safeguard],
	[FXPRESETS,2,safeguard],
	[CHAFREVERS,1,safeguard],
	[PAFREVERS,1,safeguard],
	[PAFVOLUME,4,safeguard],
	[PAFPITCH,4,safeguard],
	[PAFPITCHRANGE,0,safeguard],
	[PAFPAN,4,safeguard],
	[PAFPANWIDTH,0,safeguard],
	[PAFCHOKE,4,safeguard]
]
