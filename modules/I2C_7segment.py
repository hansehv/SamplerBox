#########################################
##  7-SEGMENT DISPLAY from original samplerbox, slightly changed
##
##   SamplerBox extended by HansEhv (https://github.com/hansehv)
#########################################
import smbus
import time
bus = smbus.SMBus(1)    # using I2C => GPIO2+3+PWR&GND = pins 3,5,?,?
def display(s7=""):     # ignore calls not meant for us
    if s7!="":
        for k in '\x76\x79\x00' + s7:     # position cursor at 0
            try:
                bus.write_byte(0x71, ord(k))
            except:
                try:
                    bus.write_byte(0x71, ord(k))
                except:
                    pass
            time.sleep(0.002)
