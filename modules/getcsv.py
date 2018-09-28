#
#  Read csv files from /boot/samplerbox
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
#   see docs at  http://homspace.xs4all.nl/homspace/samplerbox
#   changelog in changelist.txt
#
import re

def readcsv(ifile, numtxt=100, header=False):
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
                    if inrow[i]=="":    # stop after emptycell
                        if i==0:         # is this the first cell?
                            i=-1        # then indicate empty row
                        break;
                    if i < numtxt:        # Take the textfields as is
                        row.append(inrow[i])
                    else:               # Convert the rest to integer
                        row.append(int(inrow[i]))
                if i > -1:              # just return filled row
                    rows.append(row)
    return rows

def readchords(ifile):
    chordname=[""]
    chordnote=[[0]]
    chords=readcsv(ifile,1)
    for i in range(len(chords)):
        chordname.append(chords[i][0])
        values=[]
        for j in range(1,len(chords[i])):
            values.append(chords[i][j])
        chordnote.append(values)
    return chordname,chordnote 

def readscales(ifile,chordname):
    scalename=[""]
    scalesymbol=[""]
    scalechord=[[0,0,0,0,0,0,0,0,0,0,0,0]]
    scales=readcsv(ifile,100,True)
    for i in range(len(scales)):
        scalename.append(scales[i][0])
        scalesymbol.append(re.sub('b','&#9837;',re.sub('#','&#9839;',scalename[i])))
        values=[]
        for j in range(1,len(scales[i])):
            if scales[i][j]=="0" or scales[i][j]=="-":
                x=0
            else:
                try:
                    x=chordname.index(scales[i][j])
                except:
                    print ("Chord %s not defined, fall back to single note") %str(scales[i][j])
                    x=0
            values.append(x)
        scalechord.append(values)
    return scalename,scalesymbol,scalechord
