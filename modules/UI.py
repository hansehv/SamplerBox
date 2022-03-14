###############################################################
#
#   Provide an interface/API for user-interface related modules
#
#   The dictionary at the bottom explains the calling specifications
#   of the fields for user interaction, followed by some extra
#   control functions needing no user interaction.
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
#   see docs at https://homspace.nl/samplerbox
#   changelog in changelist.txt
#
###############################################################

import re
import gv,gp,remap,arp,chorus,Cpp,LFO,network
if gv.AFTERTOUCH:
	import AfterTouch
import menu as butmenu

# Writable variables

def RenewMedia(val=None):					# boolean, return value True indicates "preset load in progress",
	try:									# setting optional input to any value except False or "n*" forces a reload of same sample set
		if val and str(val)[0].upper()!="N":	# using yes/no is also allowed :-)
			gv.basename="None"				# start from scratch
			gv.LoadSamples()            	# perform the loading
		return gv.ActuallyLoading
	except:
		return True
def Preset(val=None):						# 0-127
	try:
		if val!=None:
			if val>=0 and val<=127:
				if gv.PRESET!=val:
					if gp.getindex(val,gv.presetlist)>-1:
						gv.PRESET=val
						gv.LoadSamples()
					#else: print ("Preset %d does not exist, ignored" %val)
				#else: print ("Preset %d already loaded" %val)
			return gv.ActuallyLoading
		return gv.PRESET
	except:
		return 0
def DefinitionTxt(val=None):				# contains definition.txt
	try:
		if val!=None:
			if gv.DefinitionTxt != val:
				gv.DefinitionTxt = val
				fname=gv.samplesdir+gv.presetlist[gp.getindex(gv.PRESET,gv.presetlist)][1]+"/"+gv.SAMPLESDEF
				gp.samples2write()
				with open(fname,'w') as definitionfile: definitionfile.write(gv.DefinitionTxt)
				gp.samples2read()
				gv.basename="None"         	# do a renew to sync the update
				gv.LoadSamples()
			return gv.ActuallyLoading
		return gv.DefinitionTxt
	except:
		return "** Error **"
def Voice(val=None):						# index of Voicelist (or actual "voice#" if not numeric)
	try:
		currvoice=gv.currvoice
		if val!=None:
			if isinstance(val,int):
				for voice in gv.voicelist:      	# count effects track and release samples
					if voice[0]<1: val+=1
				gv.setVoice(gv.voicelist[val][0],1)
			else:
				gv.setVoice(int(re.search(r'\d+', val).group()),0)
			return currvoice!=gv.currvoice
		return gv.currvoice
	except: return 0
def FXpreset(val=None):						# active effects preset, name in FXpresets
	try:
		if val!=None:
			gp.setFXpresets(val)
		return gv.FXpreset_last
	except:
		return "None"

def Notemap(val=None):						# active notemap, either index in notemap or "notemap name"
	try:
		if val!=None:
			currnotemap=gv.currnotemap
			newnotemap=""
			if isinstance(val, int):
				newnotemap=gv.notemaps[val-1] if val>0 	else ""
			else:
				if val in gv.notemaps: newnotemap=val
			mapchange=(currnotemap!=newnotemap)
			if mapchange:
				gv.setNotemap(val)
				remap.nm_inote=-1			# restart the mapping circus when underlying table shifted
			return mapchange
		return gv.currnotemap
	except:
		return ""
nm_inote=remap.notes_inote
nm_Q=remap.notes_Q
nm_unote=remap.notes_unote
nm_onote=remap.notes_onote
nm_retune=remap.notes_retune
nm_voice=remap.notes_voice
nm_map=remap.notes_map
nm_clr=remap.notes_clear
nm_sav=remap.notes_sav

def Scale(val=None):						# index of ScaleName
	try:
		if val!=None:
			if not isinstance(val,int):
				if val=="Note":
					val=0 
				else:
					val=gp.getindex(val,gv.scalename,True)
					if val<0:
						val=gv.currscale
			if gv.currscale!=val:
				gv.currscale=val
				gv.currchord=0
		return gv.currscale
	except:
		return 0
def Chord(val=None):						# index of Chordname
	try:
		if val!=None:
			if not isinstance(val,int):
				if val=="Note":
					val=0 
				else:
					val=gp.getindex(val,gv.chordname,True)
					if val<0:
						val=gv.currchord
			if gv.currchord!=val:
				gv.currchord=val
				gv.currscale=0
		return gv.currchord
	except:
		return 0
def SoundVolume(val=None):					# 0-100 in steps of roughly 10 (logarithmatic scale)
	try:
		if val!=None:
			if val>=0 and val<=100:
				gv.setvolume(val)
		return 0.99+gv.volume
	except:
		return 0
def MidiVolume(val=None):					# 0-100
	try:
		if val!=None:
			if val>=0 and val<=100:
				gv.volumeCC=float(val)/100
		return int(gv.volumeCC*100)
	except:
		return 0
def Gain(val=None):							# 0-300 (100 is neutral)
	try:
		if val!=None:
			if val>=0 and val<=300:
				gv.globalgain=float(val)/100
		return gv.globalgain*100
	except:
		return 0

