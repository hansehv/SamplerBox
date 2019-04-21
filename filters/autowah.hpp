// original by Daniel Zanco: https://github.com/dangpzanco/autowah
// adapted for samplerbox use and extended with LFO + CC control
//          by HansEhv: https://github.com/hansehv/SamplerBox

#include <cmath>
#include <stdint.h>

const double pi = 3.1415926535897932;
const float piFloat = 3.1415926535897932f;
const float maxInt16 = 32767.0f / 32768.0f;

class autoWah {
public:
	autoWah();
	~autoWah();

	float runEffect(float x);
	void setSampleRate(float fs);

	void setMinMaxFreq(float mi, float mx);	// General
	void setQualityFactor(float Q);		// General
	void setMixing(float alphaMix);		// General
	void setWahType(int type);		// Choose:
	void setAttack(float tauA);		// Envelope
	void setRelease(float tauR);		// Envelope
	void setSpeed(float step);		// LFO
	void setCCval(float val);		// MIDIcontroller (0-127)
	void setLVLrange(float val);		// Valuerange for LFO and CC (0-127, 127 is full range)

	void mute();
	void DoWah(float *inputstream, float *outputstream, int numsamples);

private:
	float (autoWah::*getLevel)(float x);
	float ENVlevel(float x);
	float LFOlevel(float x);
	float CClevel(float x);
	float lowPassFilter(float x);
	float stateVariableFilter(float x);
	inline float mixer(float x, float y);

	float sin(float x);
	float precisionSin(float x);
	float tan(float x);
	float precisionTan(float x);

	// Sin and Tan Constants
	const float sinConst3, sinConst5;
	const float tanConst3, tanConst5;

	// Level parameters
	float alphaA, alphaR, betaA, betaR;	// Envelope detector
	float LFOlvl, LFOmax, LFOmin, LFOstep;	// Low Frequency Oscillator
	float CCval;				// Pedal (or other midi controller)
	float LVLrange, LVLstart;		// Valuerange for LFO an CC

	// State Variable Filter parameters
	float minFreq, freqBandwidth;
	float LyLowpass,LyBandpass,LyHighpass;	// adapted during process
	float RyLowpass,RyBandpass,RyHighpass;	// adapted during process
	float *yLowpass,*yBandpass,*yHighpass;	// adapted during process
	float q, fs, centerFreq;

	// Lowpass filter parameters
	float LbufferL[2],LbufferLP;		// adapted during process
	float RbufferL[2],RbufferLP;		// adapted during process
	float (*bufferL)[2],*bufferLP;		// adapted during process
	float gainLP;

	// Mixer parameters
	float alphaMix, betaMix;

};

