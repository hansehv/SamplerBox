#
#  Read csv files from /boot/samplerbox
#
#  Base procedure reads in a given number of text fields,
#        after which remaining input is considered integer
#
#  Recognized delimiters      : comma, semicolon and tab
#  Characters removed/cleaned : space, quote (both single and double)
#  Line end characters        : linux and windows style
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
#   see docs at  http://homspace.nl/samplerbox
#   changelog in changelist.txt
#
import re, operator, copy
import gp, gv
sheet={}

def readcsv(ifile, numtxt=100, header=True):
	with open(ifile) as f:
		rows = []
		for line in f:
			row=[]
			if header:  # skip header line
				header=False
			else:
				# Split on common delimiters for csv after cleaning text and line separators
				inrow=re.split(',|;|\t',re.sub('"|\'|\n|\r', "", line))
				for i in range(len(inrow)):
					if inrow[i]=="":		# stop after emptycell
						if i==0:			# is this the first cell?
							i=-1			# then indicate empty row
						break;
					if inrow[i][0]=="#":	# allow=ignore for comments
						if i==0:			# is this the first cell?
							i=-1			# then indicate empty row
						break
					if i < numtxt:		  # Take the textfields as is
						row.append(inrow[i].strip())
					else:				   # Convert the rest to integer
						try:
							row.append(int(inrow[i].strip()))
						except:
							print ("%s: Found '%s' when expecting a digit, ignoring rest of line %s" %(ifile, inrow[i], inrow))
							break
				if i > -1:				  # just return filled row
					rows.append(row)
	return rows

def readchords(ifile):
	sheet=readcsv(ifile,1,False)
	gv.chordnote=[[0]]	 # single note
	gv.chordname=[""]
	for i in range(len(sheet)):
		if len(sheet[i]) > 1:	# skip useless lines
			gv.chordname.append(sheet[i][0])
			values=[]
			for j in range(1,len(sheet[i])):
				values.append(sheet[i][j])
			gv.chordnote.append(values)
	return 

def readscales(ifile):
	sheet=readcsv(ifile)
	gv.scalechord=[[0,0,0,0,0,0,0,0,0,0,0,0]]  # single notes
	gv.scalename=[""]
	for i in range(len(sheet)):
		gv.scalename.append(sheet[i][0])
		values=[]
		for j in range(1,len(sheet[i])):
			if sheet[i][j]=="0" or sheet[i][j]=="-":
				x=0
			else:
				try:
					x=gv.chordname.index(sheet[i][j])
				except:
					print ("%s: Chord '%s' not defined in scale '%s', fallback to single note" %(ifile,sheet[i][j],sheet[i][0]))
					gv.ConfigErr=True
					x=0
			values.append(x)
		gv.scalechord.append(values)
	return

def readcontrollerCCs(ifile):
	# controllerCCs: [wheel/button/pot/drawbarname, controller, data LSB (-1 if continuous controller)]
	sheet=readcsv(ifile,1)
	gv.controllerCCs=[[gv.UA,-1,-1]]  # define controller for unassigned controls
	for i in range(len(sheet)):
		if len(sheet[i])>2:	 # skip useless lines
			if gp.getindex(sheet[i][0],gv.controllerCCs)>-1:
				print ("%s: Controller %s already defined, ignored %s" %(ifile,sheet[i][0],sheet[i]))
			else:
				values=[]
				for j in range(3):
					values.append(sheet[i][j])
				gv.controllerCCs.append(values)
		else:
			print ("%s: ignored %s" %(ifile, sheet[i]))
			gv.ConfigErr=True
	return 

