###############################################################
# Arpeggiator: play time driven based sequences / chords
#
# Clock can be via call in AudioCallback, on PI3 approx once per 11msec's
#
# To avoid complexity:
#   - replace the "whole and nothing but" keyboard area with this
#   - start/end playing with note-on/off after notemapping and exotic note-off translations
#   - playmode, retune and release samples are ignored (=replaced)
#   - scales/chords are followed
#   - inserting "out-of-keyboard" notes in the chord/sequence will result in a silence
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
import random,gv,chorus
active=False
pressed=False
noteon=False
loop=True
stepticks=10
noteticks=5
cycleticks=30
play2end=False
sequence=[]
currnote=-1
playnote=-1
velocity=0
steps=1         # steps in the cycle = chordnotes
cycletick=0     # position in the cycle
steptick=0      # position in the cyclestep

def stepguard(xn=noteticks,xs=stepticks):
    global steps, cycleticks, stepticks, noteticks
    stepticks=xs
    cycleticks=steps*stepticks
    noteticks=xs if xs<xn else xn
stepguard()

def process():
    global mode,playnote,velocity,sequence,steps,cycletick,steptick,stepticks,noteticks,cycleticks
    if currnote>-1:     # are we playing?
        if gv.ActuallyLoading:              # playing while loading new data is impossible
            return(rewind())                # so it ends here
        xs=stepticks
        xn=noteticks
        xc=cycleticks
        if mode==3:
            if steptick>=xs-1:              # step (note+rest) end reached
                cycletick=xs*random.randint(0,steps-1)
        else:
            cycletick+=1
            if cycletick>=xc:               # chord / sequence end reached
                if play2end and not noteon: # in note off stage
                    return(rewind())        # so it ends here.
                cycletick=0                 # otherwise loop through chord / sequence
        steptick=cycletick%xs
        if steptick>=xn or steptick==0:
            noteoff()
        if steptick==0:
            playnote=currnote+sequence[int(cycletick//xs)]
            if playnote>(127-gv.stop127) and playnote<gv.stop127:   # stay within keyboard range
                if chorus.effect:
                    gv.PlaySample(playnote,playnote,gv.currvoice,velocity*chorus.gain,0,0)
                    gv.PlaySample(playnote,playnote,gv.currvoice,velocity*chorus.gain,2,-(chorus.depth/2+1))
                    gv.PlaySample(playnote,playnote,gv.currvoice,velocity*chorus.gain,5,chorus.depth)
                else:
                    gv.PlaySample(playnote,playnote,gv.currvoice,velocity,0,0)
            else:
                playnote=-1
            if fadecycles<100 and (not pressed or not loop):
                velocity-=fadestep
                if velocity<=1:
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
    global mode,lastmode
    #if currnote<0:
    if not active:
        if mode==0: mode=lastmode
        power(True)
    else:
        lastmode=mode
        mode=0
        power(False)
gv.setMC(gv.ARP,togglepower)

def noteoff():
    global playnote,velocity
    if playnote>-1:
        if playnote in gv.playingnotes:
            for m in gv.playingnotes[playnote]:
                m.fadeout(noteticks<stepticks)  # damp when notes are consecutive
                gv.playingnotes[playnote]=[]
                if noteticks<stepticks:         # process release sample if notes are not consecutive
                    gv.PlayRelSample(m.playingrelsample(),gv.currvoice,playnote,velocity,m.playingretune())
        playnote=-1

def rewind():
    global currnote,cycletick
    currnote=-1     # stop the loop first
    noteoff()       # so we're sure to stop the playing note :-)
    cycletick=-1     # not cycling

def note_onoff(messagetype, midinote, played_velocity):
    global mode,pressed,noteon,sequence,currnote,velocity,steps,cycleticks,stepticks
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
            if not play2end or mode==3:  # random(ord=2) will never reach an end
                rewind()
        else:
            return          # ignore unrelated note-off's (keys held while pressing a new one)
    if messagetype==9:      # if note on, start new arpeggio
        rewind()            # stop anything playing and initialize
        pressed=True        # keep track of keypress
        noteon=True
        velocity=played_velocity
        gv.last_musicnote=midinote-12*int(midinote/12) # do a "remainder midinote/12" without having to import the full math module
        if gv.currscale>0:               # scales require a chords mix
            sequence=gv.chordnote[gv.scalechord[gv.currscale][gv.last_musicnote]]
        else:
            sequence=gv.chordnote[gv.currchord]
        if mode==2:
            sequence=list(reversed(sequence))
        steps=len(sequence)
        cycleticks=steps*stepticks
        fadeout(1.27*fadecycles)
        currnote=midinote       # And activate!

def tempo(CCval,*z):    # time between note-on's
    global noteticks
    x=(CCval*100)/127.0
    if x>100:x=100
    elif x<10:x=10
    stepguard(noteticks,x)
gv.setMC(gv.ARPTEMPO,tempo)

def sustain(CCval,*z):  # time between note-on and note-off,
                        # when tempo is faster it will override making it continuous
    global stepticks
    x=(CCval*100)/127.0
    if x>100:x=100
    stepguard(x,stepticks)
gv.setMC(gv.ARPSUSTAIN,sustain)

modes=["Off","Up","Down","Random"]
mode=0
lastmode=1
lastlinmode=1
def ordnum(num):
    global mode,lastlinmode,sequence,lastmode
    if num==0:
        power(False)
    else:
        lastmode=mode
        power(True)
        if num<3:
            if lastlinmode!=num:
                sequence=list(reversed(sequence))
                lastlinmode=num
    mode=num
def up(*z):
    ordnum(1)
def down(*z):
    ordnum(2)
def updown(*z):
    global mode,lastlinmode,sequence
    if lastlinmode==1:
        lastlinmode=2
        sequence=list(reversed(sequence))
    else:
        lastlinmode=1
        sequence=list(reversed(sequence))
    if mode!=3:
        mode=lastlinmode
def rand(*z):
    global mode
    mode=3
def rndlin(*z):
    global mode
    if mode==3:
        mode=lastlinmode
    else:
        mode=3
gv.setMC(gv.ARPUP,up)
gv.setMC(gv.ARPDOWN,down)
gv.setMC(gv.ARPUPDOWN,updown)
gv.setMC(gv.ARPRANDOM,rand)
gv.setMC(gv.ARPRNDLIN,rndlin)

fadecycles=100
fadestep=0.0
def fadeout(CCval,*z):  # number of cycles to fadeout (default no fadeout)
    global fadestep, fadecycles, velocity
    x=((CCval)*100)/127.0
    fadecycles=x
    if fadecycles<100:
        if fadecycles<=0: fadecycles=0.5
        fadestep=1.0*velocity/fadecycles
    else:
        fadestep=0.0
gv.setMC(gv.ARPFADE,fadeout)

def ArpLoop(*z):
    global loop
    loop=not(loop)
def ArpPlay2end(*z):
    global play2end
    play2end=not(play2end)
gv.setMC(gv.ARPLOOP,ArpLoop)
gv.setMC(gv.ARP2END,ArpPlay2end)

