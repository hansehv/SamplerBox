#        -------------------------
#         M i d i   M o n i t o r
#        -------------------------

#   Utility for SamplerBox extension by HansEhv (https://github.com/hansehv)
#
#   Usage: python midimon.py

import rtmidi2, time, sys, getopt, re

print ( "\n# Watch the messages on screen:\n"
        "#  - is the expected midi device opened ?\n"
        "#  - if you play your midi device, do you see this ?\n"
        "#\n# This monitor's logic is similar to samplerbox\n"
        "#\n# So: if you see signals received here, but get no sound,\n"
        "#     it's not because your MIDI device isn't recognized by SB.\n"
        "#     If you see nothing, also try with the -v option\n"
        "#\n# ctrl-C ends (as usual...)\n"
        "#\n# optional commandline parameters for opening through port(s)\n"
        "#    -t <midi-out port enclosed in parenthesis>\n"
        "#       you can use multiple -t\n"
        "#    -a opens all available output ports\n"
        "#    -e opens/defines embedded serial output as extra device\n"
        "#       and disables replaces any real MIDI serial device as output\n"
        "#    optional extras:\n"
        "#    -r Accept realtime messages via serialreads\n"
        "#    -s Accept sysex messages via serialreads\n"
        "#    -v Verbose: show parameters passed to call-back and serialreads\n"
        )

verbose = False
realtime = False
sysex = False

thru_ports = []
arglist = sys.argv[1:]

try:
    args, vals = getopt.getopt(arglist, "naevrst:")
    e = False
    for arg, val in args:
        if arg[1:] in "na":
            if arg == "-a":
                thru_ports = ["All"]
            else:
                thru_ports = []
        elif arg == "-e":
            e = True
        elif arg == "-v":
            verbose = True
        elif arg == "-r":
            realtime = True
        elif arg == "-s":
            sysex = True
        elif arg == "-t":
            thru_ports.append(val)
    if e:
        thru_ports.append("EMBEDDED")

except getopt.error as err:
    print (str(err))
    exit()

messages={
        8: [3,"NoteOff"],
        9: [3,"NoteOn"],
        10: [3,"PolyAftertouch"],
        11: [3,"ControlChange"],
        12: [2,"ProgramChange"],
        13: [2,"ChannelAftertouch"],
        14: [3,"PitchBend"],
        15: [1,"SystemMessage"]
        }
systemmsg={
        0xF0: [-1,"SysEx"],     # collect untill EndOfSysex
        0xF1: [2,"TimeCode"],
        0xF2: [3,"SongPos"],
        0xF3: [2,"SongSelect"],
        0xF4: [-1,"Undefined"], # just collect till next status
        0xF5: [-1,"Undefined"], # likewise
        0xF6: [2,"TuneRequest"],
        0xF7: [1,"EndofSysEx"]
        }
realtimsg={   # RealTime messages will be sent immediately
        0xF8: [1,"Clock"],
        0xF9: [1,"Undefined"],
        0xFA: [1,"Start"],
        0xFB: [1,"Continue"],
        0xFC: [1,"Stop"],
        0xFD: [1,"Undefined"],
        0xFE: [1,"ActSense"],
        0xFF: [1,"SystemReset"]
        }
standardCC={
        0: "BankSelect",
        1: "Modwheel",
        2: "Breath controller",
        4: "Foot Controller",
        5: "Portamento time",
        6: "Data entry MSB",
        7: "Main volume",
        8: "Balance",
        10: "Pan",
        11: "Expression",
        12: "Effect Control1",
        13: "Effect Control2",
        16: "GenPurp.Control1",
        17: "GenPurp.Control2",
        18: "GenPurp.Control3",
        19: "GenPurp.Control4",
        32: "LSB BankSelect",
        33: "LSB Modwheel",
        34: "LSB Breath controller",
        35: "LSB ",
        36: "LSB Foot Controller",
        37: "LSB Portamento time",
        38: "LSB Data entry",
        39: "LSB Main volume",
        40: "LSB Balance",
        43: "LSB Expression",
        42: "LSB Pan",
        43: "LSB Expression",
        44: "LSB Effect Control1",
        45: "LSB Effect Control2",
        48: "LSB GenPurp.Control1",
        49: "LSB GenPurp.Control2",
        50: "LSB GenPurp.Control3",
        51: "LSB GenPurp.Control4",
        64: "Sustain/damper pedal",
        65: "Portamento",
        66: "Sostenuto",
        67: "Soft pedal",
        69: "Hold 2",
        91: "ExternalEffects depth",
        92: "Tremolo depth",
        93: "Chorus depth",
        94: "Celeste(detune) depth",
        95: "Phaser depth",
        96: "Data increment",
        97: "Data decrement",
        98: "NonReg'd Parm# LSB",
        99: "NonReg'd Parm# MSB",
        100: "Registered Parm# LSB",
        101: "Registered Parm# MSB"
        }
