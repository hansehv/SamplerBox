###############################################################
#
#   Find out network environment
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
#   see docs at https://homspace.nl/samplerbox
#   changelog in changelist.txt
#
###############################################################

import sys,subprocess
import gv

interface = "wlan0"
qvals = [
    [-30, "Amazing"],
    [-67, "Very good"],
    [-70, "Okay"],
    [-80, "Not good"],
    [-90, "Not usable"]
    ]

def match(line,keyword):
    """If the first part of line (modulo blanks) matches keyword,
    returns the end of that line. Otherwise returns None"""
    line=line.lstrip()
    length=len(keyword)
    if line[:length] == keyword:
        return line[length:]
    else:
        return None

def wireless():
    ssid = "No %s interface" %interface
    AP = False
    dbms = ""
    qval = ""
    proc = subprocess.Popen(["iw", "dev", interface, "info"],stdout=subprocess.PIPE, universal_newlines=True)
    out, err = proc.communicate()
    i = 0
    for line in out.split("\n"):
        i += 1
        parsed_line = match(line,"ssid ")
        if parsed_line:
            ssid = parsed_line
        parsed_line = match(line,"type ")
        if parsed_line:
            if parsed_line == "AP":
                AP = True
    if not AP and i>1:
        proc = subprocess.Popen(["iw", "dev", interface, "link"],stdout=subprocess.PIPE, universal_newlines=True)
        out, err = proc.communicate()
        dbm = 0
        for line in out.split("\n"):
            if match(line,"Not conn"):
                ssid = line
                break
            parsed_line = match(line,"signal: ")
            if parsed_line:
                dbm = int(parsed_line.split()[0])
                dbms = ", %sdBm: " %str(dbm)
                qval = qvals[len(qvals)-1]
                for m in qvals:
                    if dbm >= m[0]:
                        qval = m[1]
                        break
    return (["%s%s%s" %(ssid, dbms, qval)])

IPaddress="?.?.?.?"
def IP(val=None):
	global IPaddress
	try:
		IPs=IPlist()
		if len(IPs)==0:
			IPaddress="Not connected"
		elif val==None:
			if IPaddress in IPs:
				val=gv.getindex(IPaddress,IPs,True)
				if val<0:val=0
			else: val=0
		elif not isinstance(val,int):
			val=gv.getindex(val,IPs,True)
			if val<0: val=0
		elif val>=len(IPs) or val<0: val=0
		IPaddress=IPs[val]
		return IPaddress
	except: return "?.?.?.?"

gv.USE_IPv6 = gv.cp.getboolean(gv.cfg,"USE_IPv6".lower())
def IPlist(*z):						# SB IP addresses (cable and wireless plus IPv6 if enabled in configuration.txt)
	x=subprocess.check_output("hostname -I",shell=True).split()
	if gv.USE_IPv6:
		return([i for i in x])
	else:
		return([i for i in x if i.find('.')>-1])

print "IP's: %s" %(IPlist())
print "Wireless: %s" %wireless()[0]
