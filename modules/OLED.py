###############################################################
#  OLED display via SPI interface contributed by TheNothingMan,
#  see: https://github.com/TheNothingMan/SamplerBox
#
#  It uses Luma.OLED which has drivers for: SSD1306, SSD1309,
#  SSD1322, SSD1325, SSD1327, SSD1331, SSD1351, SH1106.
#  Current code only supports SH1106.
#  Please contact me (Hans) if you have or need additions !
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

import UI

print("Started OLED display")

class oled:
    def __init__(self):
        self.busy=False
        self.s4=''
        self.s5=''
        self.s6=''
        cmd = "hostname -I | cut -d\' \' -f1"
        IP = subprocess.check_output(cmd, shell = True )
        self.IP="IP:"+IP
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

    def display(msg,menu1,menu2,menu3)
        if self.busy: return False
        self.busy=True
        with self.canvas as draw:
            draw.rectangle((0, 0, self.device.width-1, self.device.height-1), outline=0, fill=0)
           if UI.USE_ALSA_MIXER:
                s1 = "%s | Vol: %d%%" % (UI.Mode(), UI.SoundVolume())
            else:
                s1 = "Mode: %s" % (gv.sample_mode)
            s2=msg
            if s2 == '':
                if UI.Voice()>1: s2=str(UI.Voice())+":"
                if UI.Presetlist()!=[]: s2 += UI.Presetlist()[UI.getindex(UI.Preset(),UI.Presetlist())][1]
            #s3 = "Scale:%s" % (UI.Scalename()[UI.Scale()])
            s3 = "Scale:%s | Chord:%s" % (UI.Scalename()[UI.Scale()], UI.Chordname()[UI.Chord()])
            # Change menu lines if necessary
            if menu1 != '':
                self.s4=menu1
                self.s5=menu2
                self.s6=menu3
            s6=self.s6 if self.s6!='' else self.IP
            draw.text((self.x, self.top), s1, font=self.font, fill=255)
            draw.rectangle((self.x, self.top+11,self.device.width, 21), outline=255, fill=255)
            draw.text((self.x+2, self.top+12), s2, font=self.font,fill=0)
            draw.text((self.x, self.top+24), s3, font=self.font, fill=255)
            draw.text((self.x, self.top+32), self.s4, font=self.font, fill=255)
            draw.text((self.x, self.top+40), self.s5, font=self.font, fill=255)
            draw.text((self.x, self.top+48), s6, font=self.font, fill=255)
        self.busy=False
        return True
