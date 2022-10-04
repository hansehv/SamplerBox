###############################################################
# Sound layers (add extra voices to the active note)
# Process incorporated in the note-on logic, so rather cheap,
# except for the extra sound (so: comparable with autochord)
#
# The interactive=UI configuration part is
#  - written for the UI module, so:
#  - usable for other human interfaces (touchscreen etc.), but:
#  - don't mix use of interfaces without adding some safeguards
#    ...if you do so, please share your implementation, thanks!
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
import gv, gp
import copy

DEFVOL = 1.0
DEFPRES = 127
gv.layerinit = [0, DEFVOL, DEFPRES]
sl_name = None
sl_details = []
sl_layer = 0
VOICE = 0
VOLUME= 1
PRES = 2

def init( voice=0 ):
	global sl_layer
	sl_layer = 0
	return [ voice, gv.layerinit[1], gv.layerinit[2] ]
gv.currlayers = [ init(1) ]

# load definition set
def load(val):
	global sl_name, sl_layer
	gv.currlayers = [ init( gv.currvoice ) ]
	if val != None:
		x = -2
		if isinstance(val,int):
			if val in range( len(gv.layernames) ):
				x = val
				gv.currlayername = gv.layernames[ x ]
		elif val == "":
			x = -1
			gv.currlayername = ""
		else:
			x = gp.getindex( val, gv.layernames, True, False )
			if x > -1:
				gv.currlayername = val
		if x > -2:
			sl_layer = 0
			sl_name = gv.currlayername
			if x > -1:
				for layer in gv.layers[x]:
					gv.currlayers.append( copy.deepcopy(layer) )
			if len(gv.currlayers) >1:
				sl_layer = 1
			else:
				sl_layer = 0
	else:
		gv.currlayername = ""
	return gv.currlayername

# Realtime change of presence
def Presence( layer, val=None, tot=127 ):
	if layer >= len( gv.currlayers ):
		return 0

	if val!=None:
		old = float( gv.currlayers[layer][2] )
		new = float( val ) / tot * 127
		if new == 0:
			new = 1		# We have to leak - and this also prevents div by zero
		gv.currlayers[layer][2] = int(round( new ))
		diff =  new / old
		for ps in gv.playingsounds:
			if ps.playingvoice() == gv.currlayers[layer][0]:
				ps.vel = ps.vel * diff

	return int(round( gv.currlayers[layer][2] / 12.7 ))

# Layer presence change via MIDI CC
def L0Pres( x, *z ): Presence( 0, x )  # L0 is the always present base sound
def L1Pres( x, *z ): Presence( 1, x )
def L2Pres( x, *z ): Presence( 2, x )
def L3Pres( x, *z ): Presence( 3, x )
def L4Pres( x, *z ): Presence( 4, x )
def L5Pres( x, *z ): Presence( 5, x )

gv.setMC(gv.LAYER0PRESENCE,L0Pres)
gv.setMC(gv.LAYER1PRESENCE,L1Pres)
gv.setMC(gv.LAYER2PRESENCE,L2Pres)
gv.setMC(gv.LAYER3PRESENCE,L3Pres)
gv.setMC(gv.LAYER4PRESENCE,L4Pres)
gv.setMC(gv.LAYER5PRESENCE,L5Pres)

# realtime velocity result
def layvel(layer, velocity):
	newvel = layer[1] * layer[2]/127 * velocity
	if newvel == 0:		# in order to fade in, a sound has to be there
		newvel = 1		# this starts it, be it as low as possible.
	if newvel > 127:
		newvel = 127	# prevent distortion
	return newvel


'''
	The interactive=UI configuration part
'''

def name(val=None):			# name of definition to save
	global sl_name
	if val!= None:
		sl_name = gp.no_delimiters(val.title())
	return sl_name

def details():
	global sl_details, sl_layer
	sl_details = []
	for ld in gv.currlayers:
		sl_details.extend([[ ld[0], ld[1] , int(round( ld[2]/12.7 )) ]])
	return sl_details

