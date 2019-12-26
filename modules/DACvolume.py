###############################################################
#   DAC volume control via the alsamixer
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################

import gv,re,alsaaudio

#MIXER_CONTROL=gv.cp.get(gv.cfg,"MIXER_CONTROL".lower()).replace(" ", "").split(',')

ok=False
mixer_card_index = re.search('\(hw:(.*),', gv.AUDIO_DEVICE_NAME) # get x from (hw:x,y) in device name
mixer_card_index = int(mixer_card_index.group(1))
mixer_controls = alsaaudio.mixers(mixer_card_index)
for mixer_control in mixer_controls:
    for mixer_id in range(0, 6):
        try:
            amix = alsaaudio.Mixer(id=mixer_id,cardindex=mixer_card_index,control=mixer_control)
            ok=True             # indicate OK
            print 'Opened Alsamixer: card (hw:%i,x), control %s' % (mixer_card_index,mixer_control)
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
    print 'Invalid mixer card id "%i" or control "%s",' % (mixer_card_index,mixer_control)
    print 'if mixer present, card id is "x" in "(hw:x,y)" in opened audio device.'
    exit(1)