def readCCmap(ifile, override=False):
	# CCmap: [buttonindex, procedureindex , additional procedure parameter, voice]
	CCmap=[]
	try:
		sheet=readcsv(ifile)
		for i in range(len(sheet)):
			voice=0
			if override:
				x=sheet[i].pop(0)
				try:
					voice=int(x)
				except:
					print("%s: Invalid voice %s, ignoring %s" %(ifile, x, str(sheet[i])))
					gv.ConfigErr=True
					continue
			if sheet[i][0]!=gv.UA:	  # skip unassigned controllers
				values=[0,"",None,voice]
				x=gp.getindex(sheet[i][0],gv.controllerCCs)
				if x<0:
					print("%s: Controller %s not defined, ignoring %s" %(ifile, sheet[i][0], str(sheet[i])))
					gv.ConfigErr=True
					continue
				elif len(sheet[i])>1:	   # skip empty lines
					if sheet[i][1]!=gv.UA:  # skip unassigned controls
						if len(sheet[i])<4:
							print("%s: ignored %s" %(ifile, str(sheet[i])))
							gv.ConfigErr=True
							continue
						for j in range(len(CCmap)):
							if CCmap[j][0]==x and CCmap[j][3]==voice:
								print ("%s: Controller '%s' already mapped, ignored %s" %(ifile,gv.controllerCCs[x][0],sheet[i]))
								gv.ConfigErr=True
								continue
						if gp.getindex(sheet[i][3].lower(),["continuous","toggle","switch","switchon","switchoff"],True)<0:
							print("%s: Mode '%s' unrecognized, ignored: %s" %(ifile, sheet[i][3], str(sheet[i])))
							gv.ConfigErr=True
						elif (sheet[i][3].lower()!="continuous" and gv.controllerCCs[x][2]==-1 or sheet[i][3].lower()=="continuous" and gv.controllerCCs[x][2]!=-1):
							print("%s: Continuous/switch controller mapped to incompatible function, ignored: %s" %(ifile, str(sheet[i])))
							gv.ConfigErr=True
						else:
							values[0]=x	 # identify controller
							# Normalize/correct the input
							if sheet[i][1].upper()==gv.FIXED.upper():
								mc=sheet[i][2]
							else:
								mc=sheet[i][1]
								values[2]=sheet[i][2]
							y=gp.getindex(mc,gv.MC)
							if y>-1:
								values[1]=y
								CCmap.append(values)
							else:
								print("%s: Control '%s' unrecognized, ignored %s" %(ifile, mc, str(sheet[i])))
								gv.ConfigErr=True
	except:
		if not override:
			print("%s: No default controller mapping found" %(ifile))
	return CCmap

keynames=[]
def readkeynames(ifile):
	# keynames: [name of key/string/pad, midinote sent by this trigger]
	global keynames
	gv.keynames=[["-1","None"]]
	keynames=[]
	gv.drumpadmap=[]
	try:		# giving keys/strings/triggers a name is optional
		sheet=readcsv(ifile)
		for i in range(len(sheet)):
			values=[]
			valucas=[]
			valuesDP=[]
			valuesCC=[]
			if len(sheet[i])>1:	 # skip useless lines
				if gp.getindex(sheet[i][0],gv.keynames)>-1:
					print ("%s: Key %s already defined, ignored %s" %(ifile,sheet[i][0],sheet[i]))
				else:
					try:
						values.append(sheet[i][1])
						values.append(sheet[i][0])
						gv.keynames.append(values)
						valucas.append(sheet[i][0].upper())
						valucas.append(sheet[i][1])
						keynames.append(valucas)
						valuesCC.append(sheet[i][0])
						valuesCC.append(gv.NOTES_CC)
						valuesCC.append(int(sheet[i][1]))
						gv.controllerCCs.append(valuesCC)
						if len(sheet[i])>2: # drumpad remap definition
							valuesDP.append(int(sheet[i][2]))
							valuesDP.append(int(sheet[i][1]))
							gv.drumpadmap.append(valuesDP)
					except:
						print ("%s: %s contains errors, partly processed" %(ifile, sheet[i]))
			else:
				print(("%s: ignored %s" %(ifile, sheet[i])))
				gv.ConfigErr=True
	except:
		pass	# giving keys/strings/triggers a name is optional
	return 

