#
#  Global/miscellaneous procedures for samplerbox
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
#   see docs at https://homspace.nl/samplerbox
#   changelog in changelist.txt
#
import subprocess, copy
import gv

def NoProc(*vals):		# Dummy
	pass

def samples2write(setting=False):
	if gv.RUN_FROM_IMAGE:
		samplesdir=gv.SAMPLES_INBOX if setting else gv.samplesdir
		print ( "Remount %s as RW" %samplesdir)
		if ( samplesdir == gv.SAMPLES_ONUSB ):
			subprocess.call( ['mount', '-vo', 'remount,rw', samplesdir] )
		else:
			subprocess.call( ['umount', samplesdir] )
			subprocess.call( ['mount', '-v', '/dev/mmcblk0p3', samplesdir] )
	else:
		print ("Not running dedicated, so no remount as we're most likely already R/W")
def samples2read(setting=False):
	if gv.RUN_FROM_IMAGE:
		samplesdir=gv.SAMPLES_INBOX if setting else gv.samplesdir
		print ( "Remount %s as RO" %samplesdir )
		if ( samplesdir == gv.SAMPLES_ONUSB ):
			subprocess.call(['mount', '-vo', 'remount,ro', samplesdir])
		else:
			subprocess.call( ['umount', samplesdir] )
			subprocess.call( ['mount', '-vr', '/dev/mmcblk0p3', samplesdir] )

def no_delimiters(raw):	# crude but effective for failsafe operation :-)
	return raw.replace(",",".").replace(";",":").replace("\t"," ")

def presetdir():
	return gv.samplesdir+gv.presetlist[getindex(gv.PRESET,gv.presetlist)][1]+"/"

def GPIOcleanup():
	if gv.GPIO:
		import RPi.GPIO as GPIO
		GPIO.setmode( GPIO.BCM )
		GPIO.cleanup()

def getindex(key, table, onecol=False, casesens=True):
	for i in range(len(table)):
		if onecol:
			if casesens:
				if key == table[i]:
					return i
			else:
				if key.lower() == table[i].lower():
					return i
		else:
			if casesens:
				if key == table[i][0]:
					return i
			else:
				if key.lower() == table[i][0].lower():
					return i
	return -100000

def parseBoolean(val):
	if val:
		try:
			val+=0		# is it an integer (~=boolean) ? (Integers !=0 are True)
		except:			# text is True unless starting with: Of(f), N(one), F(alse)
			if str(val)[0:2].title()=="Of" or str(val)[0].upper()=="N" or str(val)[0].upper()=="F":
				val = False
			else:
				val = True
	return val

def getvirtualCC():
	# Returns lowest CC minus 1. 
	# Since table is initiated with a -1, it will always be negative
	vCC = 0
	for m in gv.controllerCCs:
		if m[1] < vCC:
			vCC = m[1]
	return vCC-1

def setCCmap(voice):
	gv.CCmap = copy.deepcopy( list(gv.CCmapBox) )	# construct this voice's CC setup
	for i in range( len(gv.CCmapSet) ):
		found = False
		if (gv.CCmapSet[i][3] == 0
		or gv.CCmapSet[i][3] == voice):				# voice applies
			for j in range( len(gv.CCmap) ):		# so check if button is known
				if gv.CCmapSet[i][0] == gv.CCmap[j][0]:
					found = True
					if (gv.CCmapSet[i][3] >= gv.CCmap[j][3]):	# voice specific takes precedence
						gv.CCmap[j] = copy.deepcopy( gv.CCmapSet[i] )	# replace entry
					continue
			if not found:
				gv.CCmap.append( copy.deepcopy( gv.CCmapSet[i] ) )		# else add entry
