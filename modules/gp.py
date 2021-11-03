#
#  Global/miscellaneous procedures for samplerbox
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
#   see docs at https://homspace.nl/samplerbox
#   changelog in changelist.txt
#
import gv, subprocess

def samples2write():
    if gv.RUN_FROM_IMAGE:
        print ( "Remount %s as RW" %gv.samplesdir)
        if ( gv.samplesdir == gv.SAMPLES_ONUSB ):
            subprocess.call( ['mount', '-vo', 'remount,rw', gv.samplesdir] )
        else:
            subprocess.call( ['umount', gv.samplesdir] )
            subprocess.call( ['mount', '-v', '/dev/mmcblk0p3', gv.samplesdir] )
    else:
        print ("Not running dedicated, so no remount as we're most likely already R/W")
def samples2read():
    if gv.RUN_FROM_IMAGE:
        print ( "Remount %s as RO" %gv.samplesdir )
        if ( gv.samplesdir == gv.SAMPLES_ONUSB ):
            subprocess.call(['mount', '-vo', 'remount,ro', gv.samplesdir])
        else:
            subprocess.call( ['umount', gv.samplesdir] )
            subprocess.call( ['mount', '-vr', '/dev/mmcblk0p3', gv.samplesdir] )

def GPIOcleanup():
    if gv.GPIO:
        import RPi.GPIO as GPIO
        GPIO.setmode( GPIO.BCM )
        GPIO.cleanup()

def getindex(key, table, onecol=False, casesens=True):
    for i in range(len(table)):
        if onecol:
            if casesens:
                if key==table[i]:   return i
            else:
                if key.lower()==table[i].lower():   return i
        else:
            if casesens:
                if key==table[i][0]:return i
            else:
                if key.lower()==table[i][0].lower:  return i
    return -100000
gv.getindex=getindex                    # temporary till all modules are adapted..

def setFXpresets(val, *z):
    FXset = val
    if isinstance(val,int):
        try:
            FXset = gv.FXpresetnames[val]
        except:
            FXset = gv.FXpresetnames[0]
        idx = getindex(FXset,gv.FXpresetnames,True)
        if idx < 0:
            idx = 0
            FXset = gv.FXpresetnames[idx]
    if FXset in ["",gv.FXpreset_last]:
        gv.FXpreset_last = gv.FXpresetnames[0]
    else:
        if FXset in gv.FXpresetnames:
            gv.FXpreset_last = FXset
            for effect in gv.FXpresets[FXset]:
                gv.procs_alias[ effect ]( gv.FXpresets[FXset][effect] )
        else:
            print ("Effect %s is unspecified, ignored" %FXset)
    return FXset
gv.setMC(gv.FXPRESETS,setFXpresets)

