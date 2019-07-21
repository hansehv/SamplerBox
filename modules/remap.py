###############################################################
#  Interactively adapt mappings on running samplerbox
#  - written for the webgui
#  - usable for other human interfaces (touchscreen etc..)
#  - don't mix use of interfaces without adding some safeguards
#    ...if you do so, please share your implementation, thanks!
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
import gv,subprocess

##########  N O T E   M A P P I N G   ##########
#
#  only parameter is a dictionary that may contain next fields (inote is mandatory, values indicate proper defaults):
#   {'SB_nm_inote': ['0'],		# index of key->midinote as defined in keynotes.csv
#    'SB_nm_onote': ['1'],      # midinote 0-127, plus -1=None and -2=Ctrl
#    'SB_nm_Q': ['1'],          # 1 indicates gui to translate to 12-tone names and 2 indicates 24-tone translation
#    'SB_nm_sav': ['No'],       # "yes" anywhere in string means save, any other value ignores
#    'SB_Notemap': ['0'],       # Index of notemap names (gv.notemaps)
#    'SB_nm_voice': ['0'],      # Index of voice names (gv.voicelist), so you can only define switches to know voices in this preset
#    'SB_nm_retune': ['0']}     # Retune value in cents, range -50 to +50
#
#  It can update:
#   - global fields related to above possible dictionary fields
#   - gv.notemapping[] - the current active map
#   - gv.notemap[] and gv.notemaps - the available maps while this preset is active
#   - notemap.csv in the preset directory - persistent definition 
#   In current implementation the last two are done at the same time (I see nor reason for split, please feedback f you disagree)
#
fractions=[[1,"Semi"],[2,"Quarter"]]
newnotemap=[]
def notes(fields):
	global newnotemap
	#print fields
	currinote=gv.SB_nm_inote
	gv.SB_nm_inote=int(gv.keynames[int(fields["SB_nm_inote"][0])][0])
	if currinote==gv.SB_nm_inote and currinote>-1:
		if "SB_nm_Q" in fields:
			gv.SB_nm_Q=int(fields["SB_nm_Q"][0])
			for j in xrange(len(gv.notemapping)):
				gv.notemapping[j][1]=gv.SB_nm_Q
		if "SB_nm_onote" in fields:		gv.SB_nm_onote=int(fields["SB_nm_onote"][0])-2
		if "SB_nm_retune" in fields:	gv.SB_nm_retune=int(fields["SB_nm_retune"][0])
		if "SB_nm_voice"  in fields:	gv.SB_nm_voice=int(fields["SB_nm_voice"][0])
		app=True
		rem=(gv.SB_nm_onote==gv.SB_nm_inote and gv.SB_nm_retune==0 and gv.SB_nm_voice==0)
		for i in xrange(len(gv.notemapping)):
			if currinote==gv.notemapping[i][0]:
				if rem:
					del gv.notemapping[i]
				else:
					gv.notemapping[i][2]=gv.SB_nm_onote
					gv.notemapping[i][3]=gv.SB_nm_retune
					gv.notemapping[i][4]=gv.SB_nm_voice
				app=False
				break
			if currinote<gv.notemapping[i][0] and not rem:
				gv.notemapping.insert(i,[currinote,gv.SB_nm_Q,gv.SB_nm_onote,gv.SB_nm_retune,gv.SB_nm_voice])
				app=False
				break
		if app and not rem:
			gv.notemapping.append([currinote,gv.SB_nm_Q,gv.SB_nm_onote,gv.SB_nm_retune,gv.SB_nm_voice])
	if "SB_nm_map"  in fields:	gv.SB_nm_map=fields["SB_nm_map"][0].title()
	else:						gv.SB_nm_map=""
	if "SB_nm_sav"  in fields and "yes" in fields["SB_nm_sav"][0].lower() and gv.SB_nm_map!="":
		newnotemap=[]
		changes_added=False
		j=0
		for i in range(len(gv.notemap)):
			if gv.notemap[i][0]!=gv.SB_nm_map:
				newnotemap.append(gv.notemap[i])
			else:
				if not changes_added:	# insert all existing/changed/new values at once
					notes_newmaplines()
					changes_added=True
		if not changes_added:
			notes_newmaplines()
			gv.notemaps.append(gv.SB_nm_map)
			gv.currnotemap=gv.SB_nm_map
		gv.notemap=newnotemap
		if gv.rootprefix=="":
			subprocess.call(['mount', '-vo', 'remount,rw', gv.samplesdir])
		fname=gv.samplesdir+gv.presetlist[gv.getindex(gv.PRESET,gv.presetlist)][1]+"/"+gv.NOTEMAP_DEF
		with open(fname, 'w') as mapfile:
			mapfile.write("Set,Fractions,Key,Note,Retune,Playvoice\n")
			for i in range(len(newnotemap)):
				note=gv.midinote2notename(newnotemap[i][3],newnotemap[i][1])
				key=newnotemap[i][2]
				j=gv.getindex("%d"%key,gv.keynames)
				if j>0: key=gv.keynames[j][1]
				mapfile.write("%s,%s,%s,%s,%s,%s\n" %(newnotemap[i][0],newnotemap[i][1],key,note,newnotemap[i][4],newnotemap[i][5]))
		if gv.rootprefix=="":
			subprocess.call(['mount', '-vo', 'remount,ro', gv.samplesdir])
def notes_newmaplines():
	global newnotemap
	for j in range(len(gv.notemapping)):
		values=[gv.SB_nm_map,gv.notemapping[j][1],gv.notemapping[j][0],gv.notemapping[j][2]]
		try:
			values.append(gv.notemapping[j][3])
			values.append(gv.notemapping[j][4])
		except: pass
		newnotemap.append(values)
	return
