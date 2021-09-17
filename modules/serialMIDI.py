#################################################################
#   Midi via serial port (UART1), e.g using 5 pole DINs
#   Use rtmidi/rtmidi2 calling convention so DIN just adds to USB
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv),
#   safety measures from https://github.com/alexmacrae/SamplerBox
#################################################################

import threading, time
import serial # pip install pyserial

messages={
	8: 3,       #NoteOff
	9: 3,       #NoteOn
	10: 3,      #PolyAftertouch
	11: 3,      #ControlChange
	12: 2,      #ProgramChange
	13: 2,      #ChannelAftertouch
	14: 3,      #PitchBend
	15: 1       #SystemMessage
	}
systemmsg={
	0xF0: -1,   #SysEx	# collect untill EndOfSysex
	0xF1: 2,    #TimeCode
	0xF2: 3,    #SongPos
	0xF3: 2,    #SongSelect
	0xF4: -1,   #Undefined	# just collect till next status
	0xF5: -1,   #Undefined # likewise
	0xF6: 2,    #TuneRequest
	0xF7: 1     #EndofSysEx
	}
realtimsg={	# RealTime messages will be sent immediately
	0xF8: 1,    #Clock
	0xF9: 1,    #Undefined
	0xFA: 1,    #Start
	0xFB: 1,    #Continue
	0xFC: 1,    #Stop
	0xFD: 1,    #Undefined
	0xFE: 1,    #ActSense
	0xFF: 1     #SystemReset
	}

#   Next series of safety measures from https://github.com/alexmacrae/SamplerBox
try:
    subprocess.call(['systemctl', 'stop', 'serial-getty@ttyAMA0.service'])
    subprocess.call(['systemctl', 'disable', 'serial-getty@ttyAMA0.service'])
except:
    #print ('Failed to stop MIDI serial')
    pass

class IO:

    def __init__(self, midicallback=None, uart="SERIALPORT", realtime=False, sysex=False, timeout=0.01):

        self.midicallback = midicallback
        self.uart = uart
        self.out = True
        self.realtime = realtime
        self.sysex = sysex
        self.timeout = timeout
        try:
            self.ser = serial.Serial('/dev/ttyAMA0', baudrate=38400)
            self.ser.close()	# this solves problem when MIDI are already arriving during RPi boot
            self.ser = serial.Serial('/dev/ttyAMA0', baudrate=38400, write_timeout=self.timeout)
            self.listen()
            self.send_raw( *[137,0,0] )	# send noteoff in channel10 for note=0, a likely harmless test :-)
            time.sleep(self.timeout)
        except:
            print ('Could not start MIDI serial on %s' %self.uart)

    def listen(self):
            MidiThread = threading.Thread(target=self.callback)
            MidiThread.daemon = True
            MidiThread.start()
            print ('Opened input "%s"' %self.uart)

    def callback(self):
        message = []
        runningstatus = 0
        runningbytes = 0
        bytenum = 0

        while True:
            data = ord(self.ser.read(1))  # read a byte

            #### in midimon only !! ####
            #if verbose:
            #	print ("Serialread: %d=%s" %( data, "0x{:02X}".format(data) ) )
            #### in midimon only !! ####

            if ( data >> 7 ):	# status byte = beginning of a midi message

                if data in realtimsg:	# send real time messages immediately
                    if self.realtime:	# if they are wanted, otherwise just ignore
                        self.midicallback(mididev=self.uart, message=[data], time_stamp=None)
                    continue		# they may interleave, so don't touch current process

                if data == 0xF7:	# EndofSysEx
                    if self.sysex:	# They are allowed, so
                        bytenum = 1	# let standard procedure do its job.
                    else:		# SysEx should be ignored, so
                        message = []	# do so initialize all...
                        runningstatus = 0
                        runningbytes = 0
                        bytenum = 0
                        continue	# ...and wait for new stuff.

                else:

                    if len(message):	# Did we collect any stuff
                        # Just send as it can be undefined messages or plain errors, decision up to receiver
                        # For simplicity sake, SysEx without EndofSysEx is considered an error
                        self.midicallback(mididev=self.uart, message=message, time_stamp=None)
                        message = []	# Start a new message

                    if data in systemmsg:
                        bytenum = systemmsg[ data ]
                    else:
                        bytenum = messages[ data>>4 ]

                runningstatus = data
                runningbytes = bytenum

            elif (not bytenum) and runningstatus:	# Received data without preceding status
                    message = [runningstatus]	# use stored running status if available
                    bytenum = runningbytes-1	# and related bytes (mind we "received" one)

            message.append(data)
            bytenum -= 1
            if not bytenum:		# we're complete !
                self.midicallback(mididev=self.uart, message=message, time_stamp=None)
                message = []	# Start a new message

    def send_raw(self, *message):	# procedure name compliant with rtmidi API
        #param message example: Midi Message [144, 60, 100]
        if self.out:
            omsg = ""
            for i in message:
                omsg = "%s%s" %( omsg, chr(i) )
        try:
            self.ser.write(omsg)
        except:
            print ("Write time out on %s, closed as MIDI OUT" %self.uart)
            self.out = False

    def close_port(self):	# procedure name compliant with rtmidi API
        self.ser.close()