def readnotemap(ifile):
	# notemap: [set, fractions, key, note, retune, playvoice]
	global keynames
	gv.notemap=[]
	gv.notemaps=[]
	try:		# note mapping is optional
		sheet=readcsv(ifile,4)
		for i in range(len(sheet)):
			if len(sheet[i])>3:	 # skip useless lines
				values=["",1,0,-1,0,0,0]
				values[0]=format(sheet[i][0]).title()   # force num to string and normalize upper/lowercase usage
				if values[0]=="":
					print ("%s: Sets must have a name, ignored %s" %(ifile, sheet[i]))
					continue
				try:
					values[1]=int(sheet[i][1])
					if values[1]<1 or values[1]>2:
						print ("%s: invalid fractions, ignored %s" %(ifile, sheet[i]))
				except:
					print ("%s: invalid fractions, ignored %s" %(ifile, sheet[i]))
					continue
				try:
					values[2]=int(sheet[i][2])
				except:
					ucas=sheet[i][2].upper()
					x=gp.getindex(ucas,keynames)
					if x<0:
						print(("%s: keyname '%s' not defined, ignored %s" %(ifile, sheet[i][2], sheet[i])))
						continue
					else:
						values[2]=int(gv.keynames[x+1][0])
				if len(gv.notemap)>0:
					for j in range(len(gv.notemap)):
						if values[0]==gv.notemap[j][0] and values[2]==gv.notemap[j][2]:
							print ("%s: duplicate midinote %d in notemap %s, ignored %s" %(ifile, values[2], values[0], sheet[i]))
							break
					if j<len(gv.notemap)-1:
						continue
				try:
					values[3]=int(sheet[i][3])
				except:
					if sheet[i][3].title()=="Ctrl":
						values[3]=-2
					elif sheet[i][3].title()=="None":
						values[3]=-1
					else:
						midinote=gv.notename2midinote(sheet[i][3],values[1])
						if midinote>-1:
							values[3]=midinote
						else:
							print ("%s: invalid notename '%s', ignored %s" %(ifile, sheet[i][3], sheet[i]))
							continue
				if len(sheet[i])>4: # the values are optional
					try:
						values[4]=int(sheet[i][4])
						values[5]=int(sheet[i][5])
						values[6]=int(sheet[i][6])
					except:
						pass
				gv.notemap.append(values)
				if gp.getindex(values[0],gv.notemaps,True)<0:
					gv.notemaps.append(values[0])
			else:
				print ("%s: ignored %s" %(ifile, sheet[i]))
				gv.ConfigErr=True
		gv.notemap.sort(key=operator.itemgetter(0,2))   # sort on: map->input(midi)key
	except:
		pass	# notemapping is optional
	return

def readMTchannelmap(ifile):
	# MTchannelmap: [name of MTdevice/smf/mid/song, channel used in MTdevice/smf, progchange in that channel, voice to use]
	# Channels are the "human channels", so range 1-16 making default=1 and drum=10
	# Similar for the program changes, so piano=1
	# But internally SMF files are zero based, so range 0-15 - take care when debugging
	# Zero values used in channel and prog function as wildcards, for voice it means "first available" (usually voice=1).
	gv.voicemap=[]  # name,from,to
	try:
		sheet=readcsv(ifile,1)
		for i in range(len(sheet)):
			if len(sheet[i])>3:	 # skip useless lines
				if sheet[i][1]>-1 and sheet[i][1]<17 and sheet[i][2]>-1 and sheet[i][2]<128 and sheet[i][3]>-1:
					ok=True
					for v in gv.voicemap:
						if v[0]==sheet[i][0] and v[1]==sheet[i][1] and v[2]==sheet[i][2]:
							print ("%s: ignored %s, previously defined" %(ifile, sheet[i]))
							ok=False
					if ok: gv.voicemap.append(sheet[i])
				else:
					print ("%s: ignored %s as at least one value is out of range" %(ifile, sheet[i]))
					gv.ConfigErr=True
			else:
				print ("%s: ignored %s" %(ifile, sheet[i]))
		gv.voicemap.sort(key=operator.itemgetter(0,1))  # sort on: map->input(midi)channel
	except:
		pass	# this is all optional, default is channel#->voice#
	return 

