function SB_Update(){
	SB_GetAPI();
	if (SB_busy!=0) {		// this means SB is busy interpreting a sample set
		setTimeout(SB_Refresh, 1000);
		return;
	}
	for (var i=0;i<SB_numvars;i++){
		name=SB_VarName[i];val=SB_VarVal[i];
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
var SB_variables={	// make sure all passed parameters are covered here
	v_SB_MidiChannel: function(val){SB_MidiChannel=val;},
	v_SB_SoundVolume: function(val){SB_SoundVolume=val;},
	v_SB_MidiVolume: function(val){SB_MidiVolume=val;},
	v_SB_Preset: function(val){SB_Preset=val;},
	v_SB_Gain: function(val){SB_Gain=val;},
	v_SB_Pitchrange: function(val){SB_Pitchrange=val;},
	v_SB_Notemap: function(val){SB_Notemap=val;},
	v_SB_nm_inote: function(val){SB_nm_inote=val;},
	v_SB_nm_onote: function(val){SB_nm_onote=val;},
	v_SB_nm_unote: function(val){SB_nm_unote=val;},
	v_SB_nm_Q: function(val){SB_nm_Q=val;},
	v_SB_nm_map: function(val){SB_nm_name=val;},
	v_SB_nm_clr: function(val){SB_nm_name=val;},
	v_SB_nm_sav: function(val){SB_nm_name=val;},
	v_SB_nm_retune: function(val){SB_nm_retune=val;},
	v_SB_nm_voice: function(val){SB_nm_voice=val;},
	v_SB_Voice: function(val){SB_Voice=val;},
	v_SB_Scale: function(val){SB_Scale=val;},
	v_SB_Chord: function(val){SB_Chord=val;},
	v_SB_FVtype: function(val){SB_FVtype=val;},
	v_SB_FVroomsize: function(val){SB_FVroomsize=val;},
	v_SB_FVdamp: function(val){SB_FVdamp=val;},
	v_SB_FVlevel: function(val){SB_FVlevel=val;},
	v_SB_FVwidth: function(val){SB_FVwidth=val;},
	v_SB_AWtype: function(val){SB_AWtype=val;},
	v_SB_AWattack: function(val){SB_AWattack=val;},
	v_SB_AWrelease: function(val){SB_AWrelease=val;},
	v_SB_AWminfreq: function(val){SB_AWminfreq=val;},
	v_SB_AWmaxfreq: function(val){SB_AWmaxfreq=val;},
	v_SB_AWqfactor: function(val){SB_AWqfactor=val;},
	v_SB_AWmixing: function(val){SB_AWmixing=val;},
	v_SB_AWspeed: function(val){SB_AWspeed=val;},
	v_SB_AWlvlrange: function(val){SB_AWlvlrange=val;},
	v_SB_DLYtype: function(val){SB_DLYtype=val;},
	v_SB_DLYfb: function(val){SB_DLYfb=val;},
	v_SB_DLYwet: function(val){SB_DLYwet=val;},
	v_SB_DLYdry: function(val){SB_DLYdry=val;},
	v_SB_DLYtime: function(val){SB_DLYtime=val;},
	v_SB_DLYsteep: function(val){SB_DLYsteep=val;},
	v_SB_DLYsteplen: function(val){SB_DLYsteplen=val;},
	v_SB_DLYmin: function(val){SB_DLYmin=val;},
	v_SB_DLYmax: function(val){SB_DLYmax=val;},
	v_SB_LFtype: function(val){SB_LFtype=val;},
	v_SB_LFresonance: function(val){SB_LFresonance=val;},
	v_SB_LFcutoff: function(val){SB_LFcutoff=val;},
	v_SB_LFdrive: function(val){SB_LFdrive=val;},
	v_SB_LFlvl: function(val){SB_LFlvl=val;},
	v_SB_LFgain: function(val){SB_LFgain=val;},
	v_SB_LFOtype: function(val){SB_LFOtype=val;},
	v_SB_VIBRpitch: function(val){SB_VIBRpitch=val;},
	v_SB_VIBRspeed: function(val){SB_VIBRspeed=val;},
	v_SB_VIBRtrill: function(val){SB_VIBRtrill=val;},
	v_SB_TREMampl: function(val){SB_TREMampl=val;},
	v_SB_TREMspeed: function(val){SB_TREMspeed=val;},
	v_SB_TREMtrill: function(val){SB_TREMtrill=val;},
	v_SB_PANwidth: function(val){SB_PANwidth=val;},
	v_SB_PANspeed: function(val){SB_PANspeed=val;},
	v_SB_ARPstep: function(val){SB_ARPstep=val;},
	v_SB_ARPsustain: function(val){SB_ARPsustain=val;},
	v_SB_ARPloop: function(val){SB_ARPloop=val;},
	v_SB_ARP2end: function(val){SB_ARP2end=val;},
	v_SB_ARPord: function(val){SB_ARPord=val;},
	v_SB_ARPfade: function(val){SB_ARPfade=val;},
	v_SB_CHOrus: function(val){SB_CHOrus=val;},
	v_SB_CHOdepth: function(val){SB_CHOdepth=val;},
	v_SB_CHOgain: function(val){SB_CHOgain=val;},
	v_SB_RenewMedia: function(val){SB_RenewMedia=val;},
	v_SB_DefinitionTxt: function(val){SB_DefinitionTxt=val;}
}
var SB_input={	// make sure all passed parameters are covered here, be it with a dummy
	input_SB_MidiChannel: function(input_name,name,val,text){
		return(text+SB_numselect(input_name,name,val,1,16,1,1));
	},
	input_SB_Pitchrange: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,12,1)+SB_numselect(input_name,name,val,0,12,1,1));
	},
	input_SB_Chord: function(input_name,name,val,text){
		return(text+SB_listselect(input_name,name,val,SB_Chordname,1,SB_Chordname.length,1));
	},
	input_SB_Scale: function(input_name,name,val,text){
		return(text+SB_listselect(input_name,name,val,SB_Scalename,1,SB_Scalename.length,1));
	},
	input_SB_Preset: function(input_name,name,val,text){
		if (SB_Voicelist.length==0&&SB_xvoice==0) m=" Empty!" ;else m="";
		return(text+SB_listselect(input_name,name,val,SB_Presetlist,2,SB_Presetlist.length,1)+m);
	},
	input_SB_Voice: function(input_name,name,val,text){
		return(text+SB_listselect(input_name,name,val,SB_Voicelist,2,SB_Voicelist.length,1));
	},
	input_SB_Notemap: function(input_name,name,val,text){
		for (i=1;i<SB_Notemaps.length;i++){if (SB_Notemaps[i]==SB_Notemap) break;}
		return(text+SB_listselect(input_name,name,i,SB_Notemaps,1,SB_Notemaps.length,1));
	},
	input_SB_nm_inote: function(input_name,name,val,text){
		return(text+SB_listselect(input_name,name,val,SB_KeyNames,2,SB_KeyNames.length,1));
	},
	input_SB_nm_onote: function(input_name,name,val,text){
		return(text+SB_listselect(input_name,name,val,SB_FullNotename,2,SB_FullNotename.length,1));
	},
	input_SB_nm_unote: function(input_name,name,val,text){
		dd=SB_unote_options(SB_nm_onote)
		return(text+SB_listselect(input_name,name,val,dd,1,dd.length,1));
	},
	input_SB_nm_retune: function(input_name,name,val,text){
		return(text+SB_numselect(input_name,name,val,-50,50,1,1));
	},
	input_SB_nm_voice: function(input_name,name,val,text){
		//return(text+SB_numselect(input_name,name,val,0,127,1,0));
		return(text+SB_listselect(input_name,name,val,[[-1,"None"]].concat(SB_Voicelist),2,SB_Voicelist.length+1,1));
	},
	input_SB_nm_Q: function(input_name,name,val,text){
		return(SB_radioselect(input_name,name,val-1,text,SB_qFractions,SB_qFractions.length,1));
	},
	input_SB_nm_map: function(input_name,name,val,text){
		return(text+'<INPUT type="text" size="25" name="'+name+'" value="'+val+'" onchange=SB_Submit()</INPUT>');
		//return(text+'<INPUT type="text" size="25" name="'+name+'" value="'+val+'" pattern="[A-Za-z0-9],_\ -" title="Invalid character found"</INPUT>');
	},
	input_SB_nm_clr: function(input_name,name,val,text){
		return(SB_radioselect(input_name,name,val,text,["No",'Yes'],1,1));
	},
	input_SB_nm_sav: function(input_name,name,val,text){
		return(SB_radioselect(input_name,name,val,text,["No",'Yes'],1,1));
	},
	input_SB_SoundVolume: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)); // left out because of unexact behaviour of logic+alsa:  +SB_numselect(input_name,name,val,0,100,1,1));
	},
	input_SB_MidiVolume: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1,1));
	},
	input_SB_Gain: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,300,5)+SB_numselect(input_name,name,val,0,300,5,1));
	},
	input_SB_FVtype: function(input_name,name,val,text){
		return(SB_radioselect(input_name,name,val,text,SB_FVtypes,1,1));
	},
	input_SB_FVroomsize: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1,1));
	},
	input_SB_FVdamp: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1,1));
	},
	input_SB_FVlevel: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1,1));
	},
	input_SB_FVwidth: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1,1));
	},
	input_SB_AWtype: function(input_name,name,val,text){
		return(SB_radioselect(input_name,name,val,text,SB_AWtypes,1,1));
	},
	input_SB_AWattack: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,5,500,5)+SB_numselect(input_name,name,val,5,500,5,1));
	},
	input_SB_AWrelease: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,5,500,5)+SB_numselect(input_name,name,val,5,500,5,1));
	},
	input_SB_AWminfreq: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,20,500,20)+SB_numselect(input_name,name,val,20,500,20,1));
	},
	input_SB_AWmaxfreq: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,1000,10000,500)+SB_numselect(input_name,name,val,1000,10000,500,1));
	},
	input_SB_AWqfactor: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1,1));
	},
	input_SB_AWspeed: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,100,1100,20)+SB_numselect(input_name,name,val,100,1100,20,1));
	},
	input_SB_AWmixing: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1,1));
	},
	input_SB_AWlvlrange: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1,1));
	},
	input_SB_DLYtype: function(input_name,name,val,text){
		return(SB_radioselect(input_name,name,val,text,SB_DLYtypes,1,1));
	},
	input_SB_DLYfb: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1,1));
	},
	input_SB_DLYwet: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1,1));
	},
	input_SB_DLYdry: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1,1));
	},
	input_SB_DLYtime: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,1000,61000,1000)+SB_numselect(input_name,name,val,1000,61000,1000,1));
	},
	input_SB_DLYsteep: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,1,11,1)+SB_numselect(input_name,name,val,1,11,1,1));
	},
	input_SB_DLYsteplen: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,300,3300,50)+SB_numselect(input_name,name,val,300,3300,50,1));
	},
	input_SB_DLYmin: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,5,25,5)+SB_numselect(input_name,name,val,5,25,5,1));
	},
	input_SB_DLYmax: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,50,150,10)+SB_numselect(input_name,name,val,50,150,10,1));
	},
	input_SB_LFtype: function(input_name,name,val,text){
		return(SB_radioselect(input_name,name,val,text,SB_LFtypes,1,1));
	},
	input_SB_LFresonance: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,38,2)+SB_numselect(input_name,name,val,0,38,2,1));
	},
	input_SB_LFcutoff: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,1000,11000,1000)+SB_numselect(input_name,name,val,1000,11000,1000,1));
	},
	input_SB_LFdrive: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,1,20,1)+SB_numselect(input_name,name,val,1,20,1,1));
	},
	input_SB_LFlvl: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,10)+SB_numselect(input_name,name,val,0,100,10,1));
	},
	input_SB_LFgain: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,10,110,5)+SB_numselect(input_name,name,val,10,110,5,1));
	},
	input_SB_LFOtype: function(input_name,name,val,text){
		return(SB_radioselect(input_name,name,val,text,SB_LFOtypes,1,1));
	},
	input_SB_VIBRpitch: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,1,64,1)+SB_numselect(input_name,name,val,1,64,1,1));
	},
	input_SB_VIBRspeed: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,1,32,1)+SB_numselect(input_name,name,val,1,32,1,1));
	},
	input_SB_VIBRtrill: function(input_name,name,val,text){
		return(SB_radioselect(input_name,name,val,text,["Off","On"],1,1));
	},
	input_SB_TREMampl: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,1,100,1)+SB_numselect(input_name,name,val,1,100,1,1));
	},
	input_SB_TREMspeed: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,1,32,1)+SB_numselect(input_name,name,val,1,32,1,1));
	},
	input_SB_TREMtrill: function(input_name,name,val,text){
		return(SB_radioselect(input_name,name,val,text,["Off","On"],1,1));
	},
	input_SB_PANwidth: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,2,20,2)+SB_numselect(input_name,name,val,2,20,2,1));
	},
	input_SB_PANspeed: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,1,32,1)+SB_numselect(input_name,name,val,1,32,1,1));
	},
	input_SB_ARPstep: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,10,100,1)+SB_numselect(input_name,name,val,10,100,1,1));
	},
	input_SB_ARPsustain: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1,1));
	},
	input_SB_ARPloop: function(input_name,name,val,text){
		return(SB_radioselect(input_name,name,val,text,["Off","On"],1,1));
	},
	input_SB_ARP2end: function(input_name,name,val,text){
		return(SB_radioselect(input_name,name,val,text,["Off","On"],1,1));
	},
	input_SB_ARPord: function(input_name,name,val,text){
		return(SB_radioselect(input_name,name,val,text,SB_ARPordlist,1,1));
	},
	input_SB_ARPfade: function(input_name,name,val,text){
		j=""
		if (val<100) j="CHECKED"
		return(text+'<label class="inline alignx"><INPUT type="checkbox" onclick="return false;"'+j+'></label>'+SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1));
	},
	input_SB_CHOrus: function(input_name,name,val,text){
		return(SB_radioselect(input_name,name,val,text,["Off","On"],1,1));
	},
	input_SB_CHOdepth: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,2,15,1)+SB_numselect(input_name,name,val,2,15,1,1));
	},
	input_SB_CHOgain: function(input_name,name,val,text){
		return(text+SB_slider(input_name,name,val,30,80,2)+SB_numselect(input_name,name,val,30,80,2,1));
	},
	input_SB_RenewMedia: function(input_name,name,val,text){
		return('<LABEL><INPUT type="checkbox" name="'+name+'" class="hidden" value="Yes" onclick="SB_Submit();"><span class="button">'+text+'</span></LABEL>');
	},
	input_SB_DefinitionTxt: function(input_name,name,val,text){
		if (SB_Samplesdir.charAt(0)=='/') m='';else m=' readonly';
		return('<DIV STYLE="line-height:100%;text-align:center">'+text+m+'</DIV><TEXTAREA name="'+name+'"'+m+'>'+val+'</TEXTAREA>');
	}
}

