###############################################################
#  LCD display via I2C interface inspired by David Hilowitz,
#  see: https://github.com/dhilowitz/SamplerBox
#
#  Supports 16x2 and 20x4 I2C HD44780 displays
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
import smbus,time
import UI,gv

# Define some device constants
LCD_CHR = 1 # Mode - Sending data
LCD_CMD = 0 # Mode - Sending command

LCD_LINE = [0x80, 0xC0, 0x94, 0xD4] # LCD RAM addresses

LCD_BACKLIGHT  = 0x08  # On
#LCD_BACKLIGHT = 0x00  # Off

ENABLE = 0b00000100 # Enable bit

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

# get device characteristics
I2C_DISPLAY_LCD_WIDTH=16
I2C_DISPLAY_LCD_LINES=2
I2C_LCD_ADDR=0x3f
I2C_LCD_PORT=1
try:
	details=gv.cp.get(gv.cfg,"USE_I2C_LCD".lower()).split("x")	# either True, 16x2 or 20x4
	I2C_DISPLAY_LCD_WIDTH=int(details[0])
	I2C_DISPLAY_LCD_LINES=int(details[1])
	I2C_DISPLAY_LCD_LINES=4 if I2C_DISPLAY_LCD_LINES>4 else I2C_DISPLAY_LCD_LINES
except: pass
try:
	I2C_LCD_ADDR=int(gv.cp.get(gv.cfg,"I2C_LCD_ADDR".lower()),16)
except:	pass
try:
	I2C_LCD_PORT=int(gv.cp.get(gv.cfg,"I2C_LCD_PORT".lower()),16)
except:	pass

print "Starting I2C LCD.."
bus = smbus.SMBus(I2C_LCD_PORT)	 # using I2C

# class variables
busy=False
prevs=['']*4

#--------- SUBROUTINES ----------
def lcd_init():
	# Initialise display
	lcd_byte(0x33,LCD_CMD) # 110011 Initialise
	lcd_byte(0x32,LCD_CMD) # 110010 Initialise
	lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
	lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off 
	lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
	lcd_byte(0x01,LCD_CMD) # 000001 Clear display
	time.sleep(E_DELAY)

def lcd_byte(bits, mode):
	# Send byte to data pins
	# bits = the data
	# mode = 1 for data
	#		0 for command

	bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
	bits_low = mode | ((bits<<4) & 0xF0) | LCD_BACKLIGHT

	# High bits
	bus.write_byte(I2C_LCD_ADDR, bits_high)
	lcd_toggle_enable(bits_high)

	# Low bits
	bus.write_byte(I2C_LCD_ADDR, bits_low)
	lcd_toggle_enable(bits_low)

def lcd_toggle_enable(bits):
	# Toggle enable
	time.sleep(E_DELAY)
	bus.write_byte(I2C_LCD_ADDR, (bits | ENABLE))
	time.sleep(E_PULSE)
	bus.write_byte(I2C_LCD_ADDR,(bits & ~ENABLE))
	time.sleep(E_DELAY)
  
def lcd_string(line,message):
	# Send string to display
	message = message.ljust(I2C_DISPLAY_LCD_WIDTH," ")
	lcd_byte(LCD_LINE[line], LCD_CMD)
	for i in range(I2C_DISPLAY_LCD_WIDTH):
		lcd_byte(ord(message[i]),LCD_CHR)

#--------- Actual Display ----------
#	supports 2 and 4 line displays
def display(msg='',menu1='',menu2='',menu3='',*z):
	global busy,prevs
	if busy: return False
	busy=True
	# ---   default behaviour for first two lines
	s=['']*4
	vol=" %d%%" %UI.SoundVolume() if UI.USE_ALSA_MIXER else ""
	s[0] = "%s%s %s%s" % (UI.Scalename()[UI.Scale()], UI.Chordname()[UI.Chord()], UI.Mode(), vol)
	if UI.Voice()>1: s[1]=str(UI.Voice())+":"
	if UI.Presetlist()!=[]: s[1] += UI.Presetlist()[UI.getindex(UI.Preset(),UI.Presetlist())][1]

	# ---   menu control, fit the 3 menu lines into two/four display lines
	if I2C_DISPLAY_LCD_LINES==2:
		if menu1!='':
			if menu3=='':
				s[0]=menu1
				s[1]=menu2
			else:
				s[0]=menu1+":"+menu2
				if len(s[0])>I2C_DISPLAY_LCD_WIDTH:  # make sure the most significant part is displayed
					s[0]=menu1[:I2C_DISPLAY_LCD_WIDTH-1-len(menu2)]+":"+menu2
				s[1]=menu3
			if msg!='': s[1]=msg	# a message is important, so override s[1]
	else:
		if menu1!='':
			if menu3=='':
				s[2]=menu1
				s[3]=menu2
			else:
				s[1]=menu1
				s[2]=menu2
				s[3]=menu3
		else:
			s[2]=prevs[2]
			s[3]=prevs[3]

	# ---   display the result
	for i in xrange(I2C_DISPLAY_LCD_LINES):
		if not s[i]==prevs[i]:
			lcd_string(i,s[i])
			prevs[i]=s[i]
	busy=False
	return True

lcd_init()
time.sleep(0.5)