def readmenu(ifile):
	# menu: [Menu, Item, Show as, Spectype, Spec1, Spec2]
	import UI,menu
	sheet=readcsv(ifile,100,False)
	menu.maintxt=sheet[0][0]
	currmenu=menu.maintxt
	for i in range(1,len(sheet)):
		if len(sheet[i])>2:	 # skip useless lines
			values=["","",""]
			if sheet[i][0]!="-":
				if currmenu!="": currmenu=sheet[i][0]
			values[0]=currmenu
			if sheet[i][1] in UI.procs and UI.procs[sheet[i][1]][0]=="w":
				values[1]=sheet[i][1]
				values[2]=values[1] if len(sheet[i])<4 or sheet[i][3]=="" else sheet[i][3]
				if sheet[i][2].lower()=="boolean": values.append("boolean")
				elif sheet[i][2] in UI.procs and UI.procs[sheet[i][2]][0]!="w":
					values.append(sheet[i][2])
				else:
					if not isinstance(sheet[i][2],str): values=None
					else:
						spec=sheet[i][2].split('-')
						if len(spec)<2: values=None
						elif spec[0].isdigit() and spec[1].isdigit():
							values.append(int(spec[0]))
							values.append(int(spec[1]))
							if len(spec)>2 and spec[2].isdigit():values.append(int(spec[2]))
							else: values.append(1)
						else: values=None
				if values: menu.definition.append(values)
				else: print ("%s: Don't understand spec %s, ignored %s" %(ifile,sheet[i][2],sheet[i]))
			else:
				print("%s: Item %s unknown or not writable, ignored %s" %(ifile,sheet[i][1],sheet[i]))
		else:
			print ("%s: ignored %s" %(ifile, sheet[i]))
			gv.ConfigErr=True
	menu.init()
	return 

FXpresets_box = {}
gv.FXpresets = {}
def readFXpresets(ifile, override=False):
	# FXpresets: [Presetname, Parameter, Value]
	global FXpresets_box
	if override:
		gv.FXpresets = copy.deepcopy( FXpresets_box )
	try:
		sheet = readcsv( ifile, 100 )
		for i in range( len(sheet) ):
			if len(sheet[i]) > 2:	 # skip useless lines
				preset = sheet[i][0]
				presetl = preset.lower()
				if presetl in ["none", "box", "set"]:
					if ( presetl == "none"
					or   (  (presetl == "box" and override)
						 or (presetl == "set" and not override)
						 )
					   ):
						print ("%s: ignored %s because %s this cannot be set (now)" %(ifile, sheet[i], preset))
						gv.ConfigErr=True
						continue
					preset = "Default"
				if sheet[i][1] not in gv.procs_alias:
					print ("%s: ignored %s because %s is not a valid FX parameter" %(ifile, sheet[i], sheet[i][1]))
					gv.ConfigErr=True
					continue
				val = sheet[i][2]
				if sheet[i][2].isdigit():
					val = int(val)
				if preset in gv.FXpresets:
					gv.FXpresets[preset].update( {sheet[i][1]: val} )
				else:
					gv.FXpresets.update({ preset: {sheet[i][1]: val} })
			else:
				print ("%s: ignored %s" %(ifile, sheet[i]))
	except:
		pass	# this is all optional, defaults are hardcoded
	gv.FXpresetnames = ["None"]
	for key in gv.FXpresets.keys():
		gv.FXpresetnames.append(key)
	if not override:
		FXpresets_box = copy.deepcopy( gv.FXpresets )
		gv.FXpreset_last="None"
	return 

def readlayers(ifile):
	gv.layers=[]		# layers
	gv.layernames=[]	# layernames	
	try:
		sheet=readcsv(ifile,100,False)
		for i in range(len(sheet)):
			if len(sheet[i]) > 1:	# skip useless lines
				values=[]
				for j in range(1,len(sheet[i])):
					OK = False
					if sheet[i][j].isdigit():
						values.append( [ int(sheet[i][j]), 1 ] )
						OK = True
					else:
						try:
							vals = sheet[i][j].split(":")
							if len(vals) == 2:
								values.append( [ int(vals[0]), float(vals[1]) ] )
								OK = True
						except:
							pass
					if not OK:
						print ("%s: ignored %s,%s because this is not a valid 'voice:velocity' defintion" %(ifile, sheet[i], sheet[i][j]))
				if values:
					gv.layernames.append(sheet[i][0])
					gv.layers.append(values)
	except:
		pass	# layers are optional
	return 
