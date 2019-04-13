###############################################################
# Arpeggiator: play time driven based sequences / chords
#
# Clock can be via call in AudioCallback, on PI3 approx once per 11msec's
#
# To avoid complexity:
#   - replace the "whole and nothing but" keyboard mode with this
#   - start/end playing with note-on/off after notemapping and exotic note-off translations
#   - playmode, retune and release samples are ignored (=replaced)
#   - scales/chords are followed
#   - inserting "out-of-keyboard" notes in the chord/sequence will result in a silence
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
import random,gv
active=False
pressed=False
noteon=False
loop=True
length=10
keepon=5
play2end=False
sequence=[]
currnote=-1
playnote=-1
velocity=0
velmixer=0
cyclelen=0      # length in number of cyclesteps = chordnotes
cyclepos=-1     # position in the cyclestep(s)
cyclestep=length+5  # number of steps within a notelength
cycleoff=keepon+5   # position within the cyclestep where the noteoff is done

def stepguard():
    global cycleoff
    if (keepon+5)>cyclestep:
        cycleoff=cyclestep
    else:
        cycleoff=keepon+5

def process():
    global playnote, velmixer, cyclepos
    notepos=0
    steppos=0
    stepnr=0
    if currnote>-1:     # are we playing?
        if gv.ActuallyLoading:              # playing while loading new data is impossible
            return(rewind())                # so it ends here
        cyclepos+=1
        if order==2:
            if cyclepos%cyclestep==0:       # step (note+rest) end reached
                cyclepos=cyclestep*random.randint(0,len(sequence)-1)
        else:
            if cyclepos>=cyclelen*cyclestep:# chord / sequence end reached
                if play2end and not noteon:   # in note off stage
                    return(rewind())        # so it ends here.
                cyclepos=0                  # otherwise loop through chord / sequence
        if cyclepos==0:
            notepos=0
            stepnr=0
            steppos=0
        else:
            notepos=cyclepos%cycleoff
            steppos=cyclepos%cyclestep
            stepnr=int(cyclepos/cyclestep+0.4)
        if notepos==0:
            noteoff()
        if steppos==0:
            playnote=currnote+sequence[stepnr]
            if playnote>(127-gv.stop127) and playnote<gv.stop127:   # stay within keyboard range
                gv.playingnotes.setdefault(playnote,[]).append(gv.samples[playnote, velocity, gv.currvoice].play(playnote, playnote, velmixer*gv.globalgain, 0, 0))
            else:
                playnote=-1
            if fadecycles<100 and (not pressed or not loop):
                velmixer-=fadestep
                if velmixer<=1:
                    return(rewind())

def power(onoff):
    global active
    if onoff and not active:
        for i in gv.playingnotes:           # stop current keyboard activity
            for m in gv.playingnotes[i]:
                note=m.playingnote()
                if note>(127-gv.stop127) and note<gv.stop127:
                    m.fadeout()
                    gv.playingnotes[note] = []
                    gv.triggernotes[note] = 128
        rewind()        # initialize before start
        active=True     # and start...
    if not onoff and active:
        active=False    # stop first
        rewind()        # initialize completely for safety...
def togglepower(CCval, *z):
    if currnote<0:
        power(True)
    else:
        power(False)
gv.MC[gv.getindex(gv.ARP,gv.MC)][2]=togglepower

def noteoff():
    global playnote
    if playnote>-1:
        if playnote in gv.playingnotes:
            for m in gv.playingnotes[playnote]:
                m.fadeout(not(cycleoff==cyclestep)) # damp when notes are consecutive
            gv.playingnotes[playnote]=[]
        playnote=-1

def rewind():
    global currnote, cyclepos
    currnote=-1 # stop the loop first
    noteoff()   # so we're sure to stop the playing note :-)
    cyclepos=-1

def note_onoff(messagetype, midinote, played_velocity, velocity_mode, VELSAMPLE):
    global pressed, noteon, sequence, currnote, velmixer, velocity, cyclelen, cycleoff
    if loop:
        if messagetype==8:
            pressed=False   # keep track of keypress
            return          # but in loop, all noteoffs are to be ignored
        if messagetype==9 and midinote==currnote:
            messagetype=8   # because only a second keypress can end it
    if messagetype==8:
        if currnote==midinote:
            pressed=False   # keep track of keypress
            noteon=False
            if not play2end or order==2:  # random(ord=2) will never reach an end
                rewind()
        else:
            return          # ignore unrelated note-off's (keys held while pressing a new one)
    if messagetype==9:      # if note on, start new arpeggio
        rewind()            # stop anything playing and initialize
        pressed=True        # keep track of keypress
        noteon=True
        currnote=midinote
        velocity=played_velocity
        if velocity_mode==VELSAMPLE: 
            velmixer=127
        else:
            velmixer=velocity
        gv.last_musicnote=midinote-12*int(currnote/12) # do a "remainder midinote/12" without having to import the full math module
        if gv.currscale>0:               # scales require a chords mix
            sequence = gv.chordnote[gv.scalechord[gv.currscale][gv.last_musicnote]]
        else:
            sequence=gv.chordnote[gv.currchord]
        if order==1:
            sequence=list(reversed(sequence))
        cyclelen=len(sequence)
        stepguard()
        fadeout(1.27*fadecycles)

def tempo(CCval,*z):    # time between note-on's
    global length, cyclestep
    x=(CCval*100)/127.0
    if x>100:x=100
    cyclestep=x+5
    length=x
    stepguard()
gv.MC[gv.getindex(gv.ARPTEMPO,gv.MC)][2]=tempo

def sustain(CCval,*z):  # time between note-on and note-off,
                        # when tempo is faster it will override making it continuous
    global keepon
    x=(CCval*100)/127.0
    if x>100:x=100
    keepon=x
    stepguard()
gv.MC[gv.getindex(gv.ARPSUSTAIN,gv.MC)][2]=sustain

ordlist=["Up","Down","Random"]
order=0
lastlinord=0
def ordnum(num):
    global order,lastlinord, sequence
    order=num
    if order<2:
        if lastlinord!=order:
            sequence=list(reversed(sequence))
            lastlinord=order
def up(*z):
    ordnum(0)
def down(*z):
    ordnum(1)
def updown(*z):
    global order,lastlinord, sequence
    if lastlinord==0:
        lastlinord=1
        sequence=list(reversed(sequence))
    else:
        lastlinord=0
        sequence=list(reversed(sequence))
    if order!=2:
        order=lastlinord
def rand(*z):
    global order
    order=2
def rndlin(*z):
    global order
    if order==2:
        order=lastlinord
    else:
        order=2
gv.MC[gv.getindex(gv.ARPUP,gv.MC)][2]=up
gv.MC[gv.getindex(gv.ARPDOWN,gv.MC)][2]=down
gv.MC[gv.getindex(gv.ARPUPDOWN,gv.MC)][2]=updown
gv.MC[gv.getindex(gv.ARPRANDOM,gv.MC)][2]=rand
gv.MC[gv.getindex(gv.ARPRNDLIN,gv.MC)][2]=rndlin

fadecycles=100
fadestep=0.0
def fadeout(CCval,*z):  # number of cycles to fadeout (default no fadeout)
    global fadestep, fadecycles
    x=((CCval)*100)/127.0
    fadecycles=x
    if fadecycles<100:
        if fadecycles<=0: fadecycles=0.5
        fadestep=1.0*velmixer/fadecycles
    else:
        fadestep=0.0
gv.MC[gv.getindex(gv.ARPFADE,gv.MC)][2]=fadeout
