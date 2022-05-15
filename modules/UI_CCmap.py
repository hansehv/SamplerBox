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
import gv,gp

ctrlfam = 0
ctrl = 0		# control idx in family
ctrlMC = 0		# control index in MC table
ctrlval = -1
ctrls = []
ctrlnams = []
ctrlmods = []

ctrlr = 0
ctrlrs = []
ctrlrnams = []

voicelist = []
valtabs = {}
cmap = []

def realvoices(*z):					# [[#,name],.....] similar as variables/tables defined in code or stored in config files on SD or USB, however without voice 0 (effects track)
	global voicelist
	voicelist = []
	try:
		for i in range(len(gv.voicelist)):      # filter out effects track and release samples
			if gv.voicelist[i][0]>0:
				voicelist.append([ gv.voicelist[i][0], gv.voicelist[i][1] ])
	except: pass
	return voicelist

def setvaltabs():
	global valtabs
	valtabs = {
			'Chords': [gv.chordname, 1],		# name (starting "")
			'Scales': [gv.scalename, 1],		# name (starting "")
			'Voices': [voicelist, 2],			# voice#, name
			'BackTracks': [gv.btracklist, 3],	# track#, name, note
			'SMFs': [gv.smfnames, 2],			# seq#, (file)name
			'Notemaps': [gv.notemaps, 1],		# name (starting "None")
			'FXpresets': [gv.FXpresetnames, 1]	# name (starting "None")
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
			ctrlr = 0
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
			ctrlr = 0
			ctrlval = -1
		return savc == ctrl
	if len( ctrls ) > 0:
		ctrlMC = gp.getindex( ctrlnams[ ctrls[ctrl] ], gv.MC)
	return ctrl

def controlMC(*z):
	return ctrlMC

def controlval(val=None):
	global ctrlval
	ctrlidx = ctrls[ctrl]
	MC = gv.MC[ ctrlidx ]
	if MC[1] == 2:	# a tablevalue
		table = valtabs[ MC[0] ][0]
		onecol = True if valtabs[ MC[0] ][1] == 1 else False
		if ctrlr == 0:
			controller()
		ctrlridx = ctrlrs[ctrlr]
		if ctrlval < 0:
			ctrlval = 0
			for i in range(len(cmap)):
				if cmap[i][0] == ctrlridx:
					if cmap[i][1] == ctrlidx:
						if onecol:
							ctrlval = gp.getindex(cmap[i][2], table, onecol=True)
						else:
							ctrlval = int( cmap[i][2] )
					break
		elif val != None:
			ctrlval = int(val)
			if not onecol:
				ctrlval = table[ctrlval][0]
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

			if n[3] == -2:	# key mapped as control
				keys.append( n[1] )
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
	global ctrlr, ctrlval

	if val == None:
		try:
			control = ctrls[ctrl]
			if ctrlr == 0:
				ctrlrMC = 0
				for m in cmap:
					if m[1] == control:
						ctrlrMC = m[0]
						ctrlr = gp.getindex(ctrlrMC, ctrlrs, onecol=True)
						break
		except:
			ctrlr = -1
		if ctrlr < 0:
			print ("UI_CCmap controller: Logic error, ", ctrlr)
			ctrlr = 0;

	else:
		savc = ctrlr
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

#def assign(val=None):

def savemap(val=None):
	return 0

def current(*z):
	global cmap
	# CCmap: [buttonindex, procedureindex, additional procedure parameter, voice]
	cmap = []
	for m in gv.CCmap:
		if (m[3] == gv.currvoice
		or	m[3] < 1):
			cmap.append(m)
	return cmap
