###############################################################
#  Read and route midifiles to samplerbox via midi through
#
#  The sequencer part is served by Alsa's built-in sequencer.
#
#  Conversion of midifile info into events for alsa is done via
#  an adapted version of python midi, you can find this on:
#  https://github.com/hansehv/python-midi/tree/Adapt-for-SamplerBox
#  Original: https://github.com/vishnubob/python-midi/
#
#  This module selects the files and fires them on request.
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################

import sys,os,gv,time,threading,re
if gv.rootprefix!="":sys.path.append('%s/root/python-midi/build/lib.linux-armv7l-2.7/' %gv.rootprefix)
import midi
import midi.sequencer as sequencer
usleep = lambda x: time.sleep(x/1000000.0)
msleep = lambda x: time.sleep(x/1000.0)

client   	= 14
port    	= 0
gv.smfseqs	= {}
gv.smfdrums = {}
gv.currsmf	= 0
gv.smftempo	= 240
streamtempo	= 240
#actvoicemap = "" ==> gv.smfseqs[gv.currsmf][5]
loopit		= False
stopit		= False
seq			= midi.sequencer.SequencerWrite(alsa_sequencer_name='SMFplayer',alsa_port_name="Through %d:%d" %(client,port))

gv.MULTI_TIMBRALS["Midi Through %d:%d" %(client,port)]=[0]*16		# init program=voice per channel#
gv.MULTI_TIMBRALS["Midi Through:Midi Through Port-%d %d:%d" %(port, client,port)]=[0]*16
def issending(src):
	if "Midi Through" in src and "%d:%d" %(client,port) in src and gv.currsmf>0:
		return(True)
	return (False)

# Events supported by python midi but unhonoured by samplerbox are not sent to reduce traffic
supported_events={
	#"AfterTouchEvent",
	#"ChannelAfterTouchEvent",
	#"ChannelPrefixEvent",
	#"ControlChangeEvent",
	#"CopyrightMetaEvent",
	#"CuePointEvent",
	#"EventRegistry",
	#"InstrumentNameEvent",
	#"KeySignatureEvent",
	#"LyricsEvent",
	#"MarkerEvent",
	#"MetaEventWithText",
	"NoteEvent",
	"NoteOffEvent",
	"NoteOnEvent",
	#"PitchWheelEvent",
	#"PortEvent",
	"ProgramChangeEvent",
	#"ProgramNameEvent",
	"SequenceNumberMetaEvent",
	#"SequencerSpecificEvent",
	"SetTempoEvent",
	#"SmpteOffsetEvent",
	#"SysexEvent",
	#"TextMetaEvent",
	#"TimeSignatureEvent",
	"TrackLoopEvent",
	#"TrackNameEvent",	# This is in fact honoured during load, but ignored at playtime
	#"UnknownMetaEvent",
	"EndOfTrackEvent"}

# ----------------------------------------------------------------------
#		M I D I		S T R E A M S
# ----------------------------------------------------------------------
def getvalue(parm,data,comma=True):
	lookfor="%s="%parm
	i=data.find(lookfor)+len(lookfor)
	if not comma:
		return(data[i:])
	return(data[i:i+data[i:].find(",")])

def load(line,dirname, fname, smfseq, voicemap):
	channels={}
	v=", " if gv.DefinitionErr != "" else ""
	if smfseq<1 or smfseq>127:
		print "Skipped midifile %d:%s, out boundaries (1-127)" %(smfseq,fname)
		gv.DefinitionErr="%s%s%d" %(gv.DefinitionErr,v,line)
	elif smfseq in gv.smfseqs:
		print "Skipped midifile %d:%s, already defined via %d:%s" %(smfseq,fname,smfseq,gv.smfseqs[smfseq][0])
		gv.DefinitionErr="%s%s%d" %(gv.DefinitionErr,v,line)
	else:
		try:
			events=[]
			(song,t)=os.path.splitext(fname)
			stream=midi.read_midifile(os.path.join(dirname, fname))
			stream.make_ticks_abs()
			for track in stream:
				t=""
				for event in track:
					msg=re.split('\.|\(',"%s"%event)[1]
					data=re.split('\.|\(',"%s"%event)[2]
					if msg=="NoteOnEvent":
						c=int(getvalue("channel",data))
						if c not in channels:
							channels[c]=["Channel %d"%(c+1),True,[]]
						else:
							channels[c][0]=t if t!="" else "Channel %d"%(c+1)
							channels[c][1]=True
						if c==9:
							n=int(getvalue("data",data)[1:])
							if n in gv.smfdrums:
								if song not in gv.smfdrums[n]: gv.smfdrums[n].append(song)
							else:
								gv.smfdrums[n]=[song]
					elif msg=="TrackNameEvent":
						t=getvalue("text",data)[1:-1]
					elif msg=="EndOfTrackEvent":
						t=""
					elif msg=="ProgramChangeEvent":
						c=int(getvalue("channel",data))
						p=int(getvalue("data",data,False)[1:-2])+1
						if c not in channels:
							channels[c]=["Channel %d"%(c+1),False,[p]]
						else:
							channels[c][2].append(p)
					#elif msg in ["InstrumentNameEvent","ProgramNameEvent"]: #debug for future development
					#	print msg, data
					if msg in supported_events:
						events.append(event)
					#else: print "%s skipped %s" %(fname,event) #debug
			events.sort()
			if voicemap=="": voicemap=song
			voices=[]	# inventory of used channels and optional descriptions
			print "SMF=1%d=%s, voicemap=%s sends notes on channels:"%(smfseq,fname,voicemap)
			for key, value in channels.iteritems():
				t=[key,value]
				voices.append(t)
				l=""; c=""; s=""
				if value[1]:
					for v in value[2]:
						if c!="":s="s"
						l="%s%s%d"%(l,c,v)
						c=','
					print " - %d='%s' using voice%s %s" %(key+1,value[0],s,l)
			gv.smfseqs[smfseq]=[fname,stream.resolution,events,voices,voicemap]
		except:
			print"SMFplayer: error reading %s in %s" %(fname,dirname)