def Pitchrange(val=None):					# 0-12 (so max 1 octave up & down)
	try:
		if val!=None:
			if val>=0 and val<=12:
				gv.pitchnotes=val*2			# make it up&down
		return gv.pitchnotes/2
	except: return 12

def FVtype(val=None):						# value in FVtypes
	try:
		if val!=None:
			if isinstance(val,int): Cpp.FVsetType(val)
			else: Cpp.FVsetType(gp.getindex(val,Cpp.FVtypes,True))
		return Cpp.FVtype
	except:
		return 0
def FVroomsize(val=None):					# 0-100
	try:
		if val!=None:
			if val>=0 and val<=100:
				Cpp.FVsetroomsize(1.27*val)
		return Cpp.FVroomsize*100
	except:
		return 0
def FVdamp(val=None):						# 0-100
	try:
		if val!=None:
			if val>=0 and val<=100:
				Cpp.FVsetdamp(1.27*val)
		return Cpp.FVdamp*100
	except:
		return 0
def FVlevel(val=None):						# 0-100
	try:
		if val!=None:
			if val>=0 and val<=100:
				Cpp.FVsetlevel(1.27*val)
		return Cpp.FVlevel*100
	except:
		return 0
def FVwidth(val=None):						# 0-100
	try:
		if val!=None:
			if val>=0 and val<=100:
				Cpp.FVsetwidth(1.27*val)
		return Cpp.FVwidth*100
	except:
		return 0

def AWtype(val=None):						# value in AWtypes
	try:
		if val!=None:
			if isinstance(val,int): Cpp.AWsetType(val)
			else: Cpp.AWsetType(gp.getindex(val,Cpp.AWtypes,True))
		return Cpp.AWtype
	except:
		return 0
def AWmixing(val=None):						# 0-100
	try:
		if val!=None:
			if val>=0 and val<=100:
				Cpp.AWsetMixing(1.27*val)
		return Cpp.AWmixing*100
	except:
		return 0
def AWattack(val=None):						# 0-500
	try:
		if val!=None:
			if val>=0 and val<=500:
				Cpp.AWsetAttack(0.254*val)
		return Cpp.AWattack*1000
	except:
		return 0
def AWrelease(val=None):					# 0-500
	try:
		if val!=None:
			if val>=0 and val<=500:
				Cpp.AWsetRelease(0.254*val)
		return Cpp.AWrelease*10000
	except:
		return 0
def AWminfreq(val=None):					# 20-500
	try:
		if val!=None:
			if val>=20 and val<=500:
				Cpp.AWsetMinFreq(0.254*val)
		return Cpp.AWminfreq
	except:
		return 20
def AWmaxfreq(val=None):					# 1000-10000
	try:
		if val!=None:
			if val>=1000 and val<=10000:
				Cpp.AWsetMaxFreq(0.0127*val)
		return Cpp.AWmaxfreq
	except:
		return 1000
def AWqfactor(val=None):					# 0-100
	try:
		if val!=None:
			if val>=0 and val<=100:
				Cpp.AWsetQualityFactor(1.27*val)
		return Cpp.AWqfactor*10
	except:
		return 0
def AWspeed(val=None):						# 100-1100
	try:
		if val!=None:
			if val>=100 and val<=1100:
				Cpp.AWsetSpeed(0.127*(val-100))
		return Cpp.AWspeed
	except:
		return 100
def AWlvlrange(val=None):					# 0-100
	try:
		if val!=None:
			if val>=0 and val<=100:
				Cpp.AWsetLVLrange(1.27*val)
		return Cpp.AWlvlrange
	except:
		return 0

def DLYtype(val=None):						# value in DLYtypes
	try:
		if val!=None:
			if isinstance(val,int): Cpp.DLYsetType(val)
			else: Cpp.DLYsetType(gp.getindex(val,Cpp.DLYtypes,True))
		return Cpp.DLYtype
	except:
		return 0
def DLYfb(val=None):						# 0-100
	try:
		if val!=None:
			if val>=0 and val<=100:
				Cpp.DLYsetfb(1.27*val)
		return Cpp.DLYfb*100
	except:
		return 0
def DLYwet(val=None):						# 0-100
	try:
		if val!=None:
			if val>=0 and val<=100:
				Cpp.DLYsetwet(1.27*val)
		return Cpp.DLYwet*100
	except:
		return 0
def DLYdry(val=None):						# 0-100
	try:
		if val!=None:
			if val>=0 and val<=100:
				Cpp.DLYsetdry(1.27*val)
		return Cpp.DLYdry*100
	except:
		return 0
def DLYtime(val=None):						# 1000-61000
	try:
		if val!=None:
			if val>=1000 and val<=61000:
				Cpp.DLYsettime(1.27*(val-1000)/600)
		return Cpp.DLYtime
	except:
		return 0
def DLYsteep(val=None):						# 1-11
	try:
		if val!=None:
			if val>=1 and val<=11:
				Cpp.DLYsetsteep(12.7*(val-1))
		return Cpp.DLYsteep
	except:
		return 1
def DLYsteplen(val=None):					# 300-3300
	try:
		if val!=None:
			if val>=300 and val<=3300:
				Cpp.DLYsetsteplen(1.27*(val-300)/30)
		return Cpp.DLYsteplen
	except:
		return 300
