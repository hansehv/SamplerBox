###############################################################
#   HTTP-GUI for controlling the box with phone, tablet or PC
#   It's a minimal webserver, together with javascripts+css
#   giving buildingblocks for html based GUI.
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
###############################################################
import threading
import http.server,urllib.request,urllib.parse,urllib.error,mimetypes
from urllib.parse import urlparse,parse_qs
import os,shutil,subprocess,re
import UI
HTTP_PORT=80
HTTP_ROOT="webgui"
left=""

v6msg=""
if UI.USE_IPv6:
    try:
        import socket,socketserver
        socketserver.TCPServer.address_family=socket.AF_INET6
        v6msg=" with IPv6 support"
        left="::"
    except ImportError:
        print('please find other ways to listen on ipv6 address!')

class HTTPRequestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        path = urlparse(urllib.parse.unquote(self.path)).path
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
        length = int(self.headers.get('content-length'))
        field_data = self.rfile.read(length)
        fields=parse_qs(field_data.decode())
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
        if "SB_Voice" in fields:
            if ( UI.Voice(int(fields["SB_Voice"][0])) ):
                self.do_GET()   # answer the browser
                return
        if "SB_FXpreset" in fields:
            if ( UI.FXpreset(int(fields["SB_FXpreset"][0])) != "None" ):
                self.do_GET()   # answer the browser
                return
        mapchange=False
        if "SB_Notemap" in fields and not mapchange:
            mapchange=UI.Notemap(int(fields["SB_Notemap"][0]))
        if not (mapchange):
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
        if isinstance(parm,(int,float)):
            jsparm="%i" %int(parm+.1)
        elif isinstance(parm,str):
            if nam=="DefinitionTxt":
                jsparm="'%s'" %parm.replace('\n','&#10;').replace('\r','&#13;')
            else:
                jsparm="'%s'" %parm
        else:
            jsparm="%s" %parm
        return jsparm

    def wfilewrite(self, txt):
        self.wfile.write(txt.encode())

    def write_heading(self, txt):
        hr="\n// %s\n" %''.join([char*(len(txt)+3) for char in '-'])
        self.wfilewrite("\n%s" %hr)
        self.wfilewrite("// %s  :" %txt)
        self.wfilewrite("%s" %hr)

    def send_API(self):
        self.send_response(200)
        self.send_header("Content-type", 'application/javascript')
        self.send_header("Cache-Control", 'no-cache, must-revalidate')
        self.end_headers()

        self.wfilewrite("// SamplerBox API, interface for interacting via standard HTTP")

        self.write_heading("Variables that can be updated and submitted to samplerbox")
        i=0
        for n in UI.procs:
            m=UI.procs[n]
            if m[0]=="w":
                if (i%5)==0: self.wfilewrite("\n")
                self.wfilewrite("var %s;" %("SB_%s" %n) )
                i+=1

        self.write_heading("Informational (read-only) variables")
        self.wfilewrite("\nvar SB_busy;SB_numvars=%d;var SB_VarVal;SB_VarName=[" %i)
        i=""
        for n in UI.procs:
            m=UI.procs[n]
            if m[0]=="w":
                self.wfilewrite("%s'%s'" %(i,"SB_%s" %n) )
                i=","
        self.wfilewrite("];")
        i=0
        for n in UI.procs:
            m=UI.procs[n]
            if m[0]=="v":
                if (i%5)==0: self.wfilewrite("\n")
                self.wfilewrite("var %s;" %("SB_%s" %n) )
                i+=1

        self.write_heading("Static variables & tables")
        for n in UI.procs:
            m=UI.procs[n]
            if m[0]=="f":
                self.wfilewrite("\n%s=%s;" %("SB_%s" %n,self.get_UI_parm(n,m[1])))

        self.write_heading("Function for (re)filling all above variables with actual values from SamplerBox")
        self.wfilewrite("\nfunction SB_GetAPI() {")
        UI.nm_sync()
        self.wfilewrite("\n\tSB_busy=%i;SB_nm_onote=%s;\n\tSB_VarVal=[" %(UI.RenewMedia(),self.get_UI_parm("nm_onote",UI.procs["nm_onote"][1])) )
        i=""
        for n in UI.procs:
            m=UI.procs[n]
            if m[0]=="w":
                self.wfilewrite("%s%s" %(i,self.get_UI_parm(n,m[1])))
                i=","
        self.wfilewrite("];")

        for n in UI.procs:
            m=UI.procs[n]
            if m[0]=="v":
                self.wfilewrite("\n\t%s=%s;" %("SB_%s" %n,self.get_UI_parm(n,m[1])))
        self.wfilewrite("\n};")

def HTTP_Server(server_class=http.server.HTTPServer, handler_class=HTTPRequestHandler, port=HTTP_PORT):
    server_address = (left, port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd on port %d%s' % (port,v6msg))
    try:
        httpd.serve_forever()
    except:
        print('Starting httpd failed')

HTTPThread = threading.Thread(target = HTTP_Server)
HTTPThread.daemon = True
HTTPThread.start()