notenames=["C","Cs","C#","Dk","D","Ds","D#","Ek","E","Es","F","Fs","F#","Gk","G","Gs","G#","Ak","A","As","A#","Bk","B","Bs"]
def midinote2notename(midinote,fractions):
    notename=None
    octave=None
    note=None
    if   midinote==-2: notename="Ctrl"
    elif midinote==-1: notename="None"
    else:
        #if midinote<gv.stop127 and midinote>(127-gv.stop127):
            if fractions==1:
                octave,note=divmod(midinote,12)
                octave-=1
                note*=2
            else:
                octave,note=divmod(midinote+36,24)
            notename="%s%d" %(notenames[note],octave)
        #else: notename="%d" %(midinote)
    return notename

def checklength(definition, gotlen):
    if ( gotlen != definition[0] ):
        print (" ==> %s is defined as %d bytes, but message has %d bytes" %( definition[1], definition[0], gotlen ) )
 
#################################################################
#             M I D I    C A L L B A C K
#              what samplerbox receives
#               (and sends to through)
#################################################################

def MidiCallback(mididev, message, time_stamp):
    if verbose:
        time_stamp=None
        print ( "%s, %s, %s"  %(mididev, message, time_stamp) )
        hexp = "MIDImsg ="
        for i in message:
            hexp = "%s %s" %( hexp, "0x{:02X}".format(i) )
        print ( hexp )

    for outport in outports:
        if mididev != outports[outport][0]:  # don't return to sender
            print ( " ... forwarding %d bytes to '%s'" %( len(message), outports[outport][0] ) )
            outports[outport][1].send_raw(*message)

    status = message[0]
    msglen = len(message)
    data1 = message[1] if msglen > 1 else 0
    data2 = message[2] if msglen > 2 else 0
    dataval = "0x{:04X}".format( data1 + data2*256 )

    if status in systemmsg:
        spec = "%d"%dataval if systemmsg[status][0] > 0 else ""
        print ( '"%s", %d bytes -> %s, message %s' % ( mididev, msglen, systemmsg[status][1], spec ) )
        checklength(systemmsg[status], msglen)
    elif status in realtimsg:
        if realtime:
            print ( '"%s", %d bytes -> %s' % ( mididev, msglen, realtimsg[status][1] ) )
            checklength(realtimsg[status], msglen)
    else:
        messagetype = status >> 4
        messagechannel = (status&0xF) + 1   # make channel# human..
        spec = ""
        if messagetype == 8 or messagetype == 9:
            spec = "%d=%s, velocity=%d" %(data1, midinote2notename(data1,1), data2)
        elif messagetype == 12: # Program change
            spec = '%d (=%d for humans)' %(data1, data1+1)
        elif messagetype == 14: # Pitchbend
            spec = '%s (SB uses %d)' %(dataval, data2)
        elif messagetype == 11: # control change (CC = Continuous Controllers)
            if data1 in standardCC:
                spec = "%s %d" %(standardCC[data1], data2)
            else:
                spec = "%d->%d" %(data1, data2)
        else:
            spec = "%s" %dataval
        print ( '"%s" (%d bytes) Channel %d, %s %s' % (mididev, msglen, messagechannel, messages[messagetype][1], spec) )
        checklength(messages[messagetype], msglen)

#################################################################
#   Midi via serial port (UART1), e.g using 5 pole DINs
#   Use rtmidi/rtmidi2 calling convention so DIN just adds to USB
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv),
#   safety measures from https://github.com/alexmacrae/SamplerBox
#################################################################

