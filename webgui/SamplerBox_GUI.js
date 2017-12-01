SB_ElemID=["elem_SB_Form"];
SB_numelems=SB_ElemID.length;

//function SB_GetVars() {	// this is experimental
//	let stateCheck = setInterval(() => {
//		if (document.readyState === 'complete') {
//			clearInterval(stateCheck);
//			SB_GetAPI();
//		}
//	}, 100);
//}

function SB_Update(){
	SB_GetAPI();
	if (SB_Loading=='Yes') {
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
		}
		input_name="input_"+name;
		if (document.getElementById(input_name)) document.getElementById(input_name).innerHTML=SB_input[input_name](input_name,name,val);
	}
	for (i=0;i<SB_numelems;i++){
		name=SB_ElemID[i];
		if (document.getElementById(name)) SB_element[name](name);
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
	v_SB_Chord: function(val){SB_Chord=val;}
}
var SB_input={
	input_SB_MidiChannel: function(input_name,name,val){
		return(SB_numselect(input_name,name,val,1,16,1));
	},
	input_SB_Transpose: function(input_name,name,val){
		return(SB_numselect(input_name,name,val,-12,12,1));
	},
	input_SB_Chord: function(input_name,name,val){
		html='<SELECT name="'+name+'" SIZE="1">';
		for(var i=0;i<SB_numchords;i++){
			if (i==val) j=" selected"; else j="";
			html=html+'<OPTION VALUE='+i+j+'>'+SB_Chordname[i]+'</OPTION>';
		}
		return(html+'</SELECT>');
	},
	input_SB_Scale: function(input_name,name,val){
		html='<SELECT name="'+name+'" SIZE="1">';
		for(var i=0;i<SB_numscales;i++){
			if (i==val) j=" selected"; else j="";
			html=html+'<OPTION VALUE='+i+j+'>'+SB_Scalename[i]+'</OPTION>';
		}
		return(html+'</SELECT>');
	},
	input_SB_Preset: function(input_name,name,val){
		html='<SELECT name="'+name+'" ID="hide_'+input_name+'" SIZE="1">';
		for(var i=0;i<SB_numpresets;i++){
			if (SB_Presetlist[i][0]==val) j=" selected"; else j="";
			html=html+'<OPTION VALUE='+i+j+'>'+SB_Presetlist[i][1]+'</OPTION>';
		}
		return(html+'</SELECT>');
	},
	input_SB_SoundVolume: function(input_name,name,val){
		return(SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1));
	},
	input_SB_MidiVolume: function(input_name,name,val){
		return(SB_slider(input_name,name,val,0,100,1)+SB_numselect(input_name,name,val,0,100,1));
	},
	input_SB_Gain: function(input_name,name,val){
		return(SB_slider(input_name,name,val,0,300,5)+SB_numselect(input_name,name,val,0,300,5));
	}
}
var SB_element={
	elem_SB_Form: function(name){
		document.getElementById(name).action = window.location.pathname;
		document.getElementById(name).method = "POST";
		document.getElementById(name).onsubmit = "return SB_Validate();";
		document.getElementById(name).type = "SUBMIT";
	}
}
function SB_slider(input_name,name,val,min,max,step){
	return('<INPUT ID="'+input_name+'_r" name="'+name+'" TYPE="range" VALUE="'+val+'" min="'+min+'" max="'+max+'" step="'+step+'" onchange=SB_slidersync("'+input_name+'_r","'+input_name+'_v",true)>');
}
function SB_numselect(input_name,name,val,min,max,step){
	html='<SELECT ID="'+input_name+'_v" name="'+name+'" SIZE="1" onchange=SB_slidersync("'+input_name+'_r","'+input_name+'_v",false)>';
	for(var i=min, j=false;i<=max;i+=step){
		if ((!j) && (i>=val)) {ii=" selected";j=true} else {ii=""}
		html=html+'<OPTION VALUE='+i+ii+'>'+i+'</OPTION>';
	}
	return(html+'</SELECT>');
}
function SB_slidersync(IDslider, IDvar, sliderchange){
	if (document.getElementById(IDvar) && document.getElementById(IDslider)){
		if (sliderchange) document.getElementById(IDvar).value=document.getElementById(IDslider).value;
		else document.getElementById(IDslider).value=document.getElementById(IDvar).value;
	}
}

function SB_Validate(){
}
function SB_Refresh(){	// gets the page again without resending any form values
	window.location.assign(window.location.pathname);
}
function SB_Reload(){	// Reload the USB directory and current preset samples
	document.getElementById("elem_SB_Form").submit();
}
