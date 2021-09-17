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
