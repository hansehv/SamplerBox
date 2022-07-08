###############################################################
#  Interactively adapt Controller mapping on running samplerbox
#  - written for the UI module, so:
#  - usable for other human interfaces (touchscreen etc.), but:
#  - don't mix use of interfaces without adding some safeguards
#    ...if you do so, please share your implementation, thanks!
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
#   see docs at https://homspace.nl/samplerbox
###############################################################
import copy
import gv,gp

ctrlfam = 0
ctrl = 0		# control idx in family
ctrlMC = 0		# control index in MC table
ctrlval = -1
ctrls = []
ctrlnams = []
ctrlmods = []

ctrlr = -1
ctrlrs = []
ctrlrnams = []
prevctrlr = -1
prevctrlval = -1
prevvoice = -1

voicelist = []
btracklist = []
valtabs = {}

def realvoices(*z):					# [[#,name],.....] similar as variables/tables defined in code or stored in config files on SD or USB, however without voice 0 (effects track)
	global voicelist
	voicelist = []
	try:
		for i in range(len(gv.voicelist)):      # filter out effects track and release samples
			if gv.voicelist[i][0]>0:
				voicelist.append([ gv.voicelist[i][0], gv.voicelist[i][1] ])
	except: pass
	return voicelist

def numbered_btracks(*z):
	return btracklist

def setvaltabs():
	global valtabs, btracklist
	notemaps = ["None"]
	notemaps.extend(gv.notemaps)
	btracklist = []
	for i in range(len(gv.btracklist)):      # filter out effects track and release samples
		if gv.btracklist[i][0]>0:
			btracklist.append([ gv.btracklist[i][0], gv.btracklist[i][1] ])
	valtabs = {
			gv.CHORDS: [gv.chordname, 1],		# name (starting "")
			gv.SCALES: [gv.scalename, 1],		# name (starting "")
			gv.VOICES: [voicelist, 2],			# voice#, name
			gv.BACKTRACKS: [btracklist, 2],		# track#, name
			gv.SMFS: [gv.smfnames, 2],			# seq#, (file)name
			gv.NOTEMAPS: [notemaps, 1],			# name (starting "None")
			gv.FXPRESETS: [gv.FXpresetnames, 1]	# name (starting "None")
		};

def setnames():
	global ctrlnams, ctrlrnams
	for m in gv.MC:
		if len( m ) > 3:	# name, type, proc, family, MCmodenameindex
			ctrlnams.append( m[0] )
			ctrlmods.append( m[4] )
	for m in gv.controllerCCs:
		ctrlrnams.append( m[0] )

def ctrlnames(*z):
	return ctrlnams
def ctrlmodes(*z):
	return ctrlmods
def ctrlrnames(*z):
	return ctrlrnams

def consolidate(*z):
	realvoices()
	setvaltabs()
	controls()
	controllers()
	current()

def family(val=None):
	global ctrlfam, ctrl, ctrlr, ctrlval
	if val != None:
		savfam = ctrlfam
		try:
			val = int(val)
			try:
				f = gv.CCfamilies[val]
				ctrlfam = val
			except:
				pass
		except:
			val = val.lower()
			for i in range(len(gv.CCfamilies)):
				if gv.CCfamilies[i].lower()==val:
					ctrlfam = i
					break
		if savfam != ctrlfam:
			ctrl = 0
			ctrlr = -1
			ctrlval = -1
		return savfam == ctrlfam
	return ctrlfam

def controls(*z):					# Controls (defined & activated)
	global ctrls, ctrlnams
	ctrls = []
	i = 0
	for m in gv.MC:
		if len( m ) > 3:	# name, type, proc, family
			if m[3] == ctrlfam:
				if m[2] != gv.safeguard:
					ctrls.append( i )
		i += 1
	return ctrls

def control(val=None):
	global ctrl, ctrlr, ctrlval, ctrlMC
	if val != None:
		savc = ctrl
		ctrl = 0
		try: 
			val = int(val)
			try:
				c = ctrls[val]
				ctrl = val
			except:
				pass
		except:
			val = val.lower()
			for i in range(len(ctrls)):
				if ctrls[i][1].lower()==val:
					ctrl=i
					break
		if savc != ctrl:
			ctrlr = -1
			ctrlval = -1
		return savc == ctrl
	if len( ctrls ) > 0:
		ctrlMC = gp.getindex( ctrlnams[ ctrls[ctrl] ], gv.MC)
	return ctrl

