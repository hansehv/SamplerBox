###############################################################
#  OLED display via SPI interface contributed by TheNothingMan,
#  see: https://github.com/TheNothingMan/SamplerBox
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
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

import gv

print("Started OLED display")

class oled:
        def __init__(self):
                # Parse config for display settings
                driver = gv.cp.get(gv.cfg,"OLED_DRIVER".lower())
                RST = gv.cp.getint(gv.cfg,"OLED_RST".lower())
                CS = gv.cp.getint(gv.cfg,"OLED_CS".lower())
                DC = gv.cp.getint(gv.cfg,"OLED_DC".lower())
                port = gv.cp.getint(gv.cfg,"OLED_PORT".lower())
                # Load default font.
                self.font = ImageFont.load_default()
                
                # self.largeFont = ImageFont.truetype("arial.ttf",16)
                # Create blank image for drawing.
                # Make sure to create image with mode '1' for 1-bit color.
                self.width = gv.cp.getint(gv.cfg,"OLED_WIDTH".lower())
                self.height = gv.cp.getint(gv.cfg,"OLED_HEIGHT".lower())
                self.image = Image.new('1', (self.width, self.height))

                # First define some constants to allow easy resizing of shapes.
                self.padding = gv.cp.getint(gv.cfg,"OLED_PADDING".lower())
                self.top = self.padding
                self.bottom = self.height-self.padding
                # Move left to right keeping track of the current x position for drawing shapes.
                self.x = 0
                serial = spi(device=port, port=port, bus_speed_hz = 8000000, transfer_size = 4096, gpio_DC = DC, gpio_RST = RST)
                
                if driver=="SH1106":
                        self.device = sh1106(serial, rotate=2)
                else:
                        print("Wrong driver")
                self.canvas = canvas(self.device)

        def display(self,s2):
                with self.canvas as draw:
                        draw.rectangle((0, 0, self.device.width-1, self.device.height-1), outline=0, fill=0)
                        cmd = "hostname -I | cut -d\' \' -f1"
                        IP = subprocess.check_output(cmd, shell = True )
                        if gv.USE_ALSA_MIXER:
                                s3 = "Scale:%s" % (gv.scalename[gv.currscale])
                                s4 = "Chord: %s" % (gv.chordname[gv.currchord])
                                s5 = "MIDI Ch: %d" % (gv.MIDI_CHANNEL)
                                s1 = "%s | Vol: %d%%" % (gv.sample_mode, gv.volume)
                        else:
                                s3 = "Scale:%s | Chord:%s" % (gv.scalename[gv.currscale], gv.chordname[gv.currchord])
                                s4 = "Chord: %s" % (gv.chordname[gv.currchord])
                                s5 = "MIDI Ch: %d" % (gv.MIDI_CHANNEL)
                                s1 = "Mode: %s" % (gv.sample_mode)
                        if s2 == "":
                                if gv.currvoice>1: s2=str(gv.currvoice)+":"
                                s2 += gv.basename
                                if gv.buttfunc>0:
                                        s1 += " "*15
                                        s1 = s1[:13] + "> "+gv.button_disp[gv.buttfunc]
                        draw.text((self.x, self.top), s1, font=self.font, fill=255)
                        draw.rectangle((self.x, self.top+11,self.device.width, 21), outline=255, fill=255)
                        draw.text((self.x+2, self.top+12), s2, font=self.font,fill=0)
                        draw.text((self.x, self.top+24), s3, font=self.font, fill=255)
                        draw.text((self.x, self.top+32), s4, font=self.font, fill=255)
                        draw.text((self.x, self.top+40), s5, font=self.font, fill=255)
                        draw.text((self.x, self.top+48), "IP:"+IP, fill=255)
