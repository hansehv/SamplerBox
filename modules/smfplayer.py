###############################################################
#  Read and route midifiles to samplerbox via midi through
#  Record in 1-track format=1 midifiles
#
#  The sequencer part is served by Alsa's built-in sequencer.
#
#  Conversion of midifile info into events for alsa as well as
#  writing of midifiles is done via an adapted python midi:
#            https://github.com/hansehv/python-midi
#  Original: https://github.com/vishnubob/python-midi
#
#  This module selects the files and fires them on request
#  and records events + saves files on request.
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################

import sys,os,time,threading,re
import gp,gv
#if gv.rootprefix!="":sys.path.append('%s/root/python-midi/build/lib.linux-armv7l-2.7/' %gv.rootprefix)
import midi
import midi.sequencer as sequencer
usleep = lambda x: time.sleep(x/1000000.0)
msleep = lambda x: time.sleep(x/1000.0)

# player globals
client   	= 14
port    	= 0
gv.smfseqs	= {}
gv.currsmf	= 0
gv.smftempo	= 240
streamtempo	= 240
#actvoicemap = "" ==> gv.smfseqs[gv.currsmf][5]
loopit		= False
stopit		= False

# recorder globals
recordedSong	= "recorded"
recorder		= None
resolution		= 240
bpm				= 120
tickusecs		= None
lastevent		= None
record_controls = [ \
		gp.getindex(gv.SMFRECSTART,gv.MC), \
		gp.getindex(gv.SMFRECABORT,gv.MC), \
		gp.getindex(gv.SMFRECSAVE,gv.MC) \
		]

# instantiate classes for both the playing and the file writing
seq			= midi.sequencer.SequencerWrite(alsa_sequencer_name='SMFplayer',alsa_port_name="Through %d:%d" %(client,port))
#rec			= midi.fileio.buffer_write_event

gv.MULTI_TIMBRALS["Midi Through %d:%d" %(client,port)]=[0]*16		# init program=voice per channel#
gv.MULTI_TIMBRALS["Midi Through:Midi Through Port-%d %d:%d" %(port, client,port)]=[0]*16
def issending(src):
	if "Midi Through" in src and "%d:%d" %(client,port) in src:
		return(True)
	return (False)

# Events supported by python midi but unhonoured by samplerbox are not processed to reduce traffic
# Currently recording supports more than playing (...), concerns 11=CC and 14=Pitchbend
supported_events={
	#"AfterTouchEvent",
	#"ChannelAfterTouchEvent",
	#"ChannelPrefixEvent",
	"ControlChangeEvent": [11, midi.ControlChangeEvent],
	#"CopyrightMetaEvent",
	#"CuePointEvent",
	#"EventRegistry",
	#"InstrumentNameEvent",
	#"KeySignatureEvent",
	#"LyricsEvent",
	#"MarkerEvent",
	#"MetaEventWithText",
	#"NoteEvent",
	"NoteOffEvent": [8, midi.NoteOffEvent],
	"NoteOnEvent": [9, midi.NoteOnEvent],
	"PitchWheelEvent": [14, midi.PitchWheelEvent],
	#"PortEvent",
	"ProgramChangeEvent": [12, midi.ProgramChangeEvent],
	#"ProgramNameEvent",
	#"SequenceNumberMetaEvent",
	#"SequencerSpecificEvent",
	"SetTempoEvent": [200, midi.SetTempoEvent],
	#"SmpteOffsetEvent",
	#"SysexEvent",
	#"TextMetaEvent",
	#"TimeSignatureEvent",
	#"TrackLoopEvent",
	#"TrackNameEvent",	# This is in fact honoured during load, but ignored at playtime
	#"EndOfTrackEvent",	# This is in fact honoured during load, but ignored at playtime
	#"UnknownMetaEvent",
	}

player_exceptions=[11,14]

supported_msgs = {}
for m in supported_events:
	if supported_events[m][0] > -1:
		supported_msgs[ supported_events[m][0] ] = m

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
				print("Midi sequence %d not in sample set" %smfseq)
	else:
		if smfseq==gv.currsmf:
			stop()

def loop(*z):
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
		gv.CallbackActive = False		# Callback doesn't care about housekeeping
		while gv.currsmf>0:
			time.sleep(.01)
	for i in gv.playingnotes:			# What's playing at stop time ?
		if i<gv.MTCHNOTES: continue		# Skip main controller/keyboard
		for m in gv.playingnotes[i]:		# But remove our notes, as
			m.fadeout()			# the player may have had
			gv.playingnotes[i]=[]		# note-off's pending...

def tempo(x,*z):
	global streamtempo
	gv.smftempo=int(streamtempo*(1+(-1+2.0*x/128)))
	if gv.smftempo<1:
		gv.smftempo=1
	seq.change_tempo(gv.smftempo)	# implicitely executes seq.drain()