def DLYmin(val=None):						# 5-25
	try:
		if val!=None:
			if val>=5 and val<=25:
				Cpp.DLYsetmin(5.36*(val-5))
		return Cpp.DLYmin
	except:
		return 5
def DLYmax(val=None):						# 50-150
	try:
		if val!=None:
			if val>=50 and val<=150:
				Cpp.DLYsetmax(1.27*(val-50))
		return Cpp.DLYmax
	except:
		return 50

def LFtype(val=None):						# value in LFtypes
	try:
		if val!=None:
			if isinstance(val,int): Cpp.LFsetType(val)
			else: Cpp.LFsetType(gp.getindex(val,Cpp.LFtypes,True))
		return Cpp.LFtype
	except: return 0
def LFresonance(val=None):					# 0-38
	try:
		if val!=None:
			if val>=0 and val<=38:
				Cpp.LFsetResonance(127*val/38)
		return Cpp.LFresonance*10
	except:
		return 0
def LFcutoff(val=None):						# 1000-11000
	try:
		if val!=None:
			if val>=1000 and val<=11000:
				Cpp.LFsetCutoff(1.27*(val-1000)/100)
		return Cpp.LFcutoff
	except:
		return 1000
def LFdrive(val=None):						# 1-20
	try:
		if val!=None:
			if val>=1 and val<=20:
				Cpp.LFsetDrive((val-1)*6.35) 	# =/20.0*127)
		return Cpp.LFdrive
	except:
		return 1
def LFlvl(val=None):						# 0-100
	try:
		if val!=None:
			if val>=0 and val<=100:
				Cpp.LFsetLvl(1.27*val)
		return Cpp.LFlvl*100
	except:
		return 0
def LFgain(val=None):						# 10-110, Carefully test before using values above 50
	try:
		if val!=None:
			if val>=10 and val<=110:
				Cpp.LFsetGain(1.27*(val-10))
		return Cpp.LFgain*10
	except:
		return 10

def ODtype(val=None):						# value in ODtypes
	try:
		if val!=None:
			if isinstance(val,int): Cpp.ODsetType(val)
			else: Cpp.ODsetType(gp.getindex(val,Cpp.ODtypes,True))
		return Cpp.ODtype
	except:
		return 0
def ODboost(val=None):						# 15-65
	try:
		if val!=None:
			if val>=15 and val<=65:
				Cpp.ODsetBoost(127*(val-15)/50)
		return Cpp.ODboost
	except:
		return 30
def ODdrive(val=None):						# 1-11
	try:
		if val!=None:
			if val>=1 and val<=11:
				Cpp.ODsetDrive((val-1)*12.7)
		return Cpp.ODdrive
	except:
		return 0
def ODtone(val=None):						# 0-95 (accepts up to 100)
	try:
		if val!=None:
			if val>=0 and val<=100:
				Cpp.ODsetTone(val*1.27)
		return Cpp.ODtone
	except:
		return 1
def ODmix(val=None):						# 0-10
	try:
		if val!=None:
			if val>=0 and val<=10:
				Cpp.ODsetMix(val*12.7)
		return Cpp.ODmix*10
	except:
		return 1

def PLtype(val=None):						# value in PLtypes
	try:
		if val!=None:
			if isinstance(val,int): Cpp.PLsetType(val)
			else: Cpp.PLsetType(gp.getindex(val,Cpp.PLtypes,True))
		return Cpp.PLtype
	except:
		return 0
def PLthresh(val=None):						# 70-110
	try:
		if val!=None:
			if val>=70 and val<=110:
				Cpp.PLsetThresh(127*(val-70)/40)
		return Cpp.PLthresh
	except:
		return 0
def PLattack(val=None):						# 1-11
	try:
		if val!=None:
			if val>=1 and val<=11:
				Cpp.PLsetAttack((val-1)*12.7)
		return Cpp.PLattack
	except:
		return 1
def PLrelease(val=None):					# 1-11
	try:
		if val!=None:
			if val>=5 and val<=25:
				Cpp.PLsetRelease((val-5)*6.35)
		return Cpp.PLrelease
	except:
		return 8

def LFOtype(val=None):						# value in LFOtypes
	try:
		if val!=None:
			if isinstance(val,int): LFO.setType(val)
			else: LFO.setType(gp.getindex(val,LFO.effects,True))
		return LFO.effect
	except:
		return 0
def VIBRpitch(val=None):					# 1-64
	try:
		if val!=None:
			if val>=1 and val<=64:
				LFO.VIBRpitch=1.0*val/16
		return LFO.VIBRpitch*16
	except:
		return 0
def VIBRspeed(val=None):					# 1-32	
	try:
		if val!=None:
			if val>=1 and val<=32:
				LFO.VibrSetspeed(val*4)
		return LFO.VIBRspeed	#bug/4
	except:
		return 0
def VIBRtrill(val=None):					# boolean, or "N*" / "*"
	try:
		if val!=None:
			LFO.VIBRtrill=gp.parseBoolean(val)
		return 1 if LFO.VIBRtrill else 0
	except:
		return 0
def TREMampl(val=None):						# 1-100
	try:
		if val!=None:
			if val>=1 and val<=100:
				LFO.TREMampl=0.01*val
		return LFO.TREMampl*100
	except:
		return 0
