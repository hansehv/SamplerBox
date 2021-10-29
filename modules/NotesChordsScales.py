#
#  Notes, Chords & Scales procedures for samplerbox
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
#   see docs at https://homspace.nl/samplerbox
#   changelog in changelist.txt
#
import gv,getcsv

CHORDS_DEF = "chords.csv"
SCALES_DEF = "scales.csv"

notenames=["C","Cs","C#","Dk","D","Ds","D#","Ek","E","Es","F","Fs","F#","Gk","G","Gs","G#","Ak","A","As","A#","Bk","B","Bs"]

def getdefs():
	getcsv.readchords(gv.CONFIG_LOC + CHORDS_DEF)
	getcsv.readscales(gv.CONFIG_LOC + SCALES_DEF)


def notename2midinote(notename,fractions):
    notename=notename.title()
    if notename=="Ctrl": midinote=-2
    elif notename=="None": midinote=-1
    else:
        if notename[:2]=="Ck":  # normalize synonyms
            notename="Bs%d" %(int(notename[-1])-1) # Octave number switches between B and C
        elif notename[:2]=="Fk":
            notename="Es%s"%notename[-1]
        try:
            x=notenames.index(format(notename[:len(notename)-1]))
            if fractions==1:    # we have undivided semi-tones = 12-tone scale
                x,y=divmod(x,2) # so our range is half of what's tested
                if y!=0:        # and we can't process any found q's.
                    print("Ignored quartertone %s as we are in 12-tone mode" %notename)
                    midinote=-1
                # next statements places note C4 on 60
                else:           # 12 note logic
                    midinote = x + (int(notename[-1])+1) * 12
            else:               # 24 note logic
                midinote = x + (int(notename[-1])-2) * 24 +12
        except:
            print("Ignored unrecognized notename '%s'" %notename)
            midinote=-128
    return midinote

def midinote2notename(midinote,fractions):
    notename=None
    octave=None
    note=None
    if   midinote==-2: notename="Ctrl"
    elif midinote==-1: notename="None"
    else:
        if midinote<gv.stop127 and midinote>(127-gv.stop127):
            if fractions==1:
                octave,note=divmod(midinote,12)
                octave-=1
                note*=2
            else:
                octave,note=divmod(midinote+36,24)
            notename="%s%d" %(notenames[note],octave)
        else: notename="%d" %(midinote)
    return notename

def setChord(x,*z):
    y=gv.getindex(x,gv.chordname,True)
    if y>-1:                # ignore if undefined
        gv.currscale=0      # playing chords excludes scales
        gv.currchord=y
        gv.display("")

def setScale(x,*z):
    y=gv.getindex(x,gv.scalename,True)
    if y>-1:                # ignore if undefined
        gv.currchord=0      # playing chords excludes scales
        gv.currscale=y
        gv.display("")

def setNotemap(x, *z):
    try:
        y=x-1
    except:
        y=gv.getindex(x,gv.notemaps,True)
    if y>-1:
        if gv.notemaps[y]!=gv.currnotemap:
            gv.currnotemap=gv.notemaps[y]
            gv.notemapping=[]
            for notemap in gv.notemap:       # do we have note mapping ?
                if notemap[0]==gv.currnotemap:
                    gv.notemapping.append([notemap[2],notemap[1],notemap[3],notemap[4],notemap[5],notemap[6]])
    else:
        gv.currnotemap=""
        gv.notemapping=[]
    gv.display("")

gv.notename2midinote=notename2midinote
gv.midinote2notename=midinote2notename
gv.setNotemap=setNotemap
gv.setMC(gv.CHORDS,setChord)
gv.setMC(gv.SCALES,setScale)
gv.setMC(gv.NOTEMAPS,setNotemap)
