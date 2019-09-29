###############################################################
#   DAC volume control via the alsamixer
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################

import gv,alsaaudio

MIXER_CONTROL=gv.cp.get(gv.cfg,"MIXER_CONTROL".lower()).replace(" ", "").split(',')

ok=False

for i in range(0, 4):
    for j in range(0, len(MIXER_CONTROL)):
        try:
            amix = alsaaudio.Mixer(cardindex=gv.MIXER_CARD_ID+i,control=MIXER_CONTROL[j])
            gv.MIXER_CARD_ID+=i    # save the found value
            ok=True             # indicate OK
            print 'Opened Alsamixer: card (hw:%i,x), control %s' % (gv.MIXER_CARD_ID, MIXER_CONTROL[j])
            break
        except:
            pass
    if ok: break

if ok:
    def getvolume():
        vol = amix.getvolume()
        gv.volume = int(vol[0])
    def setvolume(volume):
        amix.setvolume(volume)
        getvolume()
    setvolume(gv.volume)
    gv.getvolume=getvolume
    gv.setvolume=setvolume
else:
    gv.USE_ALSA_MIXER=False
    gv.display("Invalid mixerdev")
    print 'Invalid mixer card id "%i" or control "%s" --' % (gv.MIXER_CARD_ID, MIXER_CONTROL)
    print '-- Mixer card id is "x" in "(hw:x,y)" (if present) in opened audio device.'
    exit(1)