def start_record(*z):
	global recorder, tickusecs, resolution, bpm, lastevent
	if not gv.MidiRecorder:
		usecs_per_beat = 60 * 1000000 / bpm
		tickusecs = usecs_per_beat / resolution
		recorder = midi.buffered_write_prepare(recorder)
		lastevent = None
		gv.MidiRecorder = record_event
		print ("MIDI recording started")

def cancel_record(*z):
	gv.MidiRecorder = False
	print ("MIDI recording canceled")

def songname (name, *z):
	global recordedSong
	# some testing..?
	recordedSong = name

def save_record(*z):
	global resolution, recordedSong
	if gv.MidiRecorder:
		gv.MidiRecorder = False
		gp.samples2write()
		fname = gp.presetdir() + recordedSong + ".mid"
		midi.buffered_write_finish( recorder, resolution, "%s" %fname )
		gp.samples2read()
		print ( "MIDI recording saved %s" %fname )

gv.setMC(gv.SMFS,play)
gv.setMC(gv.SMFLOOP,loop)
gv.setMC(gv.SMFSTOP,stop)
gv.setMC(gv.SMFTEMPO,tempo)
gv.setMC(gv.SMFRECSTART,start_record)
gv.setMC(gv.SMFRECABORT,cancel_record)
gv.setMC(gv.SMFRECSAVE,save_record)

# ----------------------------------------------------------------------
#		M I D I		S T R E A M S
# ----------------------------------------------------------------------

def getvalue(parm,data,single=True):
	lookfor="%s="%parm
	i=data.find(lookfor)+len(lookfor)
	if not single:
		txt = re.split('\,',re.split('\[|\]',data[i:])[1])
		num = []
		for j in txt:
			num.append( int(j) )
		return num
	return(data[i:i+data[i:].find(",")])

def load(line,dirname, fname, smfseq, gain, voicemap):
	channels={}
	v=", " if gv.DefinitionErr != "" else ""
	if smfseq<1 or smfseq>127:
		print("Skipped midifile %d:%s, out boundaries (1-127)" %(smfseq,fname))
		gv.DefinitionErr="%s%s%d" %(gv.DefinitionErr,v,line)
	elif smfseq in gv.smfseqs:
		print("Skipped midifile %d:%s, already defined via %d:%s" %(smfseq,fname,smfseq,gv.smfseqs[smfseq][0]))
		gv.DefinitionErr="%s%s%d" %(gv.DefinitionErr,v,line)
	else:
		try:
			events=[]
			(song,t)=os.path.splitext(fname)
			drums=[]
			stream=midi.read_midifile(os.path.join(dirname, fname))
			stream.make_ticks_abs()
			for track in stream:
				tn=""
				c=None
				for event in track:
					msg=re.split('\.|\(',"%s"%event)[1]
					data=re.split('\.|\(|\)',"%s"%event)[2]
					if msg=="TrackNameEvent":
						tn=getvalue("text",data)[1:-1]
					elif msg=="EndOfTrackEvent":
						tn=""
					elif msg in supported_events:
						m=supported_events[msg]
						t=int(getvalue("tick",data))
						try:
							c=int(getvalue("channel",data))
						except:
							continue
						if tn=="":
							tn="Channel %d"%(c+1)
						d=getvalue("data",data,False)
						if msg=="ProgramChangeEvent":
							p=d[0]+1
							if c not in channels:
								channels[c]=[ "%s"%tn, False, [p] ]
							else:
								channels[c][2].append(p)
						else:
							if c not in channels:
								channels[c]=[ "%s"%tn, (m not in player_exceptions), [] ]
							else:
								channels[c][1]=True		# just to be sure
							if msg=="NoteOnEvent":
								d[1] = int( d[1]*gain +0.5 )
								if d[1]>127:
									d[1]=127
								if c==9:	# make drum mapping for channel 10
									#n=int(getvalue("data",data)[1:])
									if d[0] not in drums:
										drums.append(d[0])
						if m not in player_exceptions:
							events.append([t,m,c,d])
			events.sort()	# sort on ticks (vishnubob's example sorts on msg (?!?) )
			if voicemap=="":
				voicemap=song
			voices=[]	# inventory of used channels and optional descriptions
			print("SMF_1%d=%s, voicemap=%s sends notes on channels:"%(smfseq,fname,voicemap))
			for key, value in channels.items():
				t=[key,value]
				voices.append(t)
				l=""; c=""; s=""; d=""
				if value[1]:
					p=""
					for v in value[2]:
						p=" using program"
						if c!="":s="s"
						l="%s%s%d"%(l,c,v)
						c=', '
					if l!="":
						l="[%s]" %l
					if key == 9:
						d="%swith instruments %s" %(c,sorted(drums))
					print (" - %d='%s'%s%s %s%s" %(key+1,value[0],p,s,l,d))
			gv.smfseqs[smfseq]=[fname,stream.resolution,events,voices,voicemap,sorted(drums)]
		except:
			print("SMFplayer: error reading %s in %s" %(fname,dirname))

