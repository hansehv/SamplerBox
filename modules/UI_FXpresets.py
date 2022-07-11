###############################################################
#  Interactively adapt the effect presets on running samplerbox
#  - written for the UI module, so:
#  - usable for other human interfaces (touchscreen etc.), but:
#  - don't mix use of interfaces without adding some safeguards
#    ...if you do so, please share your implementation, thanks!
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
#   see docs at https://homspace.nl/samplerbox
###############################################################
import gv,gp

presetname = ''

'''
	What to save is selected via Y/N buttons "fxp_<effect>".
	This "effect" refers to a family as defined in controls.csv.
	These families are also used in CCmapping.
	
	When a preset is selected, the defintions in there will have their
	related "family" button to be defaulted to Y = include.
	
	At save all definitions will be removed and replaced according savit-dict.
	The savit-dict is filled via the related buttons.
	So: when nothing is selected, the complete preset will disappear
'''

savit = {
	gv.LFO: False,
	gv.CHORUS: False,
	gv.REVERB: False,
	gv.AUTOWAH: False,
	gv.DELAY: False,
	gv.LADDER: False,
	gv.OVERDRIVE: False,
	gv.LIMITER: False,
	gv.ARP: False,
	gv.AUTOCHORD: False,
	gv.AFTERTOUCH: False,
	}

def setpreset(val, *z):
	global presetname
	FXset = val
	try:
		val =( int(val) ) # isinstance(val,int) doesn't work correctly here :-(
		try:
			FXset = gv.FXpresetnames[val]
		except:
			FXset = gv.FXpresetnames[0]
	except:
		idx = gp.getindex(FXset,gv.FXpresetnames,True)
		if idx < 0:
			idx = 0
		FXset = gv.FXpresetnames[idx]
	if FXset == "":
		gv.FXpreset_last = gv.FXpresetnames[0]
	elif (FXset != gv.FXpreset_last):
		if FXset in gv.FXpresetnames:
			gv.FXpreset_last = FXset
			defaults4sav(False)	# this the 1st reason for defining the "setpreset" proc in here
			if gv.FXpreset_last != "None":
				for effect in gv.FXpresets[FXset]:
					gv.procs_alias[ effect ][0]( gv.FXpresets[FXset][effect] )
		else:
			print ("Effect %s is unspecified, ignored" %FXset)
	presetname = FXset	# this the 2nd reason for defining the "setpreset" proc in here
	return FXset
gv.setMC(gv.FXPRESETS,setpreset)

def defaults4sav(resetall=None):
	'''
	- gv.FXpreset[gv.FXpreset_last][control] => gv.MC[control][3] = family
	- any definition causes savit[family] to be True
	'''
	if resetall != None:
		for control in savit:
			savit[control] = False
		if gp.parseBoolean(resetall):
			return
		if gv.FXpreset_last not in ["None","Default"]:
			for mc in gv.MC:
				if len(mc) > 3:
					if mc[0] in gv.FXpresets[gv.FXpreset_last]:
						savit[ gv.CCfamilies[mc[3]] ] = True
	return 0

def LFO(val=None):
	global savit
	if val!=None: savit[gv.LFO] = gp.parseBoolean(val)
	return savit[gv.LFO]
def chorus(val=None):
	global savit
	if val!=None: savit[gv.CHORUS] = gp.parseBoolean(val)
	return savit[gv.CHORUS]
def reverb(val=None):
	global savit
	if val!=None: savit[gv.REVERB] = gp.parseBoolean(val)
	return savit[gv.REVERB]
def autowah(val=None):
	global savit
	if val!=None: savit[gv.AUTOWAH] = gp.parseBoolean(val)
	return savit[gv.AUTOWAH]
def delay(val=None):
	global savit
	if val!=None: savit[gv.DELAY] = gp.parseBoolean(val)
	return savit[gv.DELAY]
def ladder(val=None):
	global savit
	if val!=None: savit[gv.LADDER] = gp.parseBoolean(val)
	return savit[gv.LADDER]
def overdrive(val=None):
	global savit
	if val!=None: savit[gv.OVERDRIVE] = gp.parseBoolean(val)
	return savit[gv.OVERDRIVE]
def limiter(val=None):
	global savit
	if val!=None: savit[gv.LIMITER] = gp.parseBoolean(val)
	return savit[gv.LIMITER]
def arp(val=None):
	global savit
	if val!=None: savit[gv.ARP] = gp.parseBoolean(val)
	return savit[gv.ARP]
def autochord(val=None):
	global savit
	if val!=None: savit[gv.AUTOCHORD] = gp.parseBoolean(val)
	return savit[gv.AUTOCHORD]
def aftertouch(val=None):
	global savit
	if val!=None: savit[gv.AFTERTOUCH] = gp.parseBoolean(val)
	return savit[gv.AFTERTOUCH]

def setname(val=None):		# name of preset to save
	global presetname
	if val != None:
		presetname = gp.no_delimiters(val.title())
		if presetname in ["Box", "Set"]:
			presetname = "Default"
	return presetname

def save(val=False):
	if (gp.parseBoolean(val)
	and presetname!=""):	# do we want to save a preset and do we know its name ?
		'''
		Replace or add the definition.
		Any definition in "Default" equal to corresponding system default
		will be ignored = not saved.
		This causes cleanup of csv's created manually (has pros and cons).
		'''
		gv.FXpresets[presetname] = {}	# saves order of existing and places new at end
		for family in savit:
			if savit[family]:
				famidx = gp.getindex(family, gv.CCfamilies, onecol=True)
				'''
				search controls for this family
				- in UI: gv.procs_alias[ procs[m][2] ][0] = procs[m][1]
				- procs[m][1] is pointer to UI routine => control content
				- UI.procs[m][2] is key of gv.MC = the controlname in csv's
				- gv.MC[control][3] is family
				'''
				for control in gv.MC:
					if control[3] == famidx:
						controlname = control[0]
						if controlname in gv.procs_alias:
							content = gv.procs_alias[ controlname ][0]()
							csvformat = gv.procs_alias[ controlname ][1]
							if csvformat == "int":
								content = int( content )
							else:
								content = csvformat[ content ]
								if controlname in [ gv.CHORDS, gv.SCALES ]:
									if content == "":
										content = "Note"
							gv.FXpresets[presetname].update( {controlname: content} )
		'''
		if nothing was checked, the preset needs to disappear
		'''
		if len( gv.FXpresets[presetname] ) == 0:
			del gv.FXpresets[presetname]
			if presetname in gv.FXpresetnames:
				gv.FXpresetnames.remove(presetname)
		elif presetname not in gv.FXpresetnames:
			gv.FXpresetnames.append(presetname)
		'''
		Now save the stuff,
		while skipping "Default" entries duplicating the system default ("BOX")
		'''
		gp.samples2write()
		fname=gp.presetdir() + gv.FXPRESETS_DEF
		with open(fname, 'w') as fxpfile:
			fxpfile.write("Presetname,Parameter,Value\n")
			for preset in gv.FXpresets:
				presetnam = "Set" if preset == "Default" else preset
				for control in gv.FXpresets[preset]:
					if preset == "Default":
						if (control in gv.FXpresets_box["Default"]
						and gv.FXpresets_box["Default"][control] == gv.FXpresets[preset][control]
						):
							continue
					fxpfile.write('%s,%s,%s\n' %(
									presetnam, control,
									gv.FXpresets[preset][control]
									)
								)
		gp.samples2read()
		setpreset(presetname)
	return 0
