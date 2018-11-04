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
                        row.append(int(inrow[i]))
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
                    print ("%s: Chord %s not defined, fallback to single note" %(ifile,str(scales[i][j])))
                    x=0
            values.append(x)
        gv.scalechord.append(values)
    return

def readmidiCCs(ifile):
    # midiCCs: [wheel/button/pot/drawbarname, controller, data LSB (-1 if continuous controller)]
    sheet=readcsv(ifile,1)
    gv.midiCCs=[[gv.UA,-1,-1]]  # define controller for unassigned controls
    for i in range(len(sheet)):
        if len(sheet[i])==3:
            if gv.getindex(sheet[0],gv.midiCCs)!=-1:
                print ("%s: Controller %s already defined, ignored %s" %(ifile,sheet[0],sheet[i]))
            else:
                values=[]
                for j in range(len(sheet[i])):
                    values.append(sheet[i][j])
                gv.midiCCs.append(values)
        else:
            print ("%s: ignored %s" %(ifile, sheet[i]))
            gv.ConfigErr=True
    return 

def readmidimap(ifile):
    # midimap: [buttonindex, procedureindex]
    sheet=readcsv(ifile)
    for i in range(len(sheet)):
        values=[0,"",None]
        table=False
        x=gv.getindex(sheet[i][0],gv.midiCCs)
        if x<0:
            print("%s: Controller %s not defined, ignoring %s" %(ifile, sheet[i][0], str(sheet[i])))
            gv.ConfigErr=True
            continue
        elif len(sheet[i])>1:       # skip empty lines
            if sheet[i][1]!=gv.UA:  # skip unassigned controlles
                if len(sheet[i])<4:
                    print("%s: ignored %s" %(ifile, str(sheet[i])))
                    gv.ConfigErr=True
                elif sheet[i][0]!=gv.UA and gv.getindex(x,gv.midimap)>0:
                    print ("%s: Controller '%s' already mapped, ignored %s" %(ifile,gv.midiCCs[x][0],sheet[i]))
                    gv.ConfigErr=True
                elif gv.getindex(sheet[i][3].lower(),["continuous","toggle","switch","switchon","switchoff"],True)==-1:
                    print("%s: Mode '%s' unrecognized, ignored: %s" %(ifile, sheet[i][3], str(sheet[i])))
                    gv.ConfigErr=True
                elif sheet[i][0]!=gv.UA and (sheet[i][3].lower()!="continuous" and gv.midiCCs[x][2]==-1 or sheet[i][3].lower()=="continuous" and gv.midiCCs[x][2]!=-1):
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
                        gv.midimap.append(values)
                    else:
                        print("%s: Type '%s' unrecognized, ignored %s" %(ifile, sheet[i][1], str(sheet[i])))
                        gv.ConfigErr=True
    return
