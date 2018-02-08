// Samplerbox filter modules by hansehv, http://homspace.xs4all.nl/homspace/samplerbox

// Februari 2018:
//  - DLLEXPORT based on full sources inspired by Erik Nieuwlands (www.nickyspride.nl/sb2/)
//    I agree with Erik: "perhaps there is a smarter way, but this worked!"
//  - added (adapted) freeverb by Jezar at Dreampoint

#define DLLEXPORT extern "C" 

// Freeverb modules
#include "allpass.cpp"
#include "comb.cpp"
#include "revmodel.cpp"

// Instantiation of class
revmodel rv;

// Freeverb entrypoints
DLLEXPORT void setroomsize(float val) { rv.setroomsize(val); } 
DLLEXPORT float getroomsize() { return rv.getroomsize(); } 
DLLEXPORT void setdamp(float val) { rv.setdamp(val); }
DLLEXPORT float getdamp() { return rv.getdamp(); }
DLLEXPORT void setwet(float val) { rv.setwet(val); }
DLLEXPORT float getwet() { return rv.getwet(); }
DLLEXPORT void setdry(float val) { rv.setdry(val); }
DLLEXPORT float getdry() { return rv.getdry(); }
DLLEXPORT void setwidth(float val) { rv.setwidth(val); }
DLLEXPORT float getwidth() { return rv.getwidth(); }
DLLEXPORT void reverb(float* inp, float* outp, int count) { rv.processreplacestereo(inp,outp,count); } 