def drumlist():
	print "Drum sounds used:"
	for i in sorted (gv.smfdrums.keys()):
		print" - %d in %s"%(i,gv.smfdrums[i])
def seqlist():
	smflist=[]
	for key, value in gv.smfseqs.iteritems():
		smflist.append([key,value[0],value[3],value[4]])
	return(smflist)

# ----------------------------------------------------------------------
#		C O N T R O L S
# ----------------------------------------------------------------------

def play(x,*z):
	smfseq=int(x)
	if gv.currsmf==0:
		if smfseq>0:
			if smfseq in gv.smfseqs:
				#print "SMFplay %s, res=%d, %s" %(gv.smfseqs[smfseq][0],gv.smfseqs[smfseq][1],gv.smfseqs[smfseq][3])
				gv.currsmf=smfseq
			else:
				print "Midi sequence %d not in sample set" %smfseq
	else:
		if smfseq==gv.currsmf:
			stop()

def loop(x,*z):
	global loopit
	if loopit:
		loopit=False
	else:
		loopit=True

def stop(*z):
	global stopit,loopit
	if loopit:	loopit=False
	else:
		stopit=True
		while gv.currsmf>0:
			time.sleep(.01)
        for i in gv.playingnotes:			# What's playing at stop time ?
            if i<gv.MTCHNOTES: continue		# Skip main controller/keyboard
            for m in gv.playingnotes[i]:	# But remove our notes, as
				m.fadeout()					# the player may have had
				gv.playingnotes[i]=[]		# note-off's pending...

def tempo(x,*z):
	global streamtempo
	gv.smftempo=int(streamtempo*(1+(-1+2.0*x/128)))
	if gv.smftempo<1: gv.smftempo=1
	seq.change_tempo(gv.smftempo)	# implicitely executes seq.drain()

gv.setMC(gv.SMFS,play)
gv.setMC(gv.SMFLOOP,loop)
gv.setMC(gv.SMFSTOP,stop)
gv.setMC(gv.SMFTEMPO,tempo)

# ----------------------------------------------------------------------
#		P L A Y E R		T H R E A D
# ----------------------------------------------------------------------

def player():
	global seq,loopit,stopit,streamtempo,actvoicemap
	seq.subscribe_port(client, port)
	while True:
		if gv.currsmf>0:
			print "SMFplay %s, res=%d, %s" %(gv.smfseqs[gv.currsmf][0],gv.smfseqs[gv.currsmf][1],gv.smfseqs[gv.currsmf][3])
			streamtempo=120		# default in sequencer, don't see use making this a parameter
			gv.smftempo=streamtempo
			seq.init_tempo(gv.smfseqs[gv.currsmf][1])
			stopit=False
			while True:
				seq.start_sequencer()
				while True:
					for event in gv.smfseqs[gv.currsmf][2]:
						if stopit: break
						msg=re.split('\.|\(',"%s"%event)[1]
						if msg=="SetTempoEvent":
							data=re.split('\.|\(',"%s"%event)[2]
							i=data.find("data=")+5
							j=data[i+1:i+data[i:].find("]")].replace(" ", "").split(',')
							streamtempo=60000000/(int(j[0])*65536+int(j[1])*256+int(j[2]))
						buf = seq.event_write(event, False, False, True)
						if buf == None:
							#print "seq buffer empty"
							#usleep(10)
							continue
						if buf < seq.output_buffer_size*.80: # <==
							msleep(5) # <==
							if buf < 1000:
								#print "seq buffer repleted"
								msleep(500)
					while event.tick > seq.queue_get_tick_time():
						if stopit: break
						seq.drain()
						msleep(500)
					break
				seq.drop_output()
				seq.stop_sequencer()
				if not loopit:
					break
			print "SMFplay finished %s" %gv.smfseqs[gv.currsmf][0]
			# ===> reset voicemap, either default or none
			gv.currsmf=0
		msleep(30)

SMFplayThread = threading.Thread(target=player)
SMFplayThread.daemon = True
SMFplayThread.start()
