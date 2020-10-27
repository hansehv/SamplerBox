// Samplerbox filter modules by hansehv, http://homspace.xs4all.nl/homspace/samplerbox

// Februari 2018:
//  - DLLEXPORT based on full sources inspired by Erik Nieuwlands (www.nickyspride.nl/sb2/)
//    I agree with Erik: "perhaps there is a smarter way, but this worked!"
//  - added (adapted versions of):
//    - freeverb by Jezar at Dreampoint
// Februari/March/April 2019:
//    - autowah by Daniel Zanco extended with LFO and pedal control
//    - echo and flanger (delay line effects) based on codesnippets by Gabriel Rivas
//    - moogladder based on model&software of Stefano D'Angelo
// September 2020:
//    - peak limiter from the Simple Compressor class by Citizen Chunk
//    - overdrive inspired by various discussions

#define DLLEXPORT extern "C" 

#include "allpass.cpp"		// Freeverb modules
#include "comb.cpp"
#include "revmodel.cpp"
#include "autowah.cpp"		// (Auto)Wah module
#include "delay.cpp"		// Delay line module for echo and flanger
#include "moogladder.cpp"	// Module for Moog pass filters
#include "overdrive.cpp"		// Non-linear distortion effects
#include "SimpleLimit.cpp"	// Peaklimiter
#include "SimpleEnvelope.cpp"
//#include "console.cpp"	// Debugger

// Instantiation of classes
revmodel rv;				// Reverb
autoWah aw;					// Wah (auto, pedal, LFO)
delay dly;					// Delay + phaser
LadderFilter lf;			// Moog low-pass
overdrive od;				// Overdrive
chunkware_simple::SimpleLimit pl;	// peaklimiter

// General routine
void SampleRate(int val)
{
	aw.setSampleRate(val);
	lf.SetsampleRate(val);
	pl.setSampleRate(val);
}
DLLEXPORT void setSampleRate(int val) { SampleRate(val); } 

// Reverb=Freeverb entrypoints
DLLEXPORT void fvsetroomsize(float val) { rv.setroomsize(val); } 
DLLEXPORT void fvsetdamp(float val) { rv.setdamp(val); }
DLLEXPORT void fvsetwet(float val) { rv.setwet(val); }
DLLEXPORT void fvsetdry(float val) { rv.setdry(val); }
DLLEXPORT void fvsetwidth(float val) { rv.setwidth(val); }
DLLEXPORT void fvmute() { rv.mute(); }
DLLEXPORT void reverb(float* inp, float* outp, int count) { rv.processreplacestereo(inp,outp,count); }
// Available, but as yet unused in samplerbox:
//DLLEXPORT float fvgetroomsize() { return rv.getroomsize(); } 
//DLLEXPORT float fvgetdamp() { return rv.getdamp(); }
//DLLEXPORT float fvgetwet() { return rv.getwet(); }
//DLLEXPORT float fvgetdry() { return rv.getdry(); }
//DLLEXPORT float fvgetwidth() { return rv.getwidth(); }

// AutoWah entrypoints
DLLEXPORT void awsetMinMaxFreq(float min, float max) { aw.setMinMaxFreq(min,max); } 
DLLEXPORT void awsetQualityFactor(float val) { aw.setQualityFactor(val); } 
DLLEXPORT void awsetMixing(float val) { aw.setMixing(val); } 
DLLEXPORT void awsetWahType(int val) { aw.setWahType(val); } 
DLLEXPORT void awsetAttack(float val) { aw.setAttack(val); } 
DLLEXPORT void awsetRelease(float val) { aw.setRelease(val); } 
DLLEXPORT void awsetSpeed(float val) { aw.setSpeed(val); } 
DLLEXPORT void awsetCCval(float val) { aw.setCCval(val); } 
DLLEXPORT void awsetLVLrange(float val) { aw.setLVLrange(val); } 
DLLEXPORT void awmute() { aw.mute(); }
DLLEXPORT void autowah(float* inp, float* outp, int count) { aw.DoWah(inp,outp,count); } 

// Delay (echo & flanger) entrypoints
DLLEXPORT void dlysetfb(float val) { dly.setfb(val); } 
DLLEXPORT void dlysetfw(float val) { dly.setfw(val); } 
DLLEXPORT void dlysetmix(float val) { dly.setmix(val); } 
DLLEXPORT void dlysetdelay(float val) { dly.setdelay(val); } 
DLLEXPORT void dlysettype(int val) { dly.settype(val); } 
DLLEXPORT void dlysetsweep(float steepness, float samples) { dly.setsweep(steepness, samples); } 
DLLEXPORT void dlysetrange(float min, float max) { dly.setrange(min,max); } 
DLLEXPORT void dlymute() { dly.mute(); }
DLLEXPORT void delay(float* inp, float* outp, int count) { dly.DoDelay(inp,outp,count); } 

// Ladderfilter (moog) entrypoints
DLLEXPORT void lfmute() { lf.Mute(); }
DLLEXPORT void lfsetresonance(float val) { lf.SetResonance(val); } 
DLLEXPORT void lfsetcutoff(float val) { lf.SetCutoff(val); } 
DLLEXPORT void lfsetdrive(float val) { lf.SetDrive(val); } 
DLLEXPORT void lfsetdry(float val) { lf.SetDry(val); } 
DLLEXPORT void lfsetwet(float val) { lf.SetWet(val); } 
DLLEXPORT void lfsetgain(float val) { lf.SetGain(val); } 
DLLEXPORT void moog(float* inp, float* outp, int count) { lf.MoogLadder(inp,outp,count); } 

// Overdrive entrypoints
DLLEXPORT void odsetboost(float val) { od.set_boost(val); } 
DLLEXPORT void odsetdrive(float val) { od.set_drive(val); } 
DLLEXPORT void odsettone(float val) { od.set_tone(val); } 
DLLEXPORT void odsetwet(float val) { od.set_wet(val); } 
DLLEXPORT void odsetdry(float val) { od.set_dry(val); } 
DLLEXPORT void overdrive(float* inp, float* outp, int count) { od.process(inp,outp,count); } 

// Peaklimiter entrypoints
DLLEXPORT void plsetthresh(float val) { pl.setThresh(val); } 
DLLEXPORT void plsetattack(float val) { pl.setAttack(val); } 
DLLEXPORT void plsetrelease(float val) { pl.setRelease(val); } 
DLLEXPORT void plinit() { pl.initRuntime(); } 
DLLEXPORT void limiter(float* inp, float* outp, int count) { pl.ProcessChunk(inp,outp,count); } 
