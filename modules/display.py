#################################################################
#   Setup direct connected HW displays (LCD, OLED, LEDS), if any.
#   It serves one menu text display plus indicator LED's
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv),
#################################################################

import gv

segment_display = None
character_display = None
LEDs_display = None

# -------- LED's can always be served

if gv.cp.getboolean(gv.cfg,"USE_LEDS".lower()):
	gv.GPIO=True
	import LEDs
	LEDs_display= LEDs.signal
	LEDs.green(False)
	LEDs.red(True,True)

# -------- Choose the line (menu) display

if gv.cp.getboolean(gv.cfg,"USE_HD44780_16x2_LCD".lower()):
	gv.GPIO=True
	import lcd_16x2
	lcd = lcd_16x2.HD44780()
	character_display = lcd.display

elif gv.cp.getboolean(gv.cfg,"USE_I2C_LCD".lower()):
	import I2C_lcd
	character_display = I2C_lcd.display

elif gv.cp.getboolean(gv.cfg,"USE_OLED".lower()):
	gv.GPIO=True
	import OLED
	oled = OLED.oled()
	character_display = oled.display

elif gv.cp.getboolean(gv.cfg,"USE_PIMORONI_LCD".lower()):
	gv.GPIO=True
	import PIM_LCD
	pimlcd = PIM_LCD.pim_lcd()
	character_display = pimlcd.display

elif gv.cp.getboolean(gv.cfg,"USE_I2C_7SEGMENTDISPLAY".lower()):
	import I2C_7segment
	segment_display = I2C_7segment.display

elif gv.cp.getboolean(gv.cfg,"USE_I2C_7SEGMENTDISPLAY_HT16K33".lower()):
	import I2C_7segment_HT16K33
	segment_display = I2C_7segment_HT16K33.display

# -------- The final display routine

def display(msg='', msg7seg='', menu1='', menu2='', menu3='', *z):
	if LEDs_display:
		LEDs_display()
	if character_display:
		character_display(msg, menu1, menu2, menu3)
	elif segment_display:
		segment_display(msg7seg)

gv.display = display

display('Start Samplerbox', '----')