def controlMC(*z):
	return ctrlMC

def controlval(val=None):
	# controlval is fout voor unassigned controllers (wordt 1e occurence)
	global ctrlval, prevctrlval
	ctrlidx = ctrls[ctrl]
	MC = gv.MC[ ctrlidx ]
	if MC[1] == 2:	# a tablevalue
		table = valtabs[ MC[0] ][0]
		onecol = True if valtabs[ MC[0] ][1] == 1 else False
		controller()	# safety first
		ctrlridx = ctrlrs[ctrlr]
		if ctrlval < 0:
			if ctrlr == 0:	# don't change for unassigning !
				ctrlval = prevctrlval
				return ctrlval
			ctrlval = 0
			for i in range(len(gv.CCmap)):
				if gv.CCmap[i][0] == ctrlridx:
					if gv.CCmap[i][1] == ctrlidx:
						if onecol:
							ctrlval = gp.getindex(gv.CCmap[i][2], table, onecol=True)
							if ctrlval < 0:
								ctrlval = 0
						else:
							ctrlval = int( gv.CCmap[i][2] )
					break
		elif val != None:
			ctrlval = int(val)
			if not onecol:
				ctrlval = table[ctrlval][0]
		prevctrlval = ctrlval
	return ctrlval

def controlmode(*z):
	global ctrl
	if ctrl >= len(ctrls):
		ctrl = 0
	return gv.MCmodenames[ gv.MC[ctrls[ctrl]][4] ]

def controltype(*z):
	global ctrl
	if ctrl >= len(ctrls):
		ctrl = 0
	return gv.MC[ctrls[ctrl]][1]

def controllers(*z):
	global ctrlrs, ctrl
	# select controllers compatible with this control
	ctrlrs = []
	i = 0

	if ctrl >= len(ctrls):
		ctrl = 0
	ctrltype = gv.MCtypes[ gv.MC[ctrls[ctrl]][1] ]

	if ctrltype < 0:	# continuous controllers (incl aftertouch)
		for c in gv.controllerCCs:
			if c[2] == ctrltype:
				ctrlrs.append( i )
			i += 1

	else:				# buttons, switches, keys
		ctrlrs = [0]	# insert the "unassigned"
		keys = []
		for n in gv.notemapping:
			if n[2] == -2:	# key mapped as control
				keys.append( n[0] )
		for c in gv.controllerCCs:
			if c[2] > 0:
				if c[1] == gv.NOTES_CC:
					if c[2] in keys:	# verify this key is mapped
						ctrlrs.append( i )
				else:
					ctrlrs.append( i )
			i += 1

	return ctrlrs

def controller(val=None):
	global ctrlr, prevctrlr, prevvoice, ctrlval

	if val == None:
		if prevvoice != gv.currvoice:
			prevvoice = gv.currvoice
			ctrlr = -1
		try:
			control = ctrls[ctrl]
			if ctrlr < 0:
				ctrlrMC = 0
				for m in gv.CCmap:
					if m[1] == control:
						ctrlrMC = m[0]
						ctrlr = gp.getindex(ctrlrMC, ctrlrs, onecol=True)
						break
		except:
			ctrlr = -2
		if ctrlr < -1:
			print ("UI_CCmap controller: Logic error, ", ctrlr)
			ctrlr = -1;

	else:
		savc = ctrlr
		if ctrlr:
			prevctrlr = ctrlrs[ctrlr]
		ctrlr = 0
		try:
			val = int(val)
			try:
				c = ctrlrs[val]
				ctrlr = val
			except:
				pass
		except:
			val = val.lower()
			for i in range(len(ctrlrs)):
				if ctrlrs[i][0].lower() == val:
					ctrlr = i
					break
		if savc != ctrlr:
			ctrlval = -1
	return ctrlr

def assign_levels():
	return ["","Set","Voice"]