def layer(val=None):
	global sl_layer
	if val!=None:
		currlayer = sl_layer
		try:
			if val in range( 1, len(gv.currlayers) +1 ):
				if val == ( len(gv.currlayers) ):	# is this a new entry
					if gv.currlayers[val-1][0]:	# and is the last out of init stage
						gv.currlayers.append( init() )	# then create a new one
					else:
						val -= 1	# else go to the one in init stage
				sl_layer = val
			elif val == 0:
				currlayer = -1		# force change indication without change
		except:
			pass
		return currlayer != sl_layer
	return sl_layer

def voice(val=None):
	global sl_layer
	if (val!=None
	and sl_layer>0):
		currvoice = gv.currlayers[ sl_layer ][ VOICE ]
		try:
			if val == 0:
				gv.currlayers.remove( gv.currlayers[sl_layer] )
				if sl_layer >= len(gv.currlayers):
					sl_layer -= 1
				currvoice = -1	# force change indication
			elif val > 0:
				val -= 1
				for i in range(len(gv.voicelist)):      # filter out effects track and release samples
					if gv.voicelist[i][0] < 1:
						val += 1
				gv.currlayers[ sl_layer ][ VOICE ] = copy.deepcopy( gv.voicelist[val][0] )
		except:
			pass
		return currvoice != gv.currlayers[ sl_layer ][ VOICE ]
	return gv.currlayers[ sl_layer ][ VOICE ]

def volume(val=None):	# 0-30 1 dec float, 10 is neutral, stored value =/10
	if (val!=None
	and sl_layer>0):
		if isinstance(val,int):
			if val in range(31):
				gv.currlayers[ sl_layer ][ VOLUME ] = 1.0 * val / 10
	return int( gv.currlayers[ sl_layer ][ VOLUME ] * 10 )

def pres(val=None):		# 0-127 int, 127 is full presence
	if (val!=None
	and sl_layer>0):
		if isinstance(val,int):
			if val in range(11):
				gv.currlayers[ sl_layer ][ PRES ] = int(round( 12.7 * val ))
	return int(round( gv.currlayers[ sl_layer ][ PRES ] / 12.7 ))

def clear(val=None):
	global sl_layer
	if val!=None:
		if gp.parseBoolean(val):
			gv.currlayers = [ init( gv.currvoice ) ]
			sl_layer = 0
	return 0

def save(val=False):
	if (gp.parseBoolean(val)
	and sl_name!=""):

		'''
		We want to save a layerset and we know its name
		Replace or add the definition.
		Ignore two entry types:
		- the first entry: "the base voice" is not part of layers.csv
		- any entry with voice=0="delete this layer"
		will be ignored = not saved.
		This causes cleanup of csv's created manually (has pros and cons).
		'''
		idx = gp.getindex( sl_name, gv.layernames, onecol=True)
		upd = True
		layers = []
		if len(gv.currlayers) == 1:
			if sl_name == gv.currlayername:
				gv.layers.remove( gv.layers[idx] )
				gv.layernames.remove( gv.layernames[idx] )
			else:
				upd = False
		else:
			layers = []
			for layer in gv.currlayers:
				if layer[0] > 0:
					layers.append( layer )
			if idx >= 0:
				gv.layers[ idx ] = copy.deepcopy( layers )	# replace existing
			else:
				gv.layers.append( copy.deepcopy( layers ))
				gv.layernames.append( copy.deepcopy( sl_name ))
				gv.currlayername = sl_name

		'''
		Now save the stuff,
		while skipping "Default" entries duplicating the system default ("BOX")
		'''
		gp.samples2write()
		fname=gp.presetdir() + gv.LAYERS_DEF
		with open(fname, 'w') as layersfile:
			layersfile.write("Name,1st layer,2nd layer,3rd layer,4th layer,5th layer\n")
			for idx in range( len(gv.layernames) ):
				first = True
				line = gv.layernames[ idx ]
				for layer in gv.layers[ idx ]:
					if first:
						first = False
						continue
					line = "%s,%i" %( line, layer[0] )
					if layer[2] == DEFPRES:
						if layer[1] != DEFVOL:
							line = "%s:%.1f" %( line, layer[1] )
					else:
						line = "%s:%.1f:%i" %( line, layer[1], int(round( layer[2]/12.7 )) )
				layersfile.write('%s\n' %line )
		gp.samples2read()

	return 0
