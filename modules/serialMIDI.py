###############################################################
#   Midi via 5 pole DIN via serial port (UART1)
#   Adapted from https://github.com/alexmacrae/SamplerBox
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################

import threading
import serial # pip install pyserial
import gv
try:
    subprocess.call(['systemctl', 'stop', 'serial-getty@ttyAMA0.service'])
    subprocess.call(['systemctl', 'disable', 'serial-getty@ttyAMA0.service'])
except:
    #print 'Failed to stop MIDI serial'
    pass
try:
    # see hack in /boot/cmline.txt : 38400 is 31250 baud for MIDI!
    ser = serial.Serial('/dev/ttyAMA0', baudrate=38400)
    ser.close()
    ser = serial.Serial('/dev/ttyAMA0', baudrate=38400)  # this solves problem when MIDI are already arriving during RPi boot
    def midi_serial_callback():
        message = [0, 0, 0]
        runningstatus = 0
        while True:
            i = 0
            while i < 3:
                data = ord(ser.read(1))  # read a byte
                if data >> 7 != 0:
                    # status byte! this is the beginning of a midi message: http://www.midi.org/techspecs/midimessages.php
                    i = 0
                    runningstatus = data
                elif i == 0 and runningstatus > 0:  # use stored running status if available
                    message[i] = runningstatus
                    i += 1
                message[i] = data
                i += 1
                if i == 2 and message[0] >> 4 == 12:  # program change: don't wait for a third byte: it has only 2 bytes
                    message[2] = 0
                    i = 3

            gv.MidiCallback(src='MIDISERIALPORT', message=message, time_stamp=None)

    MidiThread = threading.Thread(target=midi_serial_callback)
    MidiThread.daemon = True
    MidiThread.start()
    print 'Started MIDI serial'
except:
    print 'Could not start MIDI serial'