def drumlist():
	drums={}
	for key, value in gv.smfseqs.items():
		(song,t)=os.path.splitext(value[0])
		for i in range(len(value[5])):
			n=value[5][i]
			if n in drums:
				drums[n].append(song)
			else:
				drums[n]=[song]
	print ("Drum sounds used by SMF's:")
	for i in sorted (drums.keys()):
		print (" - %d in %s" %(i,drums[i]))

def seqlist():
	# returns [smfseq#, songname, voicemap, [channel#, channelname, [used_voices]], [used percussionsounds] ]
	smflist=[]
	for key, value in gv.smfseqs.items():
		(song,t)=os.path.splitext(value[0])
		i=0
		used=[]
		for i in xrange(len(value[3])):
			if value[3][i][1][1]:
				used.append([ value[3][i][0]+1, value[3][i][1][0], value[3][i][1][2] ])
		smflist.append([key, song, value[4], used, value[5] ])
	return(smflist)

# ----------------------------------------------------------------------
#		P L A Y E R		T H R E A D
# ----------------------------------------------------------------------

def player():
	global seq, loopit, stopit, streamtempo, actvoicemap
	seq.subscribe_port(client, port)
	while True:
		if gv.currsmf > 0:
			print( "SMFplay %s, res=%d" % \
				( gv.smfseqs[gv.currsmf][0], gv.smfseqs[gv.currsmf][1]
				))
			streamtempo=120		# default in sequencer, don't see use making this a parameter
			gv.smftempo=streamtempo
			seq.init_tempo(gv.smfseqs[gv.currsmf][1])
			stopit=False
			while True:
				seq.start_sequencer()
				while True:
					for e in gv.smfseqs[gv.currsmf][2]:
						event = None
						if supported_msgs[e[1][0]] == "SetTempoEvent":
							event = midi.SetTempoEvent(tick=e[0], data=e[3] )
						else:
							event = supported_events[ supported_msgs[e[1][0]] ][1] (tick=e[0],channel=e[2],data=e[3])
						if stopit:
							break
						msg = re.split('\.|\(',"%s"%event)[1]
						if msg == "SetTempoEvent":
							data = re.split('\.|\(',"%s"%event)[2]
							i = data.find("data=")+5
							j = data[i+1:i+data[i:].find("]")].replace(" ", "").split(',')
							streamtempo = 60000000 / (int(j[0]) * 65536 + int(j[1]) * 256 + int(j[2]) )
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
						if stopit:
							break
						seq.drain()
						msleep(500)
					break
				seq.drop_output()
				seq.stop_sequencer()
				if not loopit:
					break
			try:
				print("SMFplay finished %s" %gv.smfseqs[gv.currsmf][0])
			except:	# info was killed (e.g. by sample set change)
				pass
			# ===> reset voicemap, either default or none
			gv.currsmf=0
		msleep(15)

SMFplayThread = threading.Thread(target=player)
SMFplayThread.daemon = True
SMFplayThread.start()

# ----------------------------------------------------------------------
#		R E C O R D E R
# ----------------------------------------------------------------------

def ignore_record_control(messagetype, message, first_time=False):
	global record_controls
	
	if messagetype == 11:

		found = set()
		for m in gv.CCmap:	# refresh the map to catch voice change effects
			if m[1] in record_controls:
				found.add(m[0])			# set default assignment

		for f in found:
			if gv.controllerCCs[f][1] == message[1]:
				if first_time:				# filter the dummy of the start button
					return True
				elif gv.controllerCCs[f][2] == message[2]:
					return True

	return False

def record_event(mididev, multitimbral, messagechannel, messagetype, message):
	global recorder, lastevent, tickusecs

	if messagetype in supported_msgs:

		currevent = time.time()		# get time in seconds

		if not lastevent:
			if ignore_record_control(messagetype, message, True):
				return
			lastevent = currevent
		elif ignore_record_control(messagetype, message):
			return

		diffusecs = (currevent-lastevent) * 1000000
		lastevent = currevent

		if len(message) == 3:	# biggest chance, so first guess :-)
			data = [ message[1], message[2] ]
		else:
			data = [ message[1] ]
		ticks = int( round( diffusecs/tickusecs, 0))

		if supported_msgs[messagetype ] == "SetTempoEvent":
			event = midi.SetTempoEvent(tick=ticks, data=data )
		else:
			event = supported_events[ supported_msgs[messagetype] ][1] (tick=ticks, channel=messagechannel, data=data)

		midi.buffer_write_event(recorder, event)
