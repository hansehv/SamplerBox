###############################################################
#   HTTP-GUI for controlling the box with phone, tablet or PC
#   minimal webserver together with javascripts+css
#   giving buildingblocks for GUI
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
import threading
import BaseHTTPServer,urllib, mimetypes
from urlparse import urlparse,parse_qs
import os,shutil,subprocess
import gv,arp,LFO,Cpp
notesymbol=["C","C&#9839;","D","E&#9837;","E","F","F&#9839;","G","G&#9839;","A","B&#9837;","B","FX"]  # 0 in scalechord table, also used in loadsamples(!)
HTTP_PORT = 80

class HTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        path = urlparse(urllib.unquote(self.path)).path
        if path=="/SamplerBox.API":
            self.send_API()
        else:
            if len(path)<2:
                path=gv.HTTP_ROOT + "/index.html"
            elif path[len(gv.samplesdir):] != gv.samplesdir:
                path=gv.HTTP_ROOT + path
            elif gv.samplesdir[1:] != '/':
                path=gv.HTTP_ROOT + path
            # and otherwise it's an absolute path (so it's ok as is)
            try:
                #print "open %s binary" % (path)
                f = open(path, 'rb')
            except IOError:
                self.send_error(404, '"%s" does not exist' % (path))
                return None
            self.send_response(200)
            self.send_header("Cache-Control", "max-age=50400")  # 14 hours (ss*mm*hh*dd)
            mime_type = mimetypes.guess_type(path)
            self.send_header("Content-type", "%s" % (mime_type[0]) )
            fs = os.fstat(f.fileno())
            self.send_header("Content-Length", str(fs[6]))
            self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
            self.end_headers()
            shutil.copyfileobj(f, self.wfile)
            f.close()
        
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
    def do_POST(self):
        inval=0
        
        length = int(self.headers.getheader('content-length'))
        field_data = self.rfile.read(length)
        fields=parse_qs(field_data)
        #print fields
        if "SB_RenewMedia" in fields:
            if fields["SB_RenewMedia"][0] == "Yes":
                gv.basename="None"
                self.LoadSamples()
                return
        if "SB_Preset" in fields:
            inval=gv.presetlist[int(fields["SB_Preset"][0])][0]
            if gv.PRESET!=inval:
                gv.PRESET=inval;
                self.LoadSamples()
                return
        if "SB_DefinitionTxt" in fields:
            if gv.DefinitionTxt != fields["SB_DefinitionTxt"][0]:
                gv.DefinitionTxt = fields["SB_DefinitionTxt"][0]
                #print gv.DefinitionTxt
                subprocess.call(['mount', '-vo', 'remount,rw', gv.samplesdir])
                fname=gv.samplesdir+gv.presetlist[gv.getindex(gv.PRESET,gv.presetlist)][1]+"/"+gv.SAMPLESDEF
                with open(fname, 'w') as definitionfile:
                        definitionfile.write(gv.DefinitionTxt)
                subprocess.call(['mount', '-vo', 'remount,ro', gv.samplesdir])
                gv.basename="None"         # do a renew to sync the update
                self.LoadSamples()
                return
        if "SB_MidiChannel" in fields: gv.MIDI_CHANNEL      =int(fields["SB_MidiChannel"][0])
        if "SB_SoundVolume" in fields: gv.setvolume(int(fields["SB_SoundVolume"][0]))
        if "SB_MidiVolume"  in fields: gv.volumeCC          =float(fields["SB_MidiVolume"][0])/100
        if "SB_Gain"        in fields: gv.globalgain        =float(fields["SB_Gain"][0])/100
        if "SB_Pitchrange"  in fields: gv.pitchnotes        =int(fields["SB_Pitchrange"][0])*2
        if "SB_Voice"       in fields:
            if gv.voicelist[0][0]==0:   i=1
            else:   i=0
            gv.MC[gv.getindex(gv.VOICES,gv.MC)][2](int(fields["SB_Voice"][0])+i,0)
        if "SB_Notemap"     in fields:gv.MC[gv.getindex(gv.NOTEMAPS,gv.MC)][2](int(fields["SB_Notemap"][0]))
        if "SB_Scale"       in fields:
            inval=int(fields["SB_Scale"][0])
            if gv.currscale==inval: scalechange=False
            else:
                scalechange=True
                gv.currscale=inval
                if gv.last_musicnote<0: gv.currchord=0
                else: gv.currchord=gv.scalechord[gv.currscale][gv.last_musicnote]
        if "SB_Chord"       in fields and not scalechange:
            inval=int(fields["SB_Chord"][0])
            if not gv.currchord==inval:
                gv.currchord=inval
                gv.currscale=0
        if "SB_CHOrus"      in fields: gv.CHOsetType(gv.getindex(fields["SB_CHOrus"][0],["Off","On"],True))
        if "SB_CHOdepth"    in fields: gv.CHOsetdepth((float(fields["SB_CHOdepth"][0])-2)*9.77)
        if "SB_CHOgain"     in fields: gv.CHOsetgain((float(fields["SB_CHOgain"][0])-30)*2.54)
        if "SB_FVtype"      in fields: Cpp.FVsetType(gv.getindex(fields["SB_FVtype"][0],["Off","On"],True))
        if "SB_FVroomsize"  in fields: Cpp.FVsetroomsize(float(fields["SB_FVroomsize"][0])*1.27)
        if "SB_FVdamp"      in fields: Cpp.FVsetdamp(float(fields["SB_FVdamp"][0])*1.27)
        if "SB_FVlevel"     in fields: Cpp.FVsetlevel(float(fields["SB_FVlevel"][0])*1.27)
        if "SB_FVwidth"     in fields: Cpp.FVsetwidth(float(fields["SB_FVwidth"][0])*1.27)
        if "SB_AWtype"      in fields: Cpp.AWsetType(gv.getindex(fields["SB_AWtype"][0],gv.AWtypes,True))
        if "SB_AWmixing"    in fields: Cpp.AWsetMixing(float(fields["SB_AWmixing"][0])*1.27)
        if "SB_AWattack"    in fields: Cpp.AWsetAttack(float(fields["SB_AWattack"][0])*0.254)
        if "SB_AWrelease"   in fields: Cpp.AWsetRelease(float(fields["SB_AWrelease"][0])*0.254)
        if "SB_AWminfreq"   in fields: Cpp.AWsetMinFreq(float(fields["SB_AWminfreq"][0])*0.254)
        if "SB_AWmaxfreq"   in fields: Cpp.AWsetMaxFreq(float(fields["SB_AWmaxfreq"][0])*0.0127)
        if "SB_AWqfactor"   in fields: Cpp.AWsetQualityFactor(float(fields["SB_AWqfactor"][0])*0.0508)
        if "SB_AWspeed"     in fields: Cpp.AWsetSpeed((float(fields["SB_AWspeed"][0])-100)*0.127)
        if "SB_AWlvlrange"  in fields: Cpp.AWsetLVLrange(float(fields["SB_AWlvlrange"][0])*1.27)
        if "SB_DLYtype"     in fields: Cpp.DLYsetType(gv.getindex(fields["SB_DLYtype"][0],gv.DLYtypes,True))
        if "SB_DLYfb"       in fields: Cpp.DLYsetfb(float(fields["SB_DLYfb"][0])*1.27)
        if "SB_DLYwet"      in fields: Cpp.DLYsetwet(float(fields["SB_DLYwet"][0])*1.27)
        if "SB_DLYdry"      in fields: Cpp.DLYsetdry(float(fields["SB_DLYdry"][0])*1.27)
        if "SB_DLYtime"     in fields: Cpp.DLYsettime((float(fields["SB_DLYtime"][0])-1000)/600*1.27)
        if "SB_DLYsteep"    in fields: Cpp.DLYsetsteep((float(fields["SB_DLYsteep"][0])-1)*12.7)
        if "SB_DLYsteplen"  in fields: Cpp.DLYsetsteplen((float(fields["SB_DLYsteplen"][0])-300)/30*1.27)
        if "SB_DLYmin"      in fields: Cpp.DLYsetmin((float(fields["SB_DLYmin"][0])-5)*5.36)
        if "SB_DLYmax"      in fields: Cpp.DLYsetmax((float(fields["SB_DLYmax"][0])-50)*1.27)
        if "SB_LFtype"      in fields: Cpp.LFsetType(gv.getindex(fields["SB_LFtype"][0],["Off","On"],True))
        if "SB_LFresonance" in fields: Cpp.LFsetResonance(float(fields["SB_LFresonance"][0])/38*127)
        if "SB_LFcutoff"    in fields: Cpp.LFsetCutoff((float(fields["SB_LFcutoff"][0])-1000)/100*1.27)
        if "SB_LFdrive"     in fields: Cpp.LFsetDrive((float(fields["SB_LFdrive"][0])-1)*6.35) # =/20.0*127)
        if "SB_LFlvl"       in fields: Cpp.LFsetLvl((float(fields["SB_LFlvl"][0]))*1.27)
        if "SB_LFgain"      in fields: Cpp.LFsetGain((float(fields["SB_LFgain"][0])-10)*1.27)
        if "SB_LFOtype"     in fields: LFO.setType(gv.getindex(fields["SB_LFOtype"][0],gv.LFOtypes,True))
        if "SB_VIBRpitch"   in fields: gv.VIBRpitch=float(fields["SB_VIBRpitch"][0])/16
        if "SB_VIBRspeed"   in fields: LFO.VibrSetspeed(int(fields["SB_VIBRspeed"][0])*4)
        if "SB_VIBRtrill"   in fields:
            if fields["SB_VIBRtrill"][0].title()=="On":gv.VIBRtrill=True
            else: gv.VIBRtrill=False
        if "SB_TREMampl"    in fields: gv.TREMampl=float(fields["SB_TREMampl"][0])/100
        if "SB_TREMspeed"   in fields: LFO.TremSetspeed(int(fields["SB_TREMspeed"][0])*4)
        if "SB_TREMtrill"   in fields:
            if fields["SB_TREMtrill"][0].title()=="On":gv.TREMtrill=True
            else: gv.TREMtrill=False
        if "SB_PANwidth"    in fields: gv.PANwidth=float(fields["SB_PANwidth"][0])/20
        if "SB_PANspeed"    in fields: LFO.PanSetspeed(int(fields["SB_PANspeed"][0])*4)
        if "SB_ARPord"      in fields: arp.ordnum(gv.getindex(fields["SB_ARPord"][0],gv.ARPtypes,True))
        if "SB_ARPstep"     in fields: arp.tempo(int(fields["SB_ARPstep"][0])*1.27)
        if "SB_ARPsustain"  in fields: arp.sustain(int(fields["SB_ARPsustain"][0])*1.27)
        if "SB_ARPloop"     in fields:
            if fields["SB_ARPloop"][0].title()=="On":arp.loop=True
            else: arp.loop=False
        if "SB_ARP2end"     in fields:
            if fields["SB_ARP2end"][0].title()=="On":arp.play2end=True
            else: arp.play2end=False
        if "SB_ARPfade"     in fields: arp.fadeout(1.27*int(fields["SB_ARPfade"][0]))
        gv.display("") # show it on the box
        self.do_GET()       # as well as on the gui

    def LoadSamples(self):
        gv.ActuallyLoading=True     # safety first, as these processes run in parallel
        gv.LoadSamples()            # perform the loading
        self.do_GET()               # answer the browser

    def send_API(self):
        varName=["SB_RenewMedia","SB_SoundVolume","SB_MidiVolume",
                 "SB_Preset","SB_Gain","SB_Pitchrange","SB_Notemap",
                 "SB_Voice","SB_Scale","SB_Chord",
                 "SB_FVtype","SB_FVroomsize","SB_FVdamp","SB_FVlevel","SB_FVwidth",
                 "SB_AWtype","SB_AWmixing","SB_AWattack","SB_AWrelease","SB_AWminfreq",
                 "SB_AWmaxfreq","SB_AWqfactor","SB_AWspeed","SB_AWlvlrange",
                 "SB_DLYtype","SB_DLYfb","SB_DLYwet","SB_DLYdry","SB_DLYtime",
                 "SB_DLYsteep","SB_DLYsteplen","SB_DLYmin","SB_DLYmax",
                 "SB_LFtype","SB_LFresonance","SB_LFcutoff","SB_LFdrive","SB_LFlvl","SB_LFgain",
                 "SB_LFOtype","SB_VIBRpitch","SB_VIBRspeed","SB_VIBRtrill",
                 "SB_TREMampl","SB_TREMspeed","SB_TREMtrill","SB_PANwidth","SB_PANspeed",
                 "SB_ARPstep","SB_ARPsustain","SB_ARPloop",
                 "SB_ARP2end","SB_ARPord","SB_ARPfade",
                 "SB_CHOrus","SB_CHOdepth","SB_CHOgain",
                 "SB_MidiChannel","SB_DefinitionTxt"]
        
        self.send_response(200)
        self.send_header("Content-type", 'application/javascript')
        self.send_header("Cache-Control", 'no-cache, must-revalidate')
        self.end_headers()
        self.wfile.write("// SamplerBox API, interface for interacting via standard HTTP\n\n")
        self.wfile.write("// Variables that can be updated and submitted to samplerbox:")
        for i in range(len(varName)):
            if (i%5)==0: self.wfile.write("\n")
            self.wfile.write("var %s;" % (varName[i]) )

        self.wfile.write("\n\n// Informational (read-only) variables:")
        self.wfile.write("\nSB_numvars=%d;var SB_VarName;var SB_VarVal;" % (len(varName)) )
        self.wfile.write("\nvar SB_Samplesdir;var SB_LastMidiNote;var SB_LastMusicNote;var SB_DefErr;")
        self.wfile.write("\nvar SB_Mode;var SB_numpresets;var SB_Presetlist;")
        self.wfile.write("\nvar SB_xvoice;var SB_numvoices;var SB_Voicelist;")
        self.wfile.write("\nvar SB_numbtracks;var SB_bTracks;var SB_numnotemaps;var SB_Notemaps;")

        self.wfile.write("\n\n// Static tables:")
        self.wfile.write("\nSB_numnotes=%d;SB_Notename=%s;" % (len(notesymbol),notesymbol) )
        self.wfile.write("\nSB_numchords=%d;SB_Chordname=%s;\nSB_Chordnote=%s;" % (len(gv.chordname),gv.chordname,gv.chordnote) )
        self.wfile.write("\nSB_numscales=%d;SB_Scalename=%s;\nSB_Scalechord=%s;" % (len(gv.scalesymbol),gv.scalesymbol,gv.scalechord) )
        self.wfile.write("\nSB_ARPordlist=%s;" % (gv.ARPtypes) )
        self.wfile.write("\nSB_DLYtypes=%s;" % (gv.DLYtypes) )
        self.wfile.write("\nSB_AWtypes=%s;" % (gv.AWtypes) )
        self.wfile.write("\nSB_LFOtypes=%s;" % (gv.LFOtypes) )

        self.wfile.write("\n\n// Function for (re)filling all above variables with actual values from SamplerBox:\nfunction SB_GetAPI() {")
        self.wfile.write("\n\tSB_VarName=['%s'" % (varName[0]) )
        for i in range(1,len(varName)):
            self.wfile.write(",'%s'" % (varName[i]) )
        self.wfile.write("];\n\tSB_VarVal=[")
        if gv.ActuallyLoading:  ActuallyLoading="Yes"
        else:                   ActuallyLoading="No"
        self.wfile.write("'%s',%d,%d," % (ActuallyLoading,gv.volume,gv.volumeCC*100) )
        self.wfile.write("%d,%d,%d,'%s'," % (gv.PRESET,gv.globalgain*100,gv.pitchnotes/2,gv.currnotemap) )
        self.wfile.write("%d,%d,%d," % (gv.currvoice,gv.currscale,gv.currchord) )
        self.wfile.write("%d,%d,%d,%d,%d," % (gv.FVtype,gv.FVroomsize*100,gv.FVdamp*100,gv.FVlevel*100,gv.FVwidth*100) )
        self.wfile.write("%d,%d,%d,%d," % (gv.AWtype,gv.AWmixing*100,gv.AWattack*1000,gv.AWrelease*10000) )
        self.wfile.write("%d,%d,%d,%d,%d," % (gv.AWminfreq,gv.AWmaxfreq,gv.AWqfactor*100,gv.AWspeed,gv.AWlvlrange) )
        self.wfile.write("%d,%d,%d,%d,%d," % (gv.DLYtype,gv.DLYfb*100,gv.DLYwet*100,gv.DLYdry*100,gv.DLYtime) )
        self.wfile.write("%d,%d,%d,%d," % (gv.DLYsteep,gv.DLYsteplen,gv.DLYmin,gv.DLYmax) )
        self.wfile.write("%d,%d,%d,%d,%d,%d," % (gv.LFtype,gv.LFresonance*10,gv.LFcutoff,gv.LFdrive,gv.LFlvl*100,gv.LFgain*10) )
        if gv.VIBRtrill:s=1
        else:           s=0
        self.wfile.write("%d,%d,%d,'%s'," % (gv.LFOtype,gv.VIBRpitch*16,gv.VIBRspeed,s) )
        if gv.TREMtrill:s=1
        else:           s=0
        self.wfile.write("%d,%d,'%s',%d,%d," % (gv.TREMampl*100,gv.TREMspeed,s,gv.PANwidth*20,gv.PANspeed) )
        if arp.loop:    s=1
        else:           s=0
        if arp.play2end:t=1
        else:           t=0
        self.wfile.write("%d,%d,'%s','%s',%d,%d," % (arp.length,arp.keepon,s,t,gv.ARPtype,arp.fadecycles) )
        self.wfile.write("%d,%d,%d,%d,'%s'" % (gv.CHOrus,gv.CHOdepth,gv.CHOgain*100,gv.MIDI_CHANNEL,gv.DefinitionTxt.replace('\n','&#10;').replace('\r','&#13;')) )   # make it a unix formatted JS acceptable string
        self.wfile.write("];\n\tSB_Samplesdir='%s';SB_LastMidiNote=%d;SB_LastMusicNote=%s;SB_DefErr='%s';\n" % (gv.samplesdir,gv.last_midinote,gv.last_musicnote,gv.DefinitionErr) )
        self.wfile.write("\tSB_Mode='%s';SB_numpresets=%d;SB_Presetlist=%s;\n" % (gv.sample_mode,len(gv.presetlist),gv.presetlist) )
        vlist=[]
        xvoice="No"
        for i in range(len(gv.voicelist)):      # filter out effects track
            if gv.voicelist[i][0]==0:  xvoice="Yes"
            else:   vlist.append(gv.voicelist[i])
        self.wfile.write("\tSB_numvoices=%d;SB_xvoice='%s';SB_Voicelist=%s;\n" % (len(vlist),xvoice,vlist) )
        self.wfile.write("\tSB_numbtracks=%d;SB_bTracks=%s;\n" % (len(gv.btracklist),gv.btracklist) )
        notemaps=["None"]
        notemaps.extend(gv.notemaps)
        self.wfile.write("\tSB_numnotemaps=%d;SB_Notemaps=%s;\n" % (len(notemaps),notemaps) )
        self.wfile.write("};")

def HTTP_Server(server_class=BaseHTTPServer.HTTPServer, handler_class=HTTPRequestHandler, port=HTTP_PORT):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print 'Starting httpd on port %d' % (port)
    try:
        httpd.serve_forever()
    except:
        print 'Starting httpd failed'

HTTPThread = threading.Thread(target = HTTP_Server)
HTTPThread.daemon = True
HTTPThread.start()
