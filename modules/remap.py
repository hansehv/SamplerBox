###############################################################
#  Interactively adapt mappings on running samplerbox
#  - written for the UI module, so:
#  - usable for other human interfaces (touchscreen etc.), but:
#  - don't mix use of interfaces without adding some safeguards
#    ...if you do so, please share your implementation, thanks!
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
import gv,subprocess

##########  G e n e r i c   p r o c s   ##########

def no_delimiters(raw):	# rude but effective for failsafe operation :-)
	return raw.replace(",",".").replace(";",":").replace("\t"," ")

##########  N O T E   M A P P I N G   ##########

fractions=[[1,"Semi"],[2,"Quarter"]]
newnotemap=[]
actnotemap="%$@"
currinote=0
nm_inote=-1
nm_onote=None
nm_Q=None
nm_retune=None
nm_voice=None
nm_unote=None
nm_map=None

def notes_sync():
	global actnotemap,nm_inote,nm_onote,nm_unote,nm_Q,nm_retune,nm_voice,nm_map
	if actnotemap!=gv.currnotemap:
		actnotemap=gv.currnotemap
		nm_map=actnotemap
	nm_onote=-1
	if len(gv.notemapping)>0:	nm_Q=gv.notemapping[0][1]
	else:						nm_Q=1
	nm_retune=0
	nm_voice=0
	nm_unote=2
	if nm_inote>-1:
		i=gv.getindex(nm_inote,gv.notemapping)
		if i>-1:
			nm_Q=gv.notemapping[i][1]
			nm_onote=gv.notemapping[i][2]
			nm_retune=gv.notemapping[i][3]
			nm_voice=gv.notemapping[i][4]
			nm_unote=gv.notemapping[i][5]
		else:
			nm_onote=nm_inote

def notes_consolidate():
	global currinote,nm_inote,nm_Q,nm_onote,nm_retune,nm_voice
	app=True
	rem=(nm_onote==nm_inote and nm_retune==0 and nm_voice==0)
	for i in xrange(len(gv.notemapping)):
		if currinote==gv.notemapping[i][0]:
			if rem:
				del gv.notemapping[i]
			else:
				gv.notemapping[i][2]=nm_onote
				gv.notemapping[i][3]=nm_retune
				gv.notemapping[i][4]=nm_voice
				gv.notemapping[i][5]=nm_unote
			app=False
			break
		if currinote<gv.notemapping[i][0] and not rem:
			gv.notemapping.insert(i,[currinote,nm_Q,nm_onote,nm_retune,nm_voice,nm_unote])
			app=False
			break
	if app and not rem:
		gv.notemapping.append([currinote,nm_Q,nm_onote,nm_retune,nm_voice,nm_unote])
		
def notes_Q(val=None):							# Fractions or index of qFractions
	global nm_Q
	if val!=None:
		if isinstance(val,(int,long)):
			nm_Q=val
		else:
			for Q in fractions:
				if Q[1]==val:
					nm_Q=Q[0]
					break
		for j in xrange(len(gv.notemapping)):
			gv.notemapping[j][1]=nm_Q
	return nm_Q
def notes_inote(val=None):						# keyname or index in KeyNames for keyboardnote
	global currinote,nm_inote
	if val!=None:
		currinote=nm_inote
		if isinstance(val,(int,long)):
			nm_inote=int(gv.keynames[val][0])
		else:
			for key in gv.keynames:
				if key[1]==val:
					nm_inote=int(key[0])
					break
		return(currinote==nm_inote and currinote>-1)
	return nm_inote
def notes_onote(val=None):						# midinote or notename, with specials -2="Ctrl" and -1="None"
	global nm_Q,nm_onote,nm_unote
	curronote=nm_onote
	if val!=None:
		if isinstance(val,(int,long)):
			nm_onote=val-2
		else:
			nm_onote=gv.notename2midinote(val,nm_Q)
			if nm_onote<-3: nm_onote=-1
		if curronote!=nm_onote: nm_unote=0
	return nm_onote