def TREMspeed(val=None):					# 1-32
	try:
		if val!=None:
			if val>=1 and val<=32:
				LFO.TremSetspeed(val*4)
		return LFO.TREMspeed	#bug/4
	except:
		return 0
def TREMtrill(val=None):					# boolean, or "N*" / "*"
	try:
		if val!=None:
			LFO.TREMtrill=gp.parseBoolean(val)
		return 1 if LFO.TREMtrill else 0
	except:
		return False
def PANwidth(val=None):						# 2-20
	try:
		if val!=None:
			if val>=2 and val<=20:
				LFO.PANwidth=0.05*val
		return LFO.PANwidth*20
	except:
		return 0
def PANspeed(val=None):						# 1-32
	try:
		if val!=None:
			if val>=1 and val<=32:
				LFO.PanSetspeed(val*4)
		return LFO.PANspeed	#bug/4
	except:
		return 0

def ARPpower(val=None):					# boolean, or "N*" / "*"
	try:
		if val!=None:
			arp.power( gp.parseBoolean(val) )
		return 1 if arp.power else 0
	except: return False
def ARPstep(val=None):						# 10-100
	try:
		if val!=None:
			if val>=1 and val<=100:
				arp.tempo(1.27*val)
		return arp.stepticks
	except:
		return 0
def ARPsustain(val=None):					# 0-100
	try:
		if val!=None:
			if val>=1 and val<=100:
				arp.sustain(1.27*val)
		return arp.noteticks
	except:
		return 0
def ARPloop(val=None):						# boolean, or "N*" / "*"
	try:
		if val!=None:
			arp.loop=gp.parseBoolean(val)
		return 1 if arp.loop else 0
	except:
		return False
def ARP2end(val=None):						# boolean, or "N*" / "*"
	try:
		if val!=None:
			arp.play2end=gp.parseBoolean(val)
		return 1 if arp.play2end else 0
	except:
		return False
def ARPord(val=None):						# value in ARPordlist
	try:
		if val!=None:
			if isinstance(val,int): arp.ordnum(val)
			else: arp.ordnum(gp.getindex(val,arp.modes,True))
		return arp.mode
	except:
		return 0
def ARPfade(val=None):						# 0-100 (100 means "no fadeout")
	try:
		if val!=None:
			if val>=1 and val<=100:
				arp.fadeout(1.27*val)
		return arp.fadecycles
	except:
		return 0

def CHOrus(val=None):						# value in CHOtypes
	try:
		if val!=None:
			if isinstance(val,int): chorus.setType(val)
			else: chorus.setType(gp.getindex(val,chorus.effects,True))
		return chorus.effect
	except:
		return 0
def CHOdepth(val=None):						# 2-15
	try:
		if val!=None:
			if val>=2 and val<=15:
				chorus.setdepth(9.77*(val-2))
		return chorus.depth
	except:
		return 0
def CHOgain(val=None):						# 30-80
	try:
		if val!=None:
			if val>=30 and val<=80:
				chorus.setgain(2.54*(val-30))
		return chorus.gain*100
	except:
		return 0

def MidiChannel(val=None):					# 1-16
	try:
		if val!=None:
			if val>0 and val<17:
				gv.MIDI_CHANNEL=val
		return gv.MIDI_CHANNEL
	except: return 1

def CHAFreverse(val=None):					# boolean, or "N*" / "*"
	if gv.AFTERTOUCH:
		try:
			if val!=None:
				AfterTouch.chanReverse=gp.parseBoolean(val)
			return 1 if AfterTouch.chanReverse else 0
		except:
			pass
	return 0
def PAFreverse(val=None):					# boolean, or "N*" / "*"
	if gv.AFTERTOUCH:
		try:
			if val!=None:
				AfterTouch.pafReverse=gp.parseBoolean(val)
			return 1 if AfterTouch.pafReverse else 0
		except:
			pass
	return 0
def PAFpitchrange(val=None):						# 1-12
	if gv.AFTERTOUCH:
		try:
			if val!=None:
				if val>=1 and val<=12:
					AfterTouch.paPitchSetRange( (127/12)*val )
			return AfterTouch.paPitchRange
		except:
			pass
	return 2
def PAFpanwidth(val=None):							# 0-10 5=center
	if gv.AFTERTOUCH:
		try:
			if val!=None:
				if val>=0 and val<=10:
					AfterTouch.paPanSetwidth( 12.7*val )
			return AfterTouch.paPanWidth*10
		except:
			pass
	return 5

def Button(val=None):
	try:
		if val!=None:
			if isinstance(val,int): but=int(val)
			else: but=gp.getindex(val,butmenu.buttons,True)
			if but>-1:
				butmenu.nav(but,4)
				return True
		return False
	except:
		return False

# #######################################
# Readonly variables changing during play
# #######################################

def LastMidiNote(*z):				# last note on master controller in the keyboard area
	try: return gv.last_midinote
	except: return -1
def LastMusicNote(*z):				# the same, now music notation (if available)
	try: return gv.last_musicnote
	except: return ""
def DefErr(*z):						# empty or short indication of lines with errors in the definition.txt
	try: return gv.DefinitionErr
	except: return ""
def Mode(*z):						# play mode (keyb, once, loop, mixed etc)
	try: return gv.sample_mode
	except: return ""