import threading, time
import serial # pip install pyserial

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
            self.ser.close()        # this solves problem when MIDI are already arriving during RPi boot
            self.ser = serial.Serial('/dev/ttyAMA0', baudrate=38400, timeout=None, writeTimeout=self.timeout)
            # Above statement has a deprecated syntax as SB uses old serial in the Python 2.7 versions
            # Deprecated still works, but current is / should be:
            #self.ser = serial.Serial('/dev/ttyAMA0', baudrate=38400, write_timeout=self.timeout)
            print ( 'Started %s as MIDI device "%s"' %( self.ser.name, self.uart ) )
            self.send_raw( *[137,0,0] )        # send noteoff in channel10 for note=0, a likely harmless test :-)
            time.sleep(self.timeout)
            if self.out:
                print ('Opened %s for MIDI OUT' %self.uart)
            self.listen()
        except:
            print ('Could not start MIDI serial on %s' %self.uart)

    def listen(self):
        MidiThread = threading.Thread(target=self.callback)
        MidiThread.daemon = True
        MidiThread.start()
        print ('Listening on %s for MIDI IN' %self.uart)

    def callback(self):
        message = []
        runningstatus = 0
        runningbytes = 0
        bytenum = 0

        while True:
            data = ord(self.ser.read(1))  # read a byte

            #### in midimon only !! ####
            if verbose:
                    print ("Serialread: %d=%s" %( data, "0x{:02X}".format(data) ) )
            #### in midimon only !! ####

            if ( data >> 7 ):           # status byte = beginning of a midi message

                if data in realtimsg:   # send real time messages immediately
                    if self.realtime:   # if they are wanted, otherwise just ignore
                        self.midicallback(mididev=self.uart, message=[data], time_stamp=None)
                    continue                # they may interleave, so don't touch current process

                if data == 0xF7:        # EndofSysEx
                    if self.sysex:      # They are allowed, so
                        bytenum = 1     # let standard procedure do its job.
                    else:               # SysEx should be ignored, so
                        message = []    # do so initialize all...
                        runningstatus = 0
                        runningbytes = 0
                        bytenum = 0
                        continue        # ...and wait for new stuff.

                else:

                    if len(message):    # Did we collect any stuff
                        # Just send as it can be undefined messages or plain errors, decision up to receiver
                        # For simplicity sake, SysEx without EndofSysEx is considered an error
                        self.midicallback(mididev=self.uart, message=message, time_stamp=None)
                        message = []        # Start a new message

                    if data in systemmsg:
                        bytenum = systemmsg[ data ][0]
                    else:
                        bytenum = messages[ data>>4 ][0]

                runningstatus = data
                runningbytes = bytenum

            elif (not bytenum) and runningstatus:  # Received data without preceding status
                    message = [runningstatus]      # use stored running status if available
                    bytenum = runningbytes-1       # and related bytes (mind we "received" one)

            message.append(data)
            bytenum -= 1
            if not bytenum:                # we're complete !
                self.midicallback(mididev=self.uart, message=message, time_stamp=None)
                message = []        # Start a new message

    def send_raw(self, *message):        # procedure name compliant with rtmidi API
        #param message example: Midi Message [144, 60, 100]
        if self.out:
            omsg = ""
            for i in message:
                omsg = "%s%s" %( omsg, chr(i) )
            try:
                self.ser.write( omsg.encode() )
            except:
                print ("Write time out on %s, closed as MIDI OUT" %self.uart)
                self.out = False

    def close_port(self):        # procedure name compliant with rtmidi API
        self.ser.close()

###############################################################
#   Midi via USB's using rtmidi with
#   Midi via serial hooked into that.
#   Main loop handling midi
###############################################################

def print_sensing(intf, ports):
    print ("MIDI %s:" %intf)
    for port in ports:
        if ('rtmidi' not in port.lower()
        and 'Midi Through' not in port):
            print ("  - %s" %port )

outports = {}
midiserial = IO(midicallback=MidiCallback, realtime=realtime, sysex=sysex)

midi_in = rtmidi2.MidiInMulti()
midi_in.callback = MidiCallback

print ( "\n..sensing MIDI ports except serial/UART (dealt with above)..")
print_sensing ( "in", rtmidi2.get_in_ports() )
print_sensing ( "out", rtmidi2.get_out_ports() )

thru_ports = set(thru_ports)

if (len(thru_ports) > 0):
    i=1
    allvalid = "All" in thru_ports

    if midiserial.out:
        if "EMBEDDED" in thru_ports:
            outports["EMBEDDED"] = [midiserial.uart, midiserial]
        elif allvalid:
            outports[midiserial.uart] = [midiserial.uart, midiserial]
        else:
            for v in thru_ports:
                if re.search ( v, midiserial.uart):
                    outports[midiserial.uart] = [midiserial.uart, midiserial]
                    break

    #if use_midiserial:
    #    if allvalid:
    #for port in thru_ports:

    for port in rtmidi2.get_out_ports():
        if ('Midi Through' not in port
        and 'rtmidi' not in port.lower()):
            valid = allvalid
            for v in thru_ports:
                if valid:
                    break
                valid = re.search( v, port )
                # Examples showing it's use:
                #  "MIDI_THRU = ^MIDI4x4.*3$" matches "MIDI4x4 28:3"
                #   which is helpful as device number (28 here) may vary
                #  For all MIDI4x4 output ports: "MIDI_THRU = ^MIDI4x4.*"
            if valid:
                outport = "MIDI_OUT_%d" %i
                outports[outport] = [port, None]
                try:
                    outports[outport][1] = rtmidi2.MidiOut()
                    outports[outport][1].open_port(port)
                    print ('Opened "%s" as %s ' % (port,outport) )
                    i += 1
                except:
                    print ('No active device on "%s"' % (port) )
                    del outports[outport]

curr_inports = []
prev_inports = []
try:
  while True:
        curr_inports = rtmidi2.get_in_ports()
        if ( len(prev_inports) != len(curr_inports) ):
                midi_in.close_ports()
                prev_ports = []
                i=0
                for port in curr_inports:
                        if ('Midi Through' not in port
                            and 'rtmidi' not in port.lower()):
                                #print 'Open "%s" as MIDI IN %d ' % (port.split(":",1)[1].strip(),i)
                                print ('Open "%s" as MIDI_IN_%d ' % (port,i) )
                                midi_in.open_ports(port)
                        i+=1
                curr_inports = rtmidi2.get_in_ports()   # we do this indirect to catch
                prev_inports = curr_inports             #    auto opened virtual ports
        time.sleep(2)
except KeyboardInterrupt:
        print ("\nstopped by user via ctrl-c\n")
except:
        print ("\nstopped by unexpected error")
finally:
        for outport in outports:
            outports[outport][1].close_port()
        midi_in.close_ports()
