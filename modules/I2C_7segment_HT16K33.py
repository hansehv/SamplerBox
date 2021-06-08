#########################################
##  7-SEGMENT DISPLAY from original samplerbox, slightly changed
##
##   SamplerBox extended by HansEhv (https://github.com/hansehv)
#########################################
from smbus import SMBus

# only these characters are used. See HT16K33 datasheet
CHARACTER_MAP = {
    0x2D : 0x40, # -
    0x30 : 0x3F, # 0
    0x31 : 0x06, # 1
    0x32 : 0x5B, # 2
    0x33 : 0x4F, # 3
    0x34 : 0x66, # 4
    0x35 : 0x6D, # 5
    0x36 : 0x7D, # 6
    0x37 : 0x07, # 7
    0x38 : 0x7F, # 8
    0x39 : 0x67,  # 9
    0x45 : 0x79, # E 
    0x4C : 0x38, # L
}

# address of the four digits that can be displayed
DIGIT_ADDRESS = [0x00, 0x02, 0x06, 0x08]

bus = SMBus(1)

# clear the display
for i in range(0x10):
    bus.write_byte_data(0x70, i, 0x00)

# turn on oscillator
bus.write_byte(0x70, 0x21)

# configure display
bus.write_byte(0x70, 0x81)

# set brightness (7 is about right)
bus.write_byte(0x70, 0xE7)

print("Starting HT16K33 7-segment display")

def display(s7=""):
    index = 0
    if s7 != "":
        for k in s7:
            try:
                bus.write_byte_data(0x70, DIGIT_ADDRESS[index % len(DIGIT_ADDRESS)], CHARACTER_MAP[ord(k)] % 0x100)
		index += 1
            except Exception as e:
                pass
