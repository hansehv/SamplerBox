#
#  Global/miscellaneous procedures for samplerbox
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
#   see docs at https://homspace.nl/samplerbox
#   changelog in changelist.txt
#
import gv, subprocess

def samples2write():
	if gv.rootprefix=="":
		print ( "Remount samplesdir as RW" )
		subprocess.call( ['umount', gv.samplesdir] )
		subprocess.call( ['mount', '/dev/mmcblk0p3', gv.samplesdir] )
	else:
		print ("Not running dedicated, so no remount as we're most likely already R/W")
def samples2read():
	if gv.rootprefix=="":
		print ( "Remount samplesdir as RO" )
		subprocess.call( ['umount', gv.samplesdir] )
		subprocess.call( ['mount', '-r', '/dev/mmcblk0p3', gv.samplesdir] )
