###############################################################
#  LCD display via SPI interface adapted from OLED.py
#
#  Currently supports only Pimoroni st7789 LCD driver
#  but is (as ws the OLED.py) extensible.
#  Please contact me (Hans) if you have or need additions !
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
# -*- coding:utf-8 -*-

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import UI
import gv
driver = gv.cp.get(gv.cfg, "PIM_LCD_DRIVER".lower())
if driver == "ST7789":
    from ST7789 import ST7789


SPI_SPEED_MHZ = 80


class pim_lcd:
    def __init__(self):
        self.busy = False
        self.s4 = ''
        self.s5 = ''
        self.s6 = ''
        # Parse config for display settings
        BL = gv.cp.getint(gv.cfg, "PIM_LCD_BL".lower())
        CS = gv.cp.getint(gv.cfg, "PIM_LCD_CS".lower())
        DC = gv.cp.getint(gv.cfg, "PIM_LCD_DC".lower())
        port = gv.cp.getint(gv.cfg, "PIM_LCD_PORT".lower())
        print("Starting LCD %s, using SPI port %d and GPIO BL=%d, CS=%d, DC=%d"
              % (driver, port, BL, CS, DC))

        # Load default font.
        #self.font = ImageFont.load_default()
        self.font = ImageFont.truetype("modules/res/DejaVuSans.ttf",28)
        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        self.width = gv.cp.getint(gv.cfg, "PIM_LCD_WIDTH".lower())
        self.height = gv.cp.getint(gv.cfg, "PIM_LCD_HEIGHT".lower())
        self.image = Image.new("RGB", (self.width, self.height), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)

        # First define some constants to allow easy resizing of shapes.
        self.padding = gv.cp.getint(gv.cfg, "PIM_LCD_PADDING".lower())
        self.top = self.padding
        self.bottom = self.height-self.padding
        # Move left to right keeping track of the current x position for drawing shapes.
        self.x = 0

        if driver == "ST7789":
            self.device = ST7789(
                                rotation=90,   # Needed to display the right way up on Pirate Audio
                                port=port,     # SPI port
                                cs=CS,         # SPI port Chip-select channel
                                dc=DC,         # BCM pin used for data/command
                                backlight=BL,
                                spi_speed_hz=SPI_SPEED_MHZ * 1000 * 1000)
        else:
            print("Wrong driver")

    def display(self, msg, menu1, menu2, menu3):
        if self.busy: 
            return False
        self.busy = True
        # #########START DRAWING##########################
        self.draw.rectangle((0, 0, self.device.width-1, self.device.height-1), fill=(0,0,0))
        s1 = msg
        s2 = ''
        if s1 == '':
            if UI.Presetlist() != []:
                s1 = UI.Presetlist()[UI.getindex(UI.Preset(), UI.Presetlist())][1]
                preset_str = s1.split(" ",1)
                preset_num = preset_str[0]
                s1 = preset_str[1]
                s2 = preset_num # put preset number and voice number on line 2
            if UI.Voice() > 1:
                s2 += ' voice:'+ str(UI.Voice())

        s3a = "Scale:%s" % (UI.Scalename()[UI.Scale()])
        s3b = "Chord:%s" % (UI.Chordname()[UI.Chord()])
        # Change menu lines if necessary
        if menu1 != '':
            self.s4 = menu1
            self.s5 = menu2
            self.s6 = menu3
        s6 = self.s6 if self.s6 != '' else UI.IP()
        if UI.USE_ALSA_MIXER:
            s7 = "%s | Vol: %d%%" % (UI.Mode(), UI.SoundVolume())
        else:
            s7 = "Mode: %s" % (gv.sample_mode)
        self.draw.text((self.x, self.top), s1, font=self.font, fill=(128,255,0))
        # self.draw.rectangle((self.x, self.top + 28, self.device.width, self.top + 30), fill=(255,255,255))
        self.draw.text((self.x+2, self.top+32), s2, font=self.font, fill=(64,128,0))
        self.draw.text((self.x, self.top+60), s3a, font=self.font, fill=(127,127,127))
        self.draw.text((self.x, self.top+84), s3b, font=self.font, fill=(127,127,127))
        self.draw.text((self.x, self.top+112), self.s4, font=self.font, fill=(255,128,0))
        if len(menu3) > 0:  # display menu item in yellow if you can scroll values
            self.draw.text((self.x, self.top+140), self.s5, font=self.font, fill=(255,255,0)) 
        else:
            self.draw.text((self.x, self.top+140), self.s5, font=self.font, fill=(255,128,0))
        self.draw.text((self.x, self.top+168), s6, font=self.font, fill=(0,128,255))
        self.draw.text((self.x, self.top+198), s7, font=self.font, fill=(0,64,128))

        self.device.display(self.image)
        # #########END DRAWING##########################
        self.busy = False
        return True
