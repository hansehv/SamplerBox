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
#   see docs at  http://homspace.xs4all.nl/homspace/samplerbox
#   changelog in changelist.txt
#
import re, gv
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
                inrow=re.split(',|;|\t',re.sub(' |"|\'|\n|\r', "", line))
                for i in range(len(inrow)):
                    if inrow[i]=="":        # stop after emptycell
                        if i==0:            # is this the first cell?
                            i=-1            # then indicate empty row
                        break;
                    if inrow[i][0]=="#":    # allow=ignore for comments
                        if i==0:            # is this the first cell?
                            i=-1            # then indicate empty row
                        break
                    if i < numtxt:          # Take the textfields as is
                        row.append(inrow[i])
                    else:                   # Convert the rest to integer
                        try:
                            row.append(int(inrow[i]))
                        except:
                            print("%s: Found '%s' when expecting a digit, ignoring rest of line %s" %(ifile, inrow[i], inrow))
                            break
                if i > -1:                  # just return filled row
                    rows.append(row)
    return rows

def readchords(ifile):
    sheet=readcsv(ifile,1,False)
    gv.chordnote=[[0]]     # single note
    gv.chordname=[""]
    for i in range(len(sheet)):
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
    gv.scalesymbol=[""]
    for i in range(len(sheet)):
        gv.scalename.append(sheet[i][0])
        gv.scalesymbol.append(re.sub('b','&#9837;',re.sub('#','&#9839;',gv.scalename[i+1])))
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
        if len(sheet[i])>2:     # skip useless lines
            if gv.getindex(sheet[0],gv.controllerCCs)!=-1:
                print ("%s: Controller %s already defined, ignored %s" %(ifile,sheet[0],sheet[i]))
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
            if sheet[i][0]!=gv.UA:      # skip unassigned controllers
                values=[0,"",None,voice]
                x=gv.getindex(sheet[i][0],gv.controllerCCs)
                if x<0:
                    print("%s: Controller %s not defined, ignoring %s" %(ifile, sheet[i][0], str(sheet[i])))
                    gv.ConfigErr=True
                    continue
                elif len(sheet[i])>1:       # skip empty lines
                    if sheet[i][1]!=gv.UA:  # skip unassigned controls
                        if len(sheet[i])<4:
                            print("%s: ignored %s" %(ifile, str(sheet[i])))
                            gv.ConfigErr=True
                            continue
                        for j in xrange(len(CCmap)):
                            if CCmap[j][0]==x and CCmap[j][3]==voice:
                                print ("%s: Controller '%s' already mapped, ignored %s" %(ifile,gv.controllerCCs[x][0],sheet[i]))
                                gv.ConfigErr=True
                                continue
                        if gv.getindex(sheet[i][3].lower(),["continuous","toggle","switch","switchon","switchoff"],True)==-1:
                            print("%s: Mode '%s' unrecognized, ignored: %s" %(ifile, sheet[i][3], str(sheet[i])))
                            gv.ConfigErr=True
                        elif (sheet[i][3].lower()!="continuous" and gv.controllerCCs[x][2]==-1 or sheet[i][3].lower()=="continuous" and gv.controllerCCs[x][2]!=-1):
                            print("%s: Continuous/switch controller mapped to incompatible function, ignored: %s" %(ifile, str(sheet[i])))
                            gv.ConfigErr=True
                        else:
                            values[0]=x     # identify controller
                            # Normalize/correct the input
                            if sheet[i][1].upper()==gv.FIXED.upper():
                                mc=sheet[i][2]
                            else:
                                mc=sheet[i][1]
                                values[2]=sheet[i][2]
                            y=gv.getindex(mc,gv.MC)
                            if y>-1:
                                values[1]=y
                                CCmap.append(values)
                            else:
                                print("%s: Type '%s' unrecognized, ignored %s" %(ifile, sheet[i][1], str(sheet[i])))
                                gv.ConfigErr=True
    except:
        if not override:
            print "%s: No default controller mapping found" %(ifile)
    return CCmap

def readkeynames(ifile):
    # keynames: [name of key/string/pad, midinote sent by this trigger]
    gv.keynames=[]
    try:        # giving keys/strings/triggers a name is optional
        sheet=readcsv(ifile)
        for i in range(len(sheet)):
            values=[]
            if len(sheet[i])>1:     # skip useless lines
                if gv.getindex(sheet[0],gv.keynames)!=-1:
                    print ("%s: Key %s already defined, ignored %s" %(ifile,sheet[0],sheet[i]))
                else:
                    values.append(sheet[i][0])
                    values.append(sheet[i][1])
            else:
                print ("%s: ignored %s" %(ifile, sheet[i]))
                gv.ConfigErr=True
            gv.keynames.append(values)
    except:
        pass    # giving keys/strings/triggers a name is optional
    return 

def readnotemap(ifile):
    # notemap: [set, fractions, key, note, retune, playvoice]
    default=""
    gv.notemap=[]
    try:        # note mapping is optional
        sheet=readcsv(ifile,4)
        for i in range(len(sheet)):
            if len(sheet[i])>3:     # skip useless lines
                values=["",0,0,0,0,0]
                values[0]=format(sheet[i][0]).title()   # force num to string and normalize upper/lowercase usage
                if values[0]=="":
                    print ("%s: Sets must have a name, ignored %s" %(ifile, sheet[i]))
                    continue
                if default=="":
                    default=values[0]
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
                    x=gv.getindex(sheet[i][2],gv.keynames)
                    if x<0:
                        print ("%s: keyname '%s' not defined, ignored %s" %(ifile, sheet[i][2], sheet[i]))
                        continue
                    else:
                        values[2]=int(gv.keynames[x][1])
                try:
                    values[3]=int(sheet[i][3])
                    if values[3]<0 or values[5]>127:
                        print ("%s: invalid notenumber, ignored %s" %(ifile, sheet[i]))
                except:
                    midinote=gv.notename2midinote(sheet[i][3],sheet[i][1])
                    if midinote>-1:
                        values[3]=midinote
                    else:
                        print ("%s: invalid notename '%s', ignored %s" %(ifile, sheet[i][2], sheet[i]))
                        continue
                if len(sheet[i])>4: # the values are optional
                    try:
                        values[4]=int(sheet[i][4])
                        values[5]=int(sheet[i][5])
                    except:
                        pass
                gv.notemap.append(values)
            else:
                print ("%s: ignored %s" %(ifile, sheet[i]))
                gv.ConfigErr=True
    except:
        pass    # notemapping is optional
    return default
