###############################################################
#   Menu usable for 1-4 buttons (GPIO, MidiCC, ...)
#
#   /boot/samplerbox/menu.csv contains a 2-layer menu structure.
#
#   Behaviour depends on number of buttons indicated in call
#   (1=incr, 2=incr/decr, 3=incr/decr/sel, 4=incr/dec/sel/ret)
#   1 - cycle upwards through first menu item 
#   2 - 1=cycle upwards and 2=downwards first menu item
#   3 - cycle through menus with 1=up and 2=down as defined in first column
#       choose submenu with 3=sel and if so:
#       use 1=incr/3=sel to cycle up through/select items and 2=decr to return to main menu
#       if selected item, use 1=incr/2=decr to change value and 3=sel to return to menu
#   4 - similar to 3, however
#       2=decr will now cycle downwards through items instead of return to main menu
#       4=ret will return to higher menu for all situations
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
import UI,gv,time

definition=[]	# ready by getcsv
maintxt=""		# ready by getcsv

menus=[]		# can't use a dictionary as they're unsorted in python 2.7
procs=[]
level=0			# start at main menu level
mainmenu=""
menu=[-1,0]

def init():
	global menus, mainmenu
	for m in definition:
		if m[0] not in menus: menus.append(m[0])
		if mainmenu=="":
			mainmenu=m[0]

def menu_next(val=1):
	if level==0:
		menu[0]+=val
		if menu[0]<0: menu[0]=(len(menus)-1)
		if menu[0]>=len(menus): menu[0]=0
	else:
		menu[1]+=val
		if menu[1]<0: menu[1]=(len(procs)-1)
		if menu[1]>=len(procs): menu[1]=0
def menu_prev():
	menu_next(-1)

def select(init=False):
	global level,procs
	currmenu=mainmenu if init else menus[menu[0]]
	level+=1
	if level==1:
		menu[1]=0
		procs=[]
		for m in definition:
			if m[0]==currmenu:
				procs.append(m)
def selret():
	global level
	if level>0: level-=1

def value_up(val=1):
	x=UI.procs[procs[menu[1]][1]][1]()
	y=0
	if isinstance(x,basestring):	# a returned string means its a table value or boolean
		if procs[menu[1]][3]=="boolean":
			y=True if val>0 else False
		t=UI.procs[procs[menu[1]][3]][1]()
		y=UI.getindex(x,t,True)
		if y<0: y=0		# index=0, default value can have various names: "", "None", "____" etcetera
		y=value_idx_walk(val,t,y)
	elif procs[menu[1]][3]=="boolean":	# a returned integer might be boolean, we need advice from menu-3
		y=(val>0)
	elif isinstance(procs[menu[1]][3],basestring):	# it may also mean a table value or index
		t=UI.procs[procs[menu[1]][3]][1]()
		tt=t[0]
		if isinstance(tt,list) and isinstance(tt[0],int):	# integer value in multi-dimension table
			z=UI.getindex(x,t)
			y=value_idx_walk(val,t,z)
			if procs[menu[1]][3]=="Presetlist":	# historical special for compatibility with MIDI ProgramUp/Down buttons
				y=t[y][0]
		else:			# it can only be an index
			y=value_idx_walk(val,t,x)
	else:
		y=x+val*procs[menu[1]][5]
		if y<=procs[menu[1]][3]: y=procs[menu[1]][3]
		elif y>=procs[menu[1]][4]: y=procs[menu[1]][4]
	UI.procs[procs[menu[1]][1]][1](y)
def value_dn():
	value_up(-1)
def value_idx_walk(val,t,x):
	l=len(t)
	y=x+val
	if y<0: y=0 if l<3 else l-1
	elif y>=l: y=0 if l>2 else l-1
	return y
	
def nofunc(): pass

###############################################################
#		Navigation including display control
###############################################################
butfunc={
	1: [menu_next,menu_next,value_up],
	2: [menu_prev,menu_prev,value_dn],
	3: [select,select,selret],
	4: [nofunc,selret,selret]
	}

def nav(button, numbut):
	global level,menu
	if button in butfunc:
		if menu[0]==-1:
			if numbut<3:
				level=0
				select(True)	# cover your back for multiple buttons (eg GPIO & midi)
				level=2
			menu[0]=0
		if button==2 and numbut==3 and level==1: button=4
		butfunc[button][level]()
		while True:
			if not UI.RenewMedia():
				displayed=UI.display('','',line1(),line2(),line3())
				if displayed==None or displayed: break
			time.sleep(0.1)
	elif button!=0: print "Unknown menu button", button

def line1(*z):
	if level==0: return maintxt
	return menus[menu[0]]
	
def line2(*z):
	if level==0: return menus[0 if menu[0]<0 else menu[0]]
	return procs[menu[1]][2]

def line3(*z):
	if level<2: return ""
	s=""
	x=UI.procs[procs[menu[1]][1]][1]()
	if isinstance(x,basestring):	# luckily it's a string
		s=x
	elif procs[menu[1]][3]=="boolean":	# a number can be a boolean
		s="On" if x else "Off"
	elif isinstance(procs[menu[1]][3],basestring):	# and 'something' with a descriptive table
		t=UI.procs[procs[menu[1]][3]][1]()
		tt=t[0]
		if isinstance(tt,list):		# more than one dimension in this table
			if isinstance(tt[0],int):	# the integer is either a value in the table
				s=t[UI.getindex(x,t)][1]
			else:						# or it is index of the table
				s=t[x][1]	# so we need the descriptive field
		else:						# just one dimension means the integer is the index
			s=t[x]	# so description is the only field
	else:
		s="%i" %int(x)			# and pfew, yes, there are straighforward numbers too
	return ("___" if s=="" else s)

###############################################################
#		Define buttons suitable for midicontrol messages
###############################################################
CCbuts=0
CCbut=[]
def incr(*z):
	nav(1,CCbuts)
def decr(*z):
	nav(2,CCbuts)
def sel(*z):
	nav(3,CCbuts)
def ret(*z):
	nav(4,CCbuts)
def CCdef():
	global CCbuts
	CCbuts=0
	for m in gv.CCmap:
		if m[1] in CCbut: CCbuts+=1
CCbut.append(gv.setMC(gv.MENU_INCR,incr))  	# and announce the procs while preserving its index
CCbut.append(gv.setMC(gv.MENU_DECR,decr))
CCbut.append(gv.setMC(gv.MENU_SEL,sel))
CCbut.append(gv.setMC(gv.MENU_RET,ret))
gv.menu_CCdef=CCdef

###############################################################
#		Define table for general user interface use (UI.py)
###############################################################
buttons=["","Up/Next","Down/Prev","Select","Return"]