def Presetlist(*z):					# [[#,name],.....], so preset "0 Demo" gives element [0,"0 Demo]
	try: return gv.presetlist
	except: return ""
def xvoice(*z):						# Does the effects voice (voice=0) exist ?
	try:
		if gp.getindex(0,gv.voicelist)>-1:
			return True
	except: pass
	return False
def Voicelist(*z):					# [[#,name],.....] similar as variables/tables defined in code or stored in config files on SD or USB, however without voice 0 (effects track)
	vlist=[]
	try:
		for i in range(len(gv.voicelist)):      # filter out effects track and release samples
			if gv.voicelist[i][0]>0:
				vlist.append(gv.voicelist[i])
	except: pass
	return vlist
def bTracks(*z):					# [[#,name,notename in notemap],.....]. Number >0 can be assigned to a midiCC
	try: return gv.btracklist
	except: return []
def Notemaps(*z):					# Available notemaps (names)
	notemaps=["None"]
	try: notemaps.extend(gv.notemaps)
	except: pass
	return notemaps
def NoteMapping(*z):				# [[keybnote,qfraction,soundnote,retune,voice]...]
	try: return gv.notemapping
	except: return []
def MenuDisplay(*z):				# [line1,line2, ..] lines of the characterdisplay of the (button) menu
	try: return [butmenu.line1(),butmenu.line2(),butmenu.line3()]
	except: return ["No menu defined",""]

IP=network.IP
IPlist=network.IPlist
def Wireless(*z):
	try:
		return network.wireless()
	except:
		return ["Network error"]
def SSID(*z):
	return Wireless()[0]

mididevs=[]
mididev=""
def MIDIdevs(*z):					# Current opened mididevices except internal=smfplayer
	return mididevs
def MIDIdev(val=None):				# Pseudo update to serve the button menu system
	global mididev
	try:
		devs=MIDIdevs()
		if len(devs)==0:
			mididev="None"
		elif val==None:
			val=gp.getindex(mididev,devs,True)
			if val<0:val=0
		elif not isinstance(val,int):
			val=gp.getindex(val,mididevs,True)
			if val<0: val=0
		elif val>=len(mididevs) or val<0:
			val=0
		mididev=mididevs[val]
		return mididev
	except: return "Error"

def AfterTouchd(*z):				#  Details of aftertouch support
	if gv.AFTERTOUCH:
		chan = 1 if gv.CHAN_AFTOUCH else 0
		poly = 1 if gv.POLY_AFTOUCH else 0
		return [chan, AfterTouch.chanproc, poly, AfterTouch.polyproc]
	else:
		return [0, "", 0, ""]
def AfterTouchPairs(*z):			# Notepairs of current voice
	pairs = []
	if gv.AFTERTOUCH:
		if gv.currvoice in AfterTouch.notepairs:
			for m in AfterTouch.notepairs[gv.currvoice]:
				pairs.append([m, AfterTouch.notepairs[gv.currvoice][m] ])
	return pairs
	

# #######################################################
# Readonly variables from configuration and mapping files
# #######################################################

def Samplesdir(*z):					# Active samples directory. Either /samples (on SD), /media (on USB) or other path if not using the scripts on SB-image
	return gv.samplesdir
def Stop127(*z):					# First note at right/high side of keyboard area
	return gv.stop127
def qFractions(*z):					# Tone resolution
	return remap.fractions
def KeyNames(*z):					# Keynames used in csv files
	return gv.keynames
def FXpresets(*z):					# Defined effects presetlist for the current sample set
	return gv.FXpresetnames
def Chordname(*z):					# Chordnames as defined in chord.csv
	return gv.chordname
def Chordnote(*z):					# Chordnotes as defined in chord.csv
	return gv.chordnote
def Scalename(*z):					# Scalenames as defined in scales.csv
	return gv.scalename
def Scalechord(*z):					# [[0];[0,...],.....], chords(indexes) per scale
	return gv.scalechord
def ARPordlist(*z):					# Playorders available for ARP
	return arp.modes
def FVtypes(*z):					# Effects implemented via the reverb/freeverb filter
	try: return Cpp.FVtypes
	except: return ["Off"]
def DLYtypes(*z):					# Effects implemented via the Delay line filter
	try: return Cpp.DLYtypes
	except: return ["Off"]
def AWtypes(*z):					# Wah types implemented via the AutoWah filter
	try: return Cpp.AWtypes
	except: return ["Off"]
def DLYtypes(*z):					# Effects implemented via the echo/faser filter
	try: return Cpp.DLYtypes
	except: return ["Off"]
def LFtypes(*z):					# Effects implemented via the Moog low-pass filter
	try: return Cpp.LFtypes
	except: return ["Off"]
def ODtypes(*z):					# Effects implemented via Overdrive effect
	try: return Cpp.ODtypes
	except: return ["Off"]
def PLtypes(*z):					# Effects implemented via Peak limiter
	try: return Cpp.PLtypes
	except: return ["Off"]
def LFOtypes(*z):					# Effects implemented via the Low Frequency Oscillator
	try: return LFO.effects
	except: return ["Off"]
def CHOtypes(*z):					# Effects implemented via Chorus
	return chorus.effects
def AfterTouchSup(*z):					# Is aftertouch supported according configuration.txt ?
	return gv.AFTERTOUCH
