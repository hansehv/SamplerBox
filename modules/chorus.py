###############################################################
# Chorus (add pitch modulated and delayed copies of notes)
# Process incorporated in the note-on logic, so rather cheap
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
import gv

effects=["Off","On"]
effect=False
depth=0.0
gain=0.0
def setType(x,*z):
    global effect
    if x>0:
        effect=True
    else:
        effect=False
def toggle(*z):
    global effect
    effect=not(effect)
def setdepth(x,*z):  # 2-15
    global depth
    depth=2+13*x/127
def setgain(x,*z):  # 0.3-0.8
    global gain
    gain=0.3+0.5*x/127.0
def reset(scope=-1):
    global effect,depth,gain
    effect=False      # -1 turns of the effect, undefined values cover midi controller turn off
    if scope in [-2, -4]:       # also reset values
        #if scope == -3:         # load sample set default
        #    load sample set default
        #else:                   # system default
        effect=(gv.cp.get(gv.cfg,"Chorus".lower()).title() == "On")
        depth=gv.cp.getfloat(gv.cfg,"CHOdepth".lower())
        gain=gv.cp.getfloat(gv.cfg,"CHOgain".lower())
reset(-2)
gv.setMC(gv.CHORUS,toggle)
gv.setMC(gv.CHORUSDEPTH,setdepth)
gv.setMC(gv.CHORUSGAIN,setgain)