SB_ElemID=["elem_SB_Form","elem_SB_Samplesdir","elem_SB_Mode","elem_SB_xvoice","elem_SB_DefErr","elem_SB_LastMidiNote","elem_SB_LastMusicNote","elem_SB_Scale","elem_SB_Chord","elem_SB_Chords","elem_SB_Scales","elem_SB_Notemap","elem_SB_bTracks"];
SB_numelems=SB_ElemID.length;
var SB_element={
	elem_SB_Form: function(elem_name){
		document.getElementById(elem_name).action = window.location.pathname;
		document.getElementById(elem_name).method = 'POST';
		document.getElementById(elem_name).type = 'SUBMIT';

	},
	elem_SB_Samplesdir: function(elem_name){
		document.getElementById(elem_name).innerHTML=text+'<SPAN CLASS="value">'+SB_Samplesdir+'</SPAN>';
	},
	elem_SB_Mode: function(elem_name){
		document.getElementById(elem_name).innerHTML=text+'<SPAN CLASS="value">'+SB_Mode+'</SPAN>';
	},
	elem_SB_xvoice: function(elem_name,text) {
		if (SB_xvoice==0) j="";else j="CHECKED";
		document.getElementById(elem_name).innerHTML=text+'<label class="inline alignx"><INPUT type="checkbox" onclick="return false;"'+j+'></label>';
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
		if (SB_LastMusicNote<0) {m="None";} else {m=SB_Noteprint(SB_LastMusicNote);}
		document.getElementById(elem_name).innerHTML=text+'<SPAN CLASS="value">'+m+'</SPAN>';
	},
	elem_SB_Scale: function(elem_name){
		document.getElementById(elem_name).innerHTML=text+'<SPAN CLASS="value">'+SB_Scalename[SB_Scale]+'</SPAN>';
	},
	elem_SB_Chord: function(elem_name){
		document.getElementById(elem_name).innerHTML=text+'<SPAN CLASS="value">'+SB_Chordname[SB_Chord]+'</SPAN>';
	},
	elem_SB_Chords: function(elem_name){
		html='<TABLE BORDER="1"><TR><TH>Chord</TH><TH>Notes for C</TH></TR>';
		for (i=1;i<SB_Chordname.length;i++){
			html=html+'<TR VALIGN="top"><TD>'+SB_Chordname[i]+'</TD><TD>';
			filler="";
			for (j=0;j<SB_Chordnote[i].length;j++){
				html=html+filler+SB_Noteprint(SB_Chordnote[i][j]);
				filler=", ";
			}
			html=html+'</TD></TR>';
		}
		document.getElementById(elem_name).innerHTML=html+'</TABLE>';
	},
	elem_SB_Scales: function(elem_name){
		html='<TABLE BORDER="1"><TR><TH>Scale</TH><TH>Implemented Chords</TH></TR>';
		for (i=1;i<SB_Scalename.length;i++){
			html=html+'<TR VALIGN="top"><TD>'+SB_Scalename[i]+'</TD><TD>';
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
	},
	elem_SB_Notemap: function(elem_name){
		html='<TABLE BORDER="1" CELLPADDING="3" ID="TableID_Notemap"><TR><TH style="display:none;"><TH>Key</TH><TH>Plays</TH><TH>Tune</TH><TH>Voice</TH></TR>';
		for (var i=0;i<SB_NoteMapping.length;i++){
			var inote=SB_NoteMapping[i][0];
			var inotenam="%s" %inote;
			var retune="";
			var voice="";
			var j=0;var k="";
			for (j=0;i<SB_KeyNames.length;j++){
				if (SB_KeyNames[j][0]==inote){
					inotenam=SB_KeyNames[j][1];
					if (inote==SB_nm_inote){k=' style="background-color:Khaki;"'}
					break;
				}
			}
			var dd=SB_unote_options(SB_NoteMapping[i][2]);
			onotenam=dd[SB_NoteMapping[i][5]];
			if (onotenam=="None"){onotenam="";}
			if (SB_NoteMapping[i][3]!=0){retune=SB_NoteMapping[i][3]}
			if (SB_NoteMapping[i][4]!=0){voice=SB_NoteMapping[i][4]}
			html=html+'<TR VALIGN="top"'+k+'><TD style="display:none;">'+j+'</TD><TD ALIGN="center">'+inotenam+'</TD><TD ALIGN="center">'+onotenam+'</TD><TD ALIGN="center">'+retune+'</TD><TD ALIGN="center">'+voice+'</TD></TR>';
		}
		document.getElementById(elem_name).innerHTML=html+'</TABLE>';
	},
	elem_SB_bTracks: function(elem_name){
		if (SB_bTracks.length==0) {document.getElementById(elem_name).innerHTML='';}
		else {
			html='<TABLE BORDER="1" CELLPADDING="3"><TR><TD>Knob</TD><TH>Backtrack</TH><TD>Note</TH></TD>';
			for (i=0;i<SB_bTracks.length;i++){
				html=html+'<TR VALIGN="top"><TD ALIGN="center">'+SB_bTracks[i][0]+'</TD><TD ALIGN="center">'+SB_bTracks[i][1]+'</TD><TD ALIGN="center">'+SB_bTracks[i][2]+'</TD></TR>';
			}
			document.getElementById(elem_name).innerHTML=html+'</TABLE><P>';
		}
	}
}

function SB_notechord(note,chord){
	if (SB_Chordname[chord]=="Maj") c="";
	else c=SB_Chordname[chord].toLowerCase();
	var p=SB_Noteprint(note);
	return(p+c);
}
function SB_slider(input_name,name,val,min,max,step){
	return('<INPUT ID="'+input_name+'_r" name="'+name+'" TYPE="range" VALUE="'+val+'" min="'+min+'" max="'+max+'" step="'+step+'" onchange=SB_slidersync("'+input_name+'_r","'+input_name+'_v",true)>');
}
function SB_numselect(input_name,name,val,min,max,step,update){
	html='<SELECT ID="'+input_name+'_v" name="'+name+'" SIZE="1"';
	if (update==1) {html=html+' onchange=SB_slidersync("'+input_name+'_r","'+input_name+'_v",false)'}
	html=html+'>';
	for(var i=min, j=false;i<=max;i+=step){
		if ((!j) && (i>=val)) {ii=" selected";j=true} else {ii=""}
		html=html+'<OPTION VALUE='+i+ii+'>'+i+'</OPTION>';}
	return(html+'</SELECT>');
}
function SB_listselect(input_name,name,val,table,dims,size,update){
	html='<SELECT name="'+name+'" id="select_'+name+'" SIZE="1"';
	if (update==1) {html=html+' onchange=SB_Submit()';}
	//else {html=html+' onchange=SB_updateval(this)';}
	html=html+'>';
	for(var i=0;i<size;i++){
		j="";
		if (dims==1){if (i==val) j=" selected";k=table[i];}
		else {if (table[i][0]==val) j=" selected";k=table[i][1];}
		html=html+'<OPTION VALUE='+i+j+'>'+k+'</OPTION>';}
	return(html+'</SELECT>');
}
function SB_notemapselect() {
    var rows = document.getElementById("TableID_Notemap").rows;
    for (i = 0; i < rows.length; i++) {
        rows[i].onclick = function(){ return function(){
			document.getElementById("select_SB_nm_inote").value = this.cells[0].innerHTML;
            SB_Submit();
        };}(rows[i]);
    }
}
function SB_unote_options(onote){
	var d=[];
	var note=onote+2
	if (onote<0) {
		d.push(SB_FullNotename[note][2])
	}
	else if (note>=SB_firstnote&&note<=SB_lastnote) {
		var i;
		for (i=0; i<SB_FullNotename[note][2].length; i++) {
			d.push(SB_FullNotename[note][2][i]);
		};
		var octave=SB_FullNotename[note][1].slice(-1);
		for (i=0; i<d.length; i++) {
			if (d[i]=="Ck") {octave=(Number(octave)+1).toString();};
			d[i]=d[i]+octave;
		};
	}
	else {
		d.push((onote).toString());
	}
	return(d)
}
function SB_slidersync(IDslider, IDvar, sliderchange){
	if (document.getElementById(IDvar) && document.getElementById(IDslider)){
		if (sliderchange) document.getElementById(IDvar).value=document.getElementById(IDslider).value;
		else document.getElementById(IDslider).value=document.getElementById(IDvar).value;}
	SB_Submit();
}
function SB_radioselect(input_name,name,val,text,table,dims,update){
	html=""
	for (i=0;i<table.length;i++){
		j="";
		if (i==val) j="CHECKED"; else j="";
		if (dims==1){if (i==val) j=" CHECKED";k=table[i];l=table[i];}
		else {if (table[i][0]==val) j=" CHECKED";k=table[i][1];l=table[i][0];}
		html=html+' <INPUT type="radio" name="'+name+'" value="'+l+'" '+j;
		if (update==1) {html=html+' onclick="SB_Submit()"'};
		html=html+'>'+k;
	}
	return(text+html);
}

var SB_Notename=[["C"],["Cs"],["C&#9839;","D&#9837;"],["Dk"],["D"],["Ds"],["D&#9839;","E&#9837;"],["Ek"],["E"],["Es","Fk"],["F"],["Fs"],["F&#9839;","G&#9837;"],["Gk"],["G"],["Gs"],["G&#9839;","A&#9837;"],["Ak"],["A"],["As"],["A&#9839;","B&#9837;"],["Bk"],["B"],["Bs","Ck"],["FX"]];
var SB_FullNotename=new Array(130);var SB_firstnote;var SB_lastnote
function SB_init_FullNotenames(){
	SB_FullNotename[0]=[-2,"Ctrl",["Ctrl"]];
	SB_FullNotename[1]=[-1,"None",["None"]];
	SB_firstnote=127-SB_Stop127+1;
	SB_lastnote=SB_Stop127+1;
	j=0;k=-1;
	if (SB_nm_Q==1){
		for (i=2;i<130;i++){
			l=i-2;
			if (i<SB_firstnote||i>SB_lastnote) {SB_FullNotename[i]=[l,l];}
			else {SB_FullNotename[i]=[l,SB_Notename[j*2][0]+k,SB_Notename[j*2]];}
			if (j<11) {j++;} else {j=0;k++;}
		}
	} else {
		j=12;k=1;
		for (i=2;i<130;i++){
			l=i-2;
			if (l<SB_firstnote||l>SB_lastnote) {SB_FullNotename[i]=[l,l];}
			else {SB_FullNotename[i]=[l,SB_Notename[j][0]+k,SB_Notename[j]];}
			if (j<23) {j++;} else {j=0;k++;}
		}
	}
}
for (i=0;i<SB_Scalename.length;i++){
	SB_Scalename[i]=SB_Scalename[i].replace(/#/,"&#9839;").replace(/b/,"&#9837;");
}
function SB_Noteprint(note){
	var n=note*2
	var p=SB_Notename[n][0];
	if (SB_Notename[n].length>1) {p=p+"/"+SB_Notename[n][1];}
	return(p);
}

function SB_Refresh(){	// gets the page again without resending any form values
	window.location.assign(window.location.pathname);
}
function SB_Submit(){
	document.getElementById("elem_SB_Form").submit();
}