def Buttons(*z):					# Buttons supported by button menu
	return butmenu.buttons

# #################################################################################
#                         = = = = =   D I C T I O N A R Y   = = = = =
# #################################################################################

# quite some variables have range 0-100 to both have some parallel with midi 0-127 as well as the human perception
# others still show values indicating the struggle with tuning :-(
# or don't fit in the 0-100 mantra (for instance min and max settings should have same scale to avoid confusion)
# etcetera...etcetera... in other words, not completely consistent :-)

# Please look at the webgui to see some hints & practical use; much more educational and easier than explaining all variables here
# First element:
#  - w= writable: the ui can change this via a procuderu with dictionary name (NOT via this dictionary !! Use the proper function !)
#  - v= variable: informational variables/tables that change in normal (play) situation
#  - f= fixed   : informational variables/tables defined in code or stored in config files on SD or USB
# Second element:
#  - procedure with one optional parameter: return=proc(parameter)
#    depending on the proc, this parameter is either boolean, integer, text or list
#  - booleans can be:
#    - True/False
#    - a number where 0 means False and any other value means True
#    - a string beginning with "N" or "n" meaning False and any other value meaning True
#  - return value is an up2date value of the requested parameter (this maybe a list/dict/etc depending requested parameter)
#    however on update, some procedures return a boolean instead to indicate a change having impact (on others or your logic)
#  - if parameter is omitted or =None it is just an inquiry
#    if filled, its value is processed; the user facing procedure should perform error checking
#    if input contains errors, the proc tries to finish somehow, preferably without changing SB's status
#  - if procedure is called with the underlying feature not enabled, a default value is returned
#    this will ofcourse happen in display routines starting in early init stage, where features may NOT YET be enabled :-)
# Third element (optional):
#  - Alias = human readable text, used in the configuration files (e.g. the effects.csv)
#  - After definition an extra dictionary is created below with this third element as key and the procedure as data

