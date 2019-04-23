###############################################################
# Chorus (add pitch modulated and delayed copies of notes)
# Process incorporated in the note-on logic, so rather cheap
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
import gv

def setType(x,*z):
    if x>0:
        gv.CHOrus=True
    else:
        gv.CHOrus=False
def toggle(*z):
    gv.CHOrus!=gv.CHOrus
def setdepth(x,*z):  # 2-15
    gv.CHOdepth=2+13*x/127
def setgain(x,*z):  # 0.3-0.8
    gv.CHOgain=0.3+0.5*x/127.0
def reset():
    gv.CHOrus=False
    gv.CHOdepth=gv.cp.getfloat(gv.cfg,"CHOdepth".lower())
    gv.CHOgain=gv.cp.getfloat(gv.cfg,"CHOgain".lower())
reset()
gv.MC[gv.getindex(gv.CHORUS,gv.MC)][2]=toggle
gv.MC[gv.getindex(gv.CHORUSDEPTH,gv.MC)][2]=setdepth
gv.MC[gv.getindex(gv.CHORUSGAIN,gv.MC)][2]=setgain
