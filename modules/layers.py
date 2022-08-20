###############################################################
# Sound layers (add extra voices to the active note)
# Process incorporated in the note-on logic, so rather cheap
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
import gv

def Presence( layer, val=None, tot=127 ):
	if layer >= len( gv.currlayers ):
		return 0

	if val!=None:
		old = float( gv.currlayers[layer][2] )
		new = float( val ) / tot * 127
		if new == 0:
			new = 1		# We have to leak and this also prevents div by zero
		gv.currlayers[layer][2] = int(round( new ))
		diff =  new / old
		for ps in gv.playingsounds:
			if ps.playingvoice() == gv.currlayers[layer][0]:
				ps.vel = ps.vel * diff

	return int(round( gv.currlayers[layer][2] / 12.7 ))

# extra voice layers via MIDI CC
def L0Pres( x, *z ): Presence( 0, x )  # L0 is the always present base sound
def L1Pres( x, *z ): Presence( 1, x )
def L2Pres( x, *z ): Presence( 2, x )
def L3Pres( x, *z ): Presence( 3, x )
def L4Pres( x, *z ): Presence( 4, x )
def L5Pres( x, *z ): Presence( 5, x )

# announce the procs to modules
gv.setMC(gv.LAYER0PRESENCE,L0Pres)
gv.setMC(gv.LAYER1PRESENCE,L1Pres)
gv.setMC(gv.LAYER2PRESENCE,L2Pres)
gv.setMC(gv.LAYER3PRESENCE,L3Pres)
gv.setMC(gv.LAYER4PRESENCE,L4Pres)
gv.setMC(gv.LAYER5PRESENCE,L5Pres)

def layvel(layer, velocity):
	newvel = layer[1] * layer[2]/127 * velocity
	if newvel == 0:		# in order to fade in, a sound has to be there
		newvel = 1		# this starts it, be it as low as possible.
	if newvel > 127:
		newvel = 127	# prevent distortion
	return newvel
