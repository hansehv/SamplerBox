###############################################################
# Aftertouch (both channel and polyphonic)
#  - Messages are filtered unless assigned to an effect
#  - Channel is dealt with via virtual CC
#    The type=0=continuous
#    So: a "normal" CC with controller="ChannelAfterTouch"
#        only exception is CC=7=volume, this is via gain
#        in a "bulk polyphonic" method in here
#  - Polyphonic is dealt with via routines in here
#    - calling routine to supply the triggered notes
#    - "polyphonic" loops through the sounds generated per note
#      (e.g. chorus, layers) while calling the actual routine
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
import gv, gp

gv.lastvel = 64  # init the reference value
chanCC = 0
polyCC = 0
chanCCidx = 0
polyCCidx = 0
notepairs = None

# Add virtual controllers for aftertouch,
#   so they can be assigned as a CC

if gv.CHAN_AFTOUCH:
    chanCC = gp.getvirtualCC()
    chanCCidx = len(gv.controllerCCs)
    gv.controllerCCs.append([gv.CHAFTOUCH,chanCC,-1])
if gv.POLY_AFTOUCH:
    polyCC = gp.getvirtualCC()
    polyCCidx = len(gv.controllerCCs)
    gv.controllerCCs.append([gv.PAFTOUCH,polyCC,-2])

# Fill notepairs (actuallyload procedure)

def getnotenumber(voice, pair, partner, fractions):
    number=-1
    if partner.isdigit():
        number = int(partner)
    else:
        number = gv.notename2midinote(partner,fractions)
        if number < 0:
            print("AfterTouch: invalid note %s in aftertouch notepair, skipped %s in voice %d" %(partner, pair, voice) )
    return number

def fillpairs(voice=0, fractions=1, parm=None, init=False):
    global notepairs
    pairs = {}
    if init:
        notepairs={}
    elif not parm:
        pass
    else:
        if parm[0]=='(' and parm[-1]==')':
            parmpairs = parm[1:-1].split(';')
            for pair in parmpairs:
                partners = pair.split("-")
                if len(partners) != 2:
                    print("Aftertouch: incorrect notepair in voice %d, ignored '%s'" %(voice, pair) )
                    continue
                trigger = getnotenumber(voice, pair, partners[0], fractions)
                follower = getnotenumber(voice, pair, partners[1], fractions)
                if trigger<0 or follower<0:
                    continue
                if trigger == follower:
                    print("Aftertouch: incorrect notepair in voice %d, ignored %s" %(voice, pair) )
                    continue
                if voice in notepairs:
                    if trigger in notepairs[voice]:
                        if follower not in notepairs[voice][trigger]:
                            notepairs[voice][trigger].append(follower)
                    else:
                        notepairs[voice][trigger] = [follower]
                else:
                    notepairs[voice] = { trigger:[follower] }
        else:
            print("Aftertouch: incorrect %pafpair in voice %d, ignored %s" %(voice, parm) )

# Manage aftertouch messages filter via CCmap
#   (so after every voicechange)

def msgAdd(msg):
    if msg not in gv.MASTER_MESSAGES:
        gv.MASTER_MESSAGES.append(msg)
def msgRem(msg):
    if msg in gv.MASTER_MESSAGES:
        msgs = []
        for m in gv.MASTER_MESSAGES:
            if m != msg:
                msgs.append(m)
        gv.MASTER_MESSAGES = msgs

chanproc = ""
polyproc = ""
def msgFilter():
    global chanproc, polyproc
    chan = False
    poly = False
    chanproc = ""
    polyproc = ""
    for m in gv.CCmap:
        if m[0] == chanCCidx:
            chan = True
            chanproc = gv.MC[m[1]][0]
        elif m[0] == polyCCidx:
            poly = True
            polyproc = gv.MC[m[1]][0]
        if (chan and poly):
            break
    if poly and gv.POLY_AFTOUCH:
        msgAdd(10)
    elif gv.POLY_AFTOUCH:
        msgRem(10)
    if chan and gv.CHAN_AFTOUCH:
        msgAdd(13)
    elif gv.CHAN_AFTOUCH:
        msgRem(13)


### CHANNEL effects ########################

def Channel(pressure, *z):
    if pressure > 0:    # pressure=0 is too complicated
        if chanReverse:
            pressure = 128 - pressure
        for m in gv.CCmap:
            if m[0] == chanCCidx:
                if gv.MC[m[1]][0] == gv.VOLUME:
                        # Volume should be processed
                        # per note via velocity
                    for note in gv.playingnotes:
                        for pn in gv.playingnotes[note]:
                            paVolume(pn, pressure, note)
                else:   # Rest can be via common CC'd effects
                    gv.MC[m[1]][2](pressure, gv.MC[m[1]][0])
                break

chanReverse = False
def chanRevToggle(*z):
    global chanReverse
    chanReverse = not chanReverse

gv.setMC(gv.CHAFREVERS,chanRevToggle)


### POLYPHONIC effects #####################

def Polyphonic(note, pressure, *z):
    if pressure > 0:    # pressure=0 is too complicated
        if pafReverse:
            pressure = 128 - pressure
        for m in gv.CCmap:
            if m[0] == polyCCidx:
                if note in gv.playingnotes:
                    for pn in gv.playingnotes[note]:
                        # this loops through layers and chorus
                        gv.MC[m[1]][2](pn, pressure, note)
                followed = False    # prevent accumulation (e.g. with chorus)
                voice = gv.currvoice
                if voice not in notepairs:
                    voice = 0
                if voice in notepairs:
                    if note in notepairs[gv.currvoice] and not followed:
                        # process the followers, even if the master isn't played
                        #  (it doesn't hurt for the master, but will catch
                        #   specials like cymbal center choke via the rim)
                        for follower in notepairs[gv.currvoice][note]:
                            if follower in gv.playingnotes:
                                for fn in gv.playingnotes[follower]:
                                    gv.MC[m[1]][2](fn, pressure, note)
                break

pafReverse = False
def pafRevToggle(*z):
    global pafReverse
    pafReverse = not chanReverse

def paVolume(pn, pressure, note, *z):
    pn.playingvolume(True, pressure)

def paChoke(pn, pressure, note, *z):
    # perhaps we should be testing on =127 or >64 ... feedback needed...
    pn.fadeout(False)
    gv.playingnotes[note] = []
    gv.triggernotes[note] = 128  # housekeeping
    gv.DampNoise(pn)

paPitchRange = 2  # 1 note = 2 semi tones. Up&down total that is.
def paPitchSetRange(val,*z):
    global paPitchRange
    paPitchRange = int( val/10 )
def paPitch(pn, pressure, note, *z):
    diff = pressure - pn.playingvelocity()
    pn.playingretune(True, diff*paPitchRange)
    # self.retune += (2*val-self.velocity) -> starting velocity is neutral

paPanWidth = 0.5
def paPan(pn, pressure, note, *z):
    pn.playingpan(True, pressure, paPanWidth)
def paPanSetwidth(val,*z):
    global paPanWidth
    paPanWidth=val/127.0            # values 0-1, both left & right

gv.setMC(gv.PAFREVERS,pafRevToggle)
gv.setMC(gv.PAFVOLUME,paVolume)
gv.setMC(gv.PAFPITCH,paPitch)
gv.setMC(gv.PAFPITCHRANGE,paPitchSetRange)
gv.setMC(gv.PAFPAN,paPan)
gv.setMC(gv.PAFPANWIDTH,paPanSetwidth)
gv.setMC(gv.PAFCHOKE,paChoke)
