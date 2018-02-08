function SB_Update(){
	SB_GetAPI();
	if (SB_VarVal[0]=='Yes') {		// this is in fact SB_RenewMedia
		setTimeout(SB_Refresh, 1000);
		return;
	}
	for (var i=0;i<SB_numvars;i++){
		name=SB_varName[i];val=SB_VarVal[i];
		v_name="v_"+name;
		SB_variables[v_name](val);
		ID_name="ID_"+name;
		if (document.getElementById(ID_name)) {
			document.getElementById(ID_name).className += " value";
			document.getElementById(ID_name).innerHTML=val;
			//document.getElementById(ID_name).innerHTML=document.getElementById(ID_name).textContent+'<SPAN CLASS="value">'+val+'</SPAN>';
		}
		input_name="input_"+name;
		if (document.getElementById(input_name)) {
			document.getElementById(input_name).innerHTML='<span class="inline valign_middle">'+SB_input[input_name](input_name,name,val, document.getElementById(input_name).textContent)+'</span>';
		}
	}
	for (i=0;i<SB_numelems;i++){
		name=SB_ElemID[i];
		if (document.getElementById(name)){
			text=document.getElementById(name).textContent;
			SB_element[name](name,text);
		}
	}
}
var SB_variables={
	v_SB_MidiChannel: function(val){SB_MidiChannel=val;},
	v_SB_SoundVolume: function(val){SB_SoundVolume=val;},
	v_SB_MidiVolume: function(val){SB_MidiVolume=val;},
	v_SB_Preset: function(val){SB_Preset=val;},
	v_SB_Gain: function(val){SB_Gain=val;},
	v_SB_Transpose: function(val){SB_Transpose=val;},
	v_SB_Voice: function(val){SB_Voice=val;},
	v_SB_Scale: function(val){SB_Scale=val;},
	v_SB_Chord: function(val){SB_Chord=val;},
	v_SB_Filter: function(val){SB_Filter=val;},
	v_SB_FVroomsize: function(val){SB_FVroomsize=val;},
	v_SB_FVdamp: function(val){SB_FVdamp=val;},
	v_SB_FVwet: function(val){SB_FVwet=val;},
	v_SB_FVdry: function(val){SB_FVdry=val;},
	v_SB_FVwidth: function(val){SB_FVwidth=val;},
	v_SB_RenewMedia: function(val){SB_RenewMedia=val;},
	v_SB_DefinitionTxt: function(val){SB_DefinitionTxt=val;}
}
var SB_input={
	input_SB_MidiChannel: function(input_name,name,val,text){
		return(text+SB_numselect(input_name,name,val,1,16,1));
	},
	input_SB_Transpose: function(input_name,name,val,text){
		return(text+SB_numselect(input_name,name,val,-12,12,1));
	},
	input_SB_Chord: function(input_name,name,val,text){
		return(text+SB_listselect(input_name,name,val,SB_Chordname,1,SB_numchords));
	},
	input_SB_Scale: function(input_name,name,val,text){
		return(text+SB_listselect(input_name,name,val,SB_Scalename,1,SB_numscales));
	},
	input_SB_Preset: function(input_name,name,val,text){
		if (SB_numvoices==0&&SB_xvoice=='No') m=" Empty!" ;else m="";
		return(text+SB_listselect(input_name,name,val,SB_Presetlist,2,SB_numpresets)+m);
	},
	input_SB_Voice: function(input_name,name,val,text){
		return(text+SB_listselect(input_name,name,val,SB_Voicelist,2,SB_numvoices));
	},
	input_SB_SoundVolume: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1));
	},
	input_SB_MidiVolume: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1));
	},
	input_SB_Gain: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,300,5)+SB_numselect(input_name,name,val,0,300,5));
	},
	input_SB_Filter: function(input_name,name,val,text){
		return(text+SB_listselect(input_name,name,val,SB_filters,1,SB_numfilters));
	},
	input_SB_FVroomsize: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1));
	},
	input_SB_FVdamp: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1));
	},
	input_SB_FVwet: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1));
	},
	input_SB_FVdry: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1));
	},
	input_SB_FVwidth: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1));
	},
	input_SB_RenewMedia: function(input_name,name,val,text){
		return('<LABEL><INPUT type="checkbox" name="'+name+'" class="hidden" value="Yes" onclick="SB_Submit();"><span class="button">'+text+'</span></LABEL>');
	},
	input_SB_DefinitionTxt: function(input_name,name,val,text){
		if (SB_Samplesdir.charAt(0)=='/') m='';else m=' readonly';
		return('<DIV STYLE="line-height:100%;text-align:center">'+text+m+'</DIV><TEXTAREA name="'+name+'"'+m+'>'+val+'</TEXTAREA>');
	}
}
SB_ElemID=["elem_SB_Form","elem_SB_Samplesdir","elem_SB_xvoice","elem_SB_DefErr","elem_SB_LastMidiNote","elem_SB_LastMusicNote","elem_SB_Scale","elem_SB_Chord","elem_SB_Chords","elem_SB_Scales"];
SB_numelems=SB_ElemID.length;
var SB_element={
	elem_SB_Form: function(elem_name){
		document.getElementById(elem_name).action = window.location.pathname;
		document.getElementById(elem_name).method = 'POST';
		document.getElementById(name).onsubmit = "return SB_Validate();";
		document.getElementById(elem_name).type = 'SUBMIT';
	},
	elem_SB_Samplesdir: function(elem_name){
		document.getElementById(elem_name).innerHTML=text+'<SPAN CLASS="value">'+SB_Samplesdir+'</SPAN>';
	},
	elem_SB_xvoice: function(elem_name,text) {
		if (SB_xvoice=="No") j="";else j=' checked="checked"';
		document.getElementById(elem_name).innerHTML=text+'<label class="inline alignx"><INPUT type="checkbox" onclick="return false;"'+j+';"></label>';
	},
	elem_SB_DefErr: function(elem_name,text) {
		if (SB_DefErr=="") document.getElementById(elem_name).innerHTML=''
		else document.getElementById(elem_name).innerHTML='<DIV STYLE="line-height:100%;">'+text+SB_DefErr+'</DIV>';
	},
	elem_SB_LastMidiNote: function(elem_name){
		if (SB_LastMidiNote<0) {m="None";} else {m=SB_LastMidiNote;}
		document.getElementById(elem_name).innerHTML=text+'<SPAN CLASS="value">'+m+'</SPAN>';
	},
	elem_SB_LastMusicNote: function(elem_name){
		if (SB_LastMusicNote<0) {m="None";} else {m=SB_Notename[SB_LastMusicNote];}
		document.getElementById(elem_name).innerHTML=text+'<SPAN CLASS="value">'+m+'</SPAN>';
	},
	elem_SB_Scale: function(elem_name){
		document.getElementById(elem_name).innerHTML=text+'<SPAN CLASS="value">'+SB_Scalename[SB_Scale]+'</SPAN>';
	},
	elem_SB_Chord: function(elem_name){
		document.getElementById(elem_name).innerHTML=text+'<SPAN CLASS="value">'+SB_Chordname[SB_Chord]+'</SPAN>';
	},
	elem_SB_Chords: function(elem_name){
		html='<TABLE BORDER="1"><TR><TH>Chord</TH><TH>CCval</TH><TH>Notes for C</TH></TR>';
		for (i=1;i<SB_numchords;i++){
			ccnum=i+SB_Chordoffset;
			html=html+'<TR VALIGN="top"><TD>'+SB_Chordname[i]+'</TD><TD>'+ccnum+'</TD><TD>';
			filler="";
			for (j=0;j<SB_Chordnote[i].length;j++){
				html=html+filler+SB_Notename[SB_Chordnote[i][j]];
				filler=", ";
			}
			html=html+'</TD></TR>';
		}
		document.getElementById(elem_name).innerHTML=html+'</TABLE>';
	},
	elem_SB_Scales: function(elem_name){
		html='<TABLE BORDER="1"><TR><TH>Scale</TH><TH>CCval</TH><TH>Implemented Chords</TH></TR>';
		for (i=1;i<SB_numscales;i++){
			ccnum=i+SB_Scaleoffset;
			html=html+'<TR VALIGN="top"><TD>'+SB_Scalename[i]+'</TD><TD>'+ccnum+'</TD><TD>';
			filler="";
			for (j=0;j<SB_Scalechord[i].length;j++){
				if (SB_Scalechord[i][j]>0){
					html=html+filler+SB_notechord(j,SB_Scalechord[i][j]);
					filler=", ";
				}
			}
			html=html+'</TD></TR>';
		}
		document.getElementById(elem_name).innerHTML=html+'</TABLE>';
	}
}
function SB_notechord(note,chord){
	if (SB_Chordname[chord]=="Maj") c="";
	else c="_"+SB_Chordname[chord].toLowerCase();
	return(SB_Notename[note]+c);
}
function SB_slider(input_name,name,val,min,max,step){
	return('<INPUT ID="'+input_name+'_r" name="'+name+'" TYPE="range" VALUE="'+val+'" min="'+min+'" max="'+max+'" step="'+step+'" onchange=SB_slidersync("'+input_name+'_r","'+input_name+'_v",true)>');
}
function SB_numselect(input_name,name,val,min,max,step){
	html='<SELECT ID="'+input_name+'_v" name="'+name+'" SIZE="1" onchange=SB_slidersync("'+input_name+'_r","'+input_name+'_v",false)>';
	for(var i=min, j=false;i<=max;i+=step){
		if ((!j) && (i>=val)) {ii=" selected";j=true} else {ii=""}
		html=html+'<OPTION VALUE='+i+ii+'>'+i+'</OPTION>';}
	return(html+'</SELECT>');
}
function SB_listselect(input_name,name,val,table,dims,size){
	html='<SELECT name="'+name+'" SIZE="1" onchange=SB_Submit()>';
	for(var i=0;i<size;i++){
		j="";
		if (dims==1){if (i==val) j=" selected";k=table[i];}
		else {if (table[i][0]==val) j=" selected";	k=table[i][1];}
		html=html+'<OPTION VALUE='+i+j+'>'+k+'</OPTION>';}
	return(html+'</SELECT>');
}
function SB_slidersync(IDslider, IDvar, sliderchange){
	if (document.getElementById(IDvar) && document.getElementById(IDslider)){
		if (sliderchange) document.getElementById(IDvar).value=document.getElementById(IDslider).value;
		else document.getElementById(IDslider).value=document.getElementById(IDvar).value;}
	SB_Submit();
}

function SB_Refresh(){	// gets the page again without resending any form values
	window.location.assign(window.location.pathname);
}
function SB_Submit(){	// Reload the Media directory and current preset samples
	document.getElementById("elem_SB_Form").submit();
}
function SB_Validate(){
}