def assign(val=None):
	if val:
		voice = 0 if val=="Set" else gv.currvoice
		if ctrlr == 0:
			return unassign(voice)
		controller = ctrlrs[ctrlr]
		control = ctrls[ctrl]
		parm = gv.MCmodenames[ gv.MC[control][4] ]
		if gv.MC[control][1] == 2:
			valtab = valtabs[ ctrlnams[control] ][0]
			if not len(valtab):
				return 0
			if valtabs[ ctrlnams[control] ][1] == 1:
				parm = valtab[ctrlval]
			else:
				x = gp.getindex( ctrlval, valtab)
				if x < 0:
					print ( "UI_CCmap assign: Logic error, ", ctrlval, ctrlnams[control] )
				parm = valtabs[ ctrlnams[control] ][0][ x ][0]
		found = False
		for c in gv.CCmap:
			if controller == c[0]:
				found = True
				if (c[3] == voice
				 or c[3] < 1 ):
					c[1] = control
					c[2] = parm
					c[3] = voice
		if not found:
			gv.CCmap.append([ controller, control, parm, voice ])
	return 0

def unassign(voice):
	global ctrlr, ctrlval
	# We can not and will not unassign system defaults ("Box", voice=-1)
	for i in range( len(gv.CCmap) ):
		if gv.CCmap[i][0] == prevctrlr:
			if gv.CCmap[i][3] == voice:
				found = False
				# -1 = box, 0 = set, >0 = voice
				level = 1 if gv.CCmap[i][3] > 0 else 0
				if level == 1:
					found = unassignlev(i, gv.CCmapSet, 1)
				if not found:
					found = unassignlev(i, gv.CCmapBox, 0)
				if not found:
					del gv.CCmap[i]
				break
	ctrlr = -1
	ctrlval = -1
	return 0

def unassignlev(entry, CCmapX, level):
	found = False
	for m in CCmapX:
		if (m[0] == prevctrlr
		and m[3] < level):
			gv.CCmap[entry] = copy.deepcopy(m)
			found = True
			break
	return found

def resetmap(val=None):
	if val:
		if gp.parseBoolean(val):
			gp.setCCmap(gv.currvoice)
	return(0)

def savemap(val=None):				# boolean, but as read variable it's always 0=no/false
	# update all this-voice assignments
	# update set changes where visible (= not hidden by a voice assignment)
	# save the (sampleset) CCmap csv
	
	# CCmap:	[buttonindex, procedureindex, additional procedure parameter, voice]
	# file:		[Voice, Controller, Type, Sets, Mode]
	# MC:		[name,type,procedure,familyindex,MCmodenameindex]
	
	newmapset = []
	thisvoice = []
	if val!=None:
		if gp.parseBoolean(val):	# do we want to save a map ?

			# fill newmap with current except voice =-1 (box default)
			for m in gv.CCmap:
				if m[3] >= 0:
					newmapset.append(m)
					if m[3] > 0:
						thisvoice.append(m[0])

			# add other voices and possible overridden set values
			for m in gv.CCmapSet:
				if m[3] != gv.currvoice:
					if (m[3] > 0
					or  m[0] in thisvoice):
						newmapset.append(m)

			# sort on voice
			sortedset = sorted(newmapset, key = lambda x: ( x[3], x[0]))

			# save the stuff
			gp.samples2write()
			fname=gp.presetdir() + gv.CTRLMAP_DEF
			with open(fname, 'w') as mapfile:
				mapfile.write("Voice,Controller,Type,Sets,Mode\n")
				for m in sortedset:
					mc = gv.MC[ m[1] ]
					voice = m[3]
					controller = gv.controllerCCs[ m[0] ][0]
					typ = "Fixed"
					sets = mc[0]
					mode = gv.MCmodenames[ mc[4] ]
					if mc[1] == 2:	# value tables variable
						typ = mc[0]
						sets = m[2]
					mapfile.write('%s,%s,%s,%s,%s\n' %(voice,controller,typ,sets,mode) )
					gv.CCmapSet = sortedset
			gp.samples2read()

	return 0

def current(*z):
	return gv.CCmap
