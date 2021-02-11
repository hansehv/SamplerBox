###############################################################
#   HTTP-GUI for controlling the box with phone, tablet or PC
#   It's a minimal webserver, together with javascripts+css
#   giving buildingblocks for html based GUI.
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
import threading
import BaseHTTPServer,urllib, mimetypes
from urlparse import urlparse,parse_qs
import os,shutil,subprocess,re
import UI
HTTP_PORT=80
HTTP_ROOT="webgui"

v6msg=""
if UI.USE_IPv6:
    # python 2:support ipv6
    try:
        import socket,SocketServer
        SocketServer.TCPServer.address_family=socket.AF_INET6
        v6msg=" with IPv6 support"
    except ImportError:
        print('please find other ways to listen on ipv6 address!')

class HTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        path = urlparse(urllib.unquote(self.path)).path
        if path=="/SamplerBox.API":
            self.send_API()
        else:
            if len(path)<2:
                path=HTTP_ROOT + "/index.html"
            elif UI.Samplesdir()[1:] != '/':
                path=HTTP_ROOT + path
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
        
    def set_UI_parm(self,nam,val):
        parm=UI.procs[nam][1]()     # check procedure type, not all types are covered as they are not used yet.
        if isinstance(parm,int):
            try:    # this "try" is to facilitate booleans (standard int) to be entered as text processed in catch-all
                UI.procs[nam][1](int(val))
                return
            except:
                pass
        elif isinstance(parm,float):
            UI.procs[nam][1](float(val))
            return
        UI.procs[nam][1](val)    # catch-all for the strings, arrays and dicts

    def do_POST(self):
        length = int(self.headers.getheader('content-length'))
        field_data = self.rfile.read(length)
        fields=parse_qs(field_data)
        display=True
        #----------------------------------------------#
        # Process fields with special logic first      #
        #----------------------------------------------#
        if "SB_RenewMedia" in fields:
            if UI.RenewMedia(fields["SB_RenewMedia"]):
                self.do_GET()   # answer the browser
                return
        if "SB_Preset" in fields:
            loading=UI.Preset(UI.procs["Presetlist"][1]()[int(fields["SB_Preset"][0])][0])
            if loading:
                self.do_GET()   # answer the browser
                return
        if "SB_DefinitionTxt" in fields:
            loading=UI.DefinitionTxt(fields["SB_DefinitionTxt"][0])
            if loading:
                self.do_GET()   # answer the browser
                return
        voicechange=False
        if "SB_Voice" in fields: voicechange=UI.Voice(int(fields["SB_Voice"][0]))
        notemapchange=False
        if "SB_Notemap" in fields and not voicechange: UI.Notemap(int(fields["SB_Notemap"][0]))
        if not (voicechange or notemapchange):
            if "SB_nm_inote"  in fields:    # inote is used as a signal: remapping requires it and html page sends it regardless of it being changed
                if UI.nm_inote(int(fields["SB_nm_inote"][0])):   # so now we know something has changed on a screen containing remapping fields
                    if "SB_nm_Q" in fields: UI.nm_Q(int(fields["SB_nm_Q"][0]))    # needs to be before onote to get proper name2note translation
                    if "SB_nm_unote" in fields: UI.nm_unote(int(fields["SB_nm_unote"][0]))    # needs to be before onote, so onote can reset it
                    if "SB_nm_onote" in fields: UI.nm_onote(int(fields["SB_nm_onote"][0]))
                    if "SB_nm_retune" in fields: UI.nm_retune(int(fields["SB_nm_retune"][0]))
                    if "SB_nm_voice" in fields: UI.nm_voice(int(fields["SB_nm_voice"][0])-1)
                    UI.nm_consolidate()
        scalechange=False       # Scale takes precedence over Chord
        if "SB_Scale" in fields: scalechange=(UI.Scale()!=UI.Scale(int(fields["SB_Scale"][0])))
        if "SB_Chord" in fields and not scalechange: UI.Chord(int(fields["SB_Chord"][0]))
        if "SB_Button" in fields: display = not (UI.Button(fields["SB_Button"][0])) # if we had succesfull button, a display was shown already
        #----------------------------------------------#
        # Next process straightforward fields in bulk  #
        #----------------------------------------------#
        for n in fields:
            nam=n[3:]
            if nam not in ["RenewMedia","Preset","DefinitionTxt","Voice","Notemap","nm_inote","nm_Q","nm_onote","nm_retune","nm_voice","Scale","Chord","Button"]:    #"nm_map","nm_sav",
                self.set_UI_parm(nam,fields[n][0])

        if display: UI.display("") # show it on the box if not done already
        self.do_GET()       # as well as on the gui

    def get_UI_parm(self,nam,proc):
        parm=proc()
        if isinstance(parm,(int,long,float)):
            jsparm="%i" %int(parm+.1)
        elif isinstance(parm,basestring):
            if nam=="DefinitionTxt":
                jsparm="'%s'" %parm.replace('\n','&#10;').replace('\r','&#13;')
            else:
                jsparm="'%s'" %parm
        else:
            jsparm="%s" %parm
        return jsparm

    def write_heading(self, txt):
        hr="\n// %s\n" %''.join([char*(len(txt)+3) for char in '-'])
        self.wfile.write("\n%s" %hr)
        self.wfile.write("// %s  :" %txt)
        self.wfile.write("%s" %hr)
        
    def send_API(self):
        self.send_response(200)
        self.send_header("Content-type", 'application/javascript')
        self.send_header("Cache-Control", 'no-cache, must-revalidate')
        self.end_headers()

        self.wfile.write("// SamplerBox API, interface for interacting via standard HTTP")

        self.write_heading("Variables that can be updated and submitted to samplerbox")
        i=0
        for n in UI.procs:
            m=UI.procs[n]
            if m[0]=="w":
                if (i%5)==0: self.wfile.write("\n")
                self.wfile.write("var %s;" %("SB_%s" %n) )
                i+=1

        self.write_heading("Informational (read-only) variables")
        self.wfile.write("\nvar SB_busy;SB_numvars=%d;var SB_VarVal;SB_VarName=[" %i)
        i=""
        for n in UI.procs:
            m=UI.procs[n]
            if m[0]=="w":
                self.wfile.write("%s'%s'" %(i,"SB_%s" %n) )
                i=","
        self.wfile.write("];")
        i=0
        for n in UI.procs:
            m=UI.procs[n]
            if m[0]=="v":
                if (i%5)==0: self.wfile.write("\n")
                self.wfile.write("var %s;" %("SB_%s" %n) )
                i+=1

        self.write_heading("Static variables & tables")
        for n in UI.procs:
            m=UI.procs[n]
            if m[0]=="f":
                self.wfile.write("\n%s=%s;" %("SB_%s" %n,self.get_UI_parm(n,m[1])))

        self.write_heading("Function for (re)filling all above variables with actual values from SamplerBox")
        self.wfile.write("\nfunction SB_GetAPI() {")
        UI.nm_sync()
        self.wfile.write("\n\tSB_busy=%i;SB_nm_onote=%s;\n\tSB_VarVal=[" %(UI.RenewMedia(),self.get_UI_parm("nm_onote",UI.procs["nm_onote"][1])) )
        i=""
        for n in UI.procs:
            m=UI.procs[n]
            if m[0]=="w":
                self.wfile.write("%s%s" %(i,self.get_UI_parm(n,m[1])))
                i=","
        self.wfile.write("];")

        for n in UI.procs:
            m=UI.procs[n]
            if m[0]=="v":
                self.wfile.write("\n\t%s=%s;" %("SB_%s" %n,self.get_UI_parm(n,m[1])))
        self.wfile.write("\n};")

def HTTP_Server(server_class=BaseHTTPServer.HTTPServer, handler_class=HTTPRequestHandler, port=HTTP_PORT):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print 'Starting httpd on port %d%s' % (port,v6msg)
    try:
        httpd.serve_forever()
    except:
        print 'Starting httpd failed'

HTTPThread = threading.Thread(target = HTTP_Server)
HTTPThread.daemon = True
HTTPThread.start()