procs={
	"RenewMedia":["w",RenewMedia],	# boolean, True indicates "preset load in progress",
											# setting any value except False forces reload of sample set
		# a presetload like above should finish and then requires a refresh of all values

		# next procedures return a boolean parameter after update request, indicating the request resulted in a change
	"DefinitionTxt":["w",DefinitionTxt],	# contains definition.txt, either returns definition.txt or renewmedia
	"Preset":["w",Preset],					# 0-127, returns either preset or renewmedia
	"Voice":["w",Voice],					# (integer) index of Voicelist or (string) actual voice, returns either voice or voicechange
	"FXpreset":["w",FXpreset],				# (string) Name to be activated FXpresets, returns either "None" or the newly activated FXpreset
	"Notemap":["w",Notemap],				# (string) Notemap or (integer) index in notemap of active notemap, returns either notemap or notemapchange
	"nm_inote":["w",nm_inote],				# (string) Keyname or (integer) index in KeyNames for keyboardnote

		# next procedures always return the value of the respective parameter
	"nm_Q":["w",nm_Q],								# (integer) index of qFractions or (string) tones, so currently either "Semi" or "Quarter"
	"nm_unote":["w",nm_unote],						# index of an interface defined table/note to present the output note (when user prefers Bb above A# etcetera)
	"nm_onote":["w",nm_onote],						# (integer) -2 to 127 with -2=Ctrl, -1=None and 0-127=midinotes or (string) notename + None/Ctrl
	"nm_retune":["w",nm_retune],					# -50 - +50, retune in cents (0 is neutral)
	"nm_voice":["w",nm_voice],		     			# index of Voicelist to switch to, so you can only define switches to know voices in this preset
	"nm_map":["w",nm_map],							# name of map to save
	"nm_clr":["w",nm_clr],							# boolean, requesting clear notemap if True
	"nm_sav":["w",nm_sav],							# boolean, requesting save notemap if True
	"Scale":["w",Scale,gv.SCALES],					# index of ScaleName (& ScaleChord)
	"Chord":["w",Chord,gv.CHORDS],					# index of Chordname
	"SoundVolume":["w",SoundVolume],				# 0-100
	"MidiVolume":["w",MidiVolume],					# 0-100
	"Gain":["w",Gain],								# 0-300 (100 is neutral
	"Pitchrange":["w",Pitchrange,gv.PITCHSENS],		# 0-12 (so max 1 octave up & down)
	"FVtype":["w",FVtype,gv.REVERB],				# (integer) index or (string) of value in FVtypes
	"FVroomsize":["w",FVroomsize,gv.REVERBROOM],	# 0-100
	"FVdamp":["w",FVdamp,gv.REVERBDAMP],			# 0-100
	"FVlevel":["w",FVlevel,gv.REVERBLVL],			# 0-100
	"FVwidth":["w",FVwidth,gv.REVERBWIDTH],			# 0-100
	"AWtype":["w",AWtype,gv.AUTOWAH],				# (integer) index or (string) of value in AWtypes
	"AWmixing":["w",AWmixing,gv.AUTOWAHLVL],		# 0-100
	"AWattack":["w",AWattack,gv.AUTOWAHATTACK],		# 0-500
	"AWrelease":["w",AWrelease,gv.AUTOWAHRELEASE],	# 0-500
	"AWminfreq":["w",AWminfreq,gv.AUTOWAHMIN],		# 20-500
	"AWmaxfreq":["w",AWmaxfreq,gv.AUTOWAHMAX],		# 1000-10000
	"AWqfactor":["w",AWqfactor,gv.AUTOWAHQ],		# 0-100
	"AWspeed":["w",AWspeed,gv.AUTOWAHSPEED],		# 100-1100
	"AWlvlrange":["w",AWlvlrange,gv.AUTOWAHLVLRNGE],# 0-100
	"DLYtype":["w",DLYtype,gv.DELAYTYPE],			# (integer) index or (string) of value in DLYtypes
	"DLYfb":["w",DLYfb,gv.DELAYFB],					# 0-100
	"DLYwet":["w",DLYwet,gv.DELAYFW],				# 0-100
	"DLYdry":["w",DLYdry,gv.DELAYMIX],				# 0-100
	"DLYtime":["w",DLYtime,gv.DELAYTIME],			# 1000-61000
	"DLYsteep":["w",DLYsteep,gv.DELAYSTEEP],		# 1-11
	"DLYsteplen":["w",DLYsteplen,gv.DELAYSTEPLEN],	# 300-3300
	"DLYmin":["w",DLYmin,gv.DELAYMIN],				# 5-25
	"DLYmax":["w",DLYmax,gv.DELAYMAX],				# 50-150
	"LFtype":["w",LFtype,gv.LADDER],				# (integer) index or (string) of value in LFtypes
	"LFresonance":["w",LFresonance,gv.LADDERRES],	# 0-38
	"LFcutoff":["w",LFcutoff,gv.LADDERCUTOFF],		# 1000-11000	
	"LFdrive":["w",LFdrive,gv.LADDERDRIVE],			# 1-20
	"LFlvl":["w",LFlvl,gv.LADDERLVL],				# 0-100
	"LFgain":["w",LFgain,gv.LADDERGAIN],			# 10-110, Carefully test before using values above 50
	"ODtype":["w",ODtype,gv.OVERDRIVE],				# (integer) index or (string) of value in ODtypes
	"ODboost":["w",ODboost,gv.ODRVBOOST],			# 15-65
	"ODdrive":["w",ODdrive,gv.ODRVDRIVE],			# 1-11
	"ODtone":["w",ODtone,gv.ODRVTONE],				# 0-95 (accepts up to 100)
	"ODmix":["w",ODmix,gv.ODRVMIX],					# 0-10 (10=100% wet)
	"PLtype":["w",PLtype,gv.LIMITER],				# (integer) index or (string) of value in PLtypes
	"PLthresh":["w",PLthresh,gv.LIMITTHRESH],		# 70-110
	"PLattack":["w",PLattack,gv.LIMITATTACK],		# 1-11
	"PLrelease":["w",PLrelease,gv.LIMITRELEASE],	# 1-11
	"LFOtype":["w",LFOtype,gv.LFOTYPE],				# (integer) index or (string) of value in LFOtypes
	"VIBRpitch":["w",VIBRpitch,gv.VIBRDEPTH],		# 1-64
	"VIBRspeed":["w",VIBRspeed,gv.VIBRSPEED],		# 1-32	
	"VIBRtrill":["w",VIBRtrill,gv.VIBRTRILL],		# boolean
	"TREMampl":["w",TREMampl,gv.TREMDEPTH],			# 1-100
	"TREMspeed":["w",TREMspeed,gv.TREMSPEED],		# 1-32
	"TREMtrill":["w",TREMtrill,gv.TREMTRILL],		# boolean
	"PANwidth":["w",PANwidth,gv.PANWIDTH],			# 2-20
	"PANspeed":["w",PANspeed,gv.PANSPEED],			# 1-32
	"ARPeggiator":["w",ARPpower,arp.power],			# boolean
	"ARPord":["w",ARPord,gv.ARP],					# (integer) index or (string) of value in ARPordlist
	"ARPstep":["w",ARPstep,gv.ARPTEMPO],			# 10-100
	"ARPsustain":["w",ARPsustain,gv.ARPSUSTAIN],	# 0-100
	"ARPloop":["w",ARPloop,gv.ARPLOOP],				# boolean
	"ARP2end":["w",ARP2end,gv.ARP2END],				# boolean
	"ARPfade":["w",ARPfade,gv.ARPFADE],				# 0-100 (100 means "no fadeout")
	"CHOrus":["w",CHOrus,gv.CHORUS],				# (integer) index or (string) of value in CHOeffects
	"CHOdepth":["w",CHOdepth,gv.CHORUSDEPTH],		# 2-15
	"CHOgain":["w",CHOgain,gv.CHORUSGAIN],			# 30-80
	"MidiChannel":["w",MidiChannel],				# 1-16
	"CHAFreverse":["w",CHAFreverse,gv.CHAFREVERS],	# boolean (0-1)
	"PAFreverse":["w",PAFreverse,gv.PAFREVERS],		# boolean (0-1)
	"PAFpitchrange":["w",PAFpitchrange,gv.PAFPITCHRANGE],	# 1-12 (semitones, up&down, so max 1 octave total)
	"PAFpanwidth":["w",PAFpanwidth,gv.PAFPANWIDTH],	# 0-10 5=center
	"Button":["w",Button],							# index of Buttons, where 0 has no function (no button touched)

# Readonly variables changing during play (parameters are ignored)

	"LastMidiNote":["v",LastMidiNote],		# last note on master controller in the keyboard area
	"LastMusicNote":["v",LastMusicNote],	# the same, now music notation (if available)
	"DefErr":["v",DefErr],					# empty or short indication of lines with errors in the definition.txt
	"Mode":["v",Mode],						# play mode (keyb, once, loop etc)
	"Presetlist":["v",Presetlist],			# [[#,name],.....], so preset "0 Demo" gives element [0,"0 Demo]
	"xvoice":["v",xvoice],					# Does the/ effects track (voice=0) exist ?
	"Voicelist":["v",Voicelist],			# [[#,name],.....] similar to table defined in code or stored in config files on SD or USB, however without voice 0 (effects track)
	"bTracks":["v",bTracks],				# [[#,name,notename in notemap],.....]. Number >0 can be assigned to a midiCC
	"Notemaps":["v",Notemaps],				# Available notemaps (names)
	"NoteMapping":["v",NoteMapping],		# [[keybnote,qfraction,soundnote,retune,voice]...]	
	"MenuDisplay":["v",MenuDisplay],		# [line1,line2, ..] lines of the characterdisplay of the (button) menu
	"IP":["w",IP],							# index of IP addresses found (it's classified "w" to force into the button menu)
	"IPlist":["v",IPlist],					# SB IP addresses (cable and wireless plus IPv6 if enabled in configuration.txt)
	"Wireless":["v",Wireless],				# Wireless network info
	"SSID":["w",SSID],						# Wireless network (it's classified "w" to force into the button menu)
	"MIDIdevs":["v",MIDIdevs],				# Current opened mididevices except internal=smfplayer
	"MIDIdev":["w",MIDIdev],				# Opened MIDIdevice (it's classified "w" to force into the button menu)
	"AfterTouchd":["v",AfterTouchd],		# Details of aftertouch support
	"AfterTouchPairs":["v",AfterTouchPairs],# Notepairs of current voice

# Readonly variables from configuration and mapping files (parameters are ignored)

	"Samplesdir":["f",Samplesdir],			# Active samples directory. Either /samples (on SD), /media (on USB) or other author defined path if not using the scripts on SB-image
	"Stop127":["f",Stop127],				# First note at right/high side of keyboard area
	"qFractions":["f",qFractions],			# [[1, 'Semi'], [2, 'Quarter']]
	"KeyNames":["f",KeyNames],				# Notenames as defined in keynotes.csv
	"FXpresets":["f",FXpresets],			# Effect presetnames available in current set (merged box en set presets)
	"Chordname":["f",Chordname],			# Chordnames as defined in chord.csv
	"Chordnote":["f",Chordnote],			# Chordnotes as defined in chord.csv
	"Scalename":["f",Scalename],			# Scalenames as defined in scales.csv
	"Scalechord":["f",Scalechord],			# [[0,...],.....], chords(indexes) per scale, defined in scales.csv
	"ARPordlist":["f",ARPordlist],			# Playorders available for ARP
	"DLYtypes":["f",DLYtypes],				# Effects implemented via the Delay line filter
	"AWtypes":["f",AWtypes],				# Wah types implemented via the AutoWah filter
	"FVtypes":["f",FVtypes],				# Reverb/Freeverb types (just on/off..)
	"LFtypes":["f",LFtypes],				# Moog low pass (just on/off..)
	"ODtypes":["f",ODtypes],				# Overdrive effect (just on/off..)
	"PLtypes":["f",PLtypes],				# Peak limiter (just on/off..)
	"LFOtypes":["f",LFOtypes],				# Effects implemented via the Low Frequency Oscillator
	"CHOtypes":["f",CHOtypes],				# Chorus (just on/off..)
	"AfterTouchSup":["f",AfterTouchSup],	# Is aftertouch supported in this configuration
	"Buttons":["f",Buttons]					# Buttons supported by button menu
	}

