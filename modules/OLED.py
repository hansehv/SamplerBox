# -*- coding:utf-8 -*-

from luma.core.interface.serial import i2c, spi
from luma.core.render import canvas
from luma.core import lib

from luma.oled.device import sh1106
import RPi.GPIO as GPIO

import time
import subprocess

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

RST = 25
CS = 8
DC = 24

USER_I2C = 0

if  USER_I2C == 1:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RST,GPIO.OUT)
        GPIO.output(RST,GPIO.HIGH)

        serial = i2c(port=1, address=0x3c)
else:
        serial = spi(device=0, port=0, bus_speed_hz = 8000000, transfer_size = 4096, gpio_DC = 24, gpio_RST = 25)

#device = sh1106(serial, rotate=2) #sh1106

print("Started OLED display")

class OLED:
        def __init__(self, width=128, height=64, padding=-2, x=0):
                # Load default font.
                self.font = ImageFont.load_default()

                # Create blank image for drawing.
                # Make sure to create image with mode '1' for 1-bit color.
                self.width = width
                self.height = height
                self.image = Image.new('1', (width, height))

                # First define some constants to allow easy resizing of shapes.
                self.padding = padding
                self.top = padding
                self.bottom = height-padding
                # Move left to right keeping track of the current x position for drawing shapes.
                self.x = 0
                serial = spi(device=0, port=0, bus_speed_hz = 8000000, transfer_size = 4096, gpio_DC = 24, gpio_RST = 25)
                self.device = sh1106(serial, rotate=2)
                self.canvas = canvas(self.device)


        def display(self,s2,basename='',sample_mode='',USE_ALSA_MIXER=False,volume=0,currvoice=0,currchord=0,chordname=[''],scalename=[''],currscale=0,button_disp=[''],buttfunc=0,midichannel=0):
                with self.canvas as draw:
                        draw.rectangle((0, 0, self.device.width-1, self.device.height-1), outline=0, fill=0)
                        if USE_ALSA_MIXER:
                                s3 = "Scale:%s" % (scalename[currscale])
                                s4 = "Chord: %s" % (chordname[currchord])
                                s5 = "MIDI Ch: %d" % (midichannel)
                                s1 = "%s | Vol: %d%%" % (sample_mode, volume)
                        else:
                                s3 = "Scale:%s | Chord:%s" % (scalename[currscale], chordname[currchord])
                                s1 = "Mode: %s" % (sample_mode)
                        if s2 == "":
                                if currvoice>1: s2=str(currvoice)+":"
                                s2 += basename
                                if buttfunc>0:
                                        s1 += " "*15
                                        s1 = s1[:13] + "> "+button_disp[buttfunc]
                        draw.text((self.x, self.top), s1, font=self.font, fill=255)
                        draw.text((self.x, self.top+8), s2, font=self.font,fill=255)
                        draw.text((self.x, self.top+24), s3, font=self.font, fill=255)
                        draw.text((self.x, self.top+32), s4, font=self.font, fill=255)
                        draw.text((self.x, self.top+40), s5, font=self.font, fill=255)