def notes_retune(val=None):						# -50 - +50 (0 is neutral)
	global nm_retune
	if val!=None:
		try:
			if val>-51 and val<51:
				nm_retune=val
		except: pass
	return nm_retune
def notes_voice(val=None):		       			# (integer) index of Voicelist to switch to or (string) voice
	global nm_voice
	if val!=None:
		try:
			if isinstance(val,(int,long)):
				if val<0:		# "no voice change"?
					nm_voice=0
				else:
					for i in range(len(gv.voicelist)):      # filter out effects track and release samples
						if gv.voicelist[i][0]<1: val+=1
					nm_voice=gv.voicelist[val][0]
			else:
				nm_voice=int(re.search(r'\d+', val).group())
		except: pass
	return nm_voice
def notes_unote(val=None):						# index of an interface defined table/note to present the output note (when user prefers Bb above A# etcetera)
	global nm_unote
	if val!=None:
		nm_unote=0
		if isinstance(val,(int,long)):
			nm_unote=val
		else:
			try: nm_unote=int(val)
			except: pass
	return nm_unote

def notes_map(val=None):						# name of map to save
	global nm_map
	if val!=None:
		nm_map=no_delimiters(val.title())
	return nm_map
def notes_clear(val=None):
	if val!=None:
		if gv.parseBoolean(val):
			gv.notemapping=[]
	return False
def notes_sav(val=None):						# boolean, but as read variable it's always 0=no/false
	global newnotemap, nm_map
	if val!=None:
		if gv.parseBoolean(val) and nm_map!="":	# do we want to save a map and do we know the name to save it ?
			newnotemap=[]
			changes_added=False
			j=0
			for i in range(len(gv.notemap)):
				if gv.notemap[i][0]!=nm_map:
					newnotemap.append(gv.notemap[i])
				else:
					if not changes_added:	# insert all existing/changed/new values at once
						notes_newmaplines()
						changes_added=True
			if not changes_added:
				notes_newmaplines()
				gv.currnotemap=nm_map
			gv.notemap=newnotemap
			gv.notemaps=[]
			for m in gv.notemap:
				if m[0] not in gv.notemaps:
					gv.notemaps.append(m[0])
			if nm_map not in gv.notemaps:
				nm_map=""
			if gv.rootprefix=="": subprocess.call(['mount', '-vo', 'remount,rw', gv.samplesdir])
			else: print "Not running dedicated, so no remount as we're most likely already R/W"
			fname=gv.samplesdir+gv.presetlist[gv.getindex(gv.PRESET,gv.presetlist)][1]+"/"+gv.NOTEMAP_DEF
			with open(fname, 'w') as mapfile:
				mapfile.write("Set,Fractions,Key,Note,Retune,Playvoice,unote\n")
				for i in range(len(newnotemap)):
					note=gv.midinote2notename(newnotemap[i][3],newnotemap[i][1])
					key=newnotemap[i][2]
					j=gv.getindex("%d"%key,gv.keynames)
					if j>0: key=gv.keynames[j][1]
					mapfile.write('%s,%s,%s,%s,%s,%s,%s\n' %(newnotemap[i][0],newnotemap[i][1],key,note,newnotemap[i][4],newnotemap[i][5],newnotemap[i][6]))
			if gv.rootprefix=="": subprocess.call(['mount', '-vo', 'remount,ro', gv.samplesdir])
	return 0
def notes_newmaplines():
	global newnotemap
	for j in range(len(gv.notemapping)):
		values=[nm_map,gv.notemapping[j][1],gv.notemapping[j][0],gv.notemapping[j][2]]
		try:
			values.append(gv.notemapping[j][3])
			values.append(gv.notemapping[j][4])
			values.append(gv.notemapping[j][5])
		except: pass
		newnotemap.append(values)
	return