gv.procs_alias = {}
for m in procs:
	if len(procs[m]) > 2:
		gv.procs_alias[ procs[m][2] ] = procs[m][1]

#             = = = = =   Extra procedures, not (directly) related to in/output fields   = = = = =

# notemap housekeeping
nm_sync=remap.notes_sync					# Execute before showing results on the display to be in sync with play status
nm_consolidate=remap.notes_consolidate		# Executed before using/presenting changes on nm_inote, nm_onote, nm_retune, nm_voice or nm_unote
# access to configuration.txt, example: up=UI.cfg_int("BUT_incr")
cfg_txt=lambda x: gv.cp.get(gv.cfg,x.lower())
cfg_int=lambda x: gv.cp.getint(gv.cfg,x.lower())
cfg_float=lambda x: gv.cp.getfloat(gv.cfg,x.lower())
cfg_bool=lambda x: gv.cp.getboolean(gv.cfg,x.lower())
# miscellaneous
getindex=gp.getindex						# index=getindex(searchval,table<,onecol>). "onecol" is optional boolean "has table one column only". Default=False
display=gp.NoProc							# if the user interface needs to display something on the system display
menu=butmenu.nav							# the buttons menu navigation
USE_ALSA_MIXER=False						# this is (re)set by audio detection
USE_IPv6=gv.USE_IPv6						# set by network module
