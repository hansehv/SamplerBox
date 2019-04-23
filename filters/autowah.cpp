#include "autowah.hpp"

autoWah::autoWah() : 
	sinConst3(-1.0f / 6.0f), sinConst5(1.0f / 120.0f), 
	tanConst3(1.0f / 3.0f), tanConst5(1.0f / 3.0f),
	fs(44.1e3)
{
	setAttack(40e-3f);
	setRelease(2e-3f);
	setMinMaxFreq(20, 3000);
	setQualityFactor(1.0f / 5.0f);
	setMixing(0.9f);
	LFOmax=10000000;
	LFOmin=LFOmax/100;
	LFOlvl=LFOmax;
	setSpeed(500.0f);
	setCCval(0.0f);
	setLVLrange(90.0f);
	mute();
	getLevel=&autoWah::ENVlevel;
}

autoWah::~autoWah()
{
}

void autoWah::mute()
{
	LyLowpass=0.0f;
	LyBandpass=0.0f;
	LyHighpass=0.0f;
	RyLowpass=0.0f;
	RyBandpass=0.0f;
	RyHighpass=0.0f; 
	LbufferL[0]=0.0f; 
	LbufferL[1]=0.0f; 
	LbufferLP=0.0f;
	RbufferL[0]=0.0f;
	RbufferL[2]=0.0f;
	RbufferLP=0.0f;
}

float autoWah::runEffect(float x)
{
	float yL = (this->*getLevel)(x);

	//fc = yL * (maxFreq - minFreq) + minFreq;
	centerFreq = yL * freqBandwidth + minFreq;

	float xF = lowPassFilter(x);
	float yF = stateVariableFilter(xF);

	float y = mixer(x, yF);

	return y;
}

float autoWah::ENVlevel(float x)
{
	float xL = x;
	if (xL < 0.0f) xL = -xL; // xL = abs(x)
	float y1 = alphaR * *bufferL[1] + betaR * xL;
	if (xL > y1)	*bufferL[1] = xL;
	else		*bufferL[1] = y1;
	*bufferL[0] = alphaA * *bufferL[0] + betaA * *bufferL[1];

	return *bufferL[0];
}

float autoWah::LFOlevel(float x)
{
	(void)x;	// silence compiler warning
	LFOlvl = LFOlvl-LFOstep;
	if (LFOlvl < LFOmin || LFOlvl > LFOmax) {
		LFOstep = -LFOstep;
		LFOlvl = LFOlvl- 2*LFOstep;
		}
	return LVLstart+LFOlvl/LFOmax*LVLrange;
}

float autoWah::CClevel(float x)
{
	(void)x;	// silence compiler warning
	return LVLstart+CCval*LVLrange;
}

float autoWah::lowPassFilter(float x)		// sets global bufferLP
{
	//float K = std::tan(centerFreq);
	float K = autoWah::tan(centerFreq);
	float b0 = K / (K + 1);
	// b1 = b0;
	// a1 = (K - 1) / (K + 1);
	float a1 = 2.0f * (b0 - 0.5f);

	float xh = x - a1 * *bufferLP;
	float y = b0 * (xh + *bufferLP);
	*bufferLP = xh;

	return gainLP * y;
}

float autoWah::stateVariableFilter(float x)	// sets globals yXpass
{
	float f = 2.0f * autoWah::sin(centerFreq);

	*yHighpass  = x - *yLowpass - q * *yBandpass;
	*yBandpass += f * *yHighpass;
	*yLowpass  += f * *yBandpass;

	return *yBandpass;
}

void autoWah::setWahType(int type)
{
	switch(type) {
		case 1:
		      getLevel=&autoWah::ENVlevel;
		      break;
		case 2:
		      getLevel=&autoWah::LFOlevel;
		      break;
		case 3:
		      getLevel=&autoWah::CClevel;
		      break;
	}
}

void autoWah::setAttack(float tauA)
{
	alphaA = std::exp(-1.0 / (tauA*fs));
	betaA = 1.0f - alphaA;
}

void autoWah::setRelease(float tauR)
{
	alphaR = std::exp(-1.0 / (tauR*fs));
	betaR = 1.0f - alphaR;
}

void autoWah::setMinMaxFreq(float x_minFreq, float x_maxFreq)
{
	freqBandwidth = pi*(2.0f*x_maxFreq - x_minFreq)/fs;
	minFreq = pi*x_minFreq/fs;
}

void autoWah::setSampleRate(float x)
{
	fs = x;
}

void autoWah::setSpeed(float x)
{
	LFOstep = x;
}

void autoWah::setCCval(float x)
{
	CCval = x/127;
}

void autoWah::setLVLrange(float x)
{
	LVLrange=x/127;
	LVLstart=(1-LVLrange)/2;
}

void autoWah::setQualityFactor(float x)
{
	q = x;
	gainLP = std::sqrt(0.5f * q);
}

void autoWah::setMixing(float x)
{
	alphaMix = x * 5;
	betaMix = 1.0f - x;
}

inline float autoWah::mixer(float x, float y)
{
	return alphaMix * y + betaMix * x;
}

float autoWah::sin(float x)
{
	return x * (1.0f + sinConst3*x*x);
}

float autoWah::precisionSin(float x)
{
	float x2 = x * x;
	float x4 = x2 * x2;
	return x * (1.0f + sinConst3*x2 + sinConst5*x4);
}

float autoWah::tan(float x)
{
	return x * (1.0f + tanConst3*x*x);
}

float autoWah::precisionTan(float x)
{
	float x2 = x * x;
	float x4 = x2 * x2;
	return x * (1.0f + tanConst3*x2 + tanConst5*x4);
}

// --------------- make basic filter callable from from samplerbox ------------

void autoWah::DoWah(float *inputstream, float *outputstream, int numsamples)
{
	float *inS,*outS,x,y;

	inS=inputstream;
	outS=outputstream;

	for (int l=0;l<numsamples;l++)
	{
	// Left
		yLowpass=&LyLowpass;
		yBandpass=&LyBandpass;
		yHighpass=&LyHighpass;
		bufferL=&LbufferL;
		bufferLP=&LbufferLP;

		x = *inS/32768.0f;
		y = runEffect(x);
		// Saturation
		if (y > maxInt16) y = maxInt16;
		else if (y < -1.0f) y = -1.0f;
		*outS = (int16_t)(y * 32768.0f);

		inS++;
		outS++;

	// Right
		yLowpass=&RyLowpass;
		yBandpass=&RyBandpass;
		yHighpass=&RyHighpass;
		bufferL=&RbufferL;
		bufferLP=&RbufferLP;

		x = *inS/32768.0f;
		y = runEffect(x);
		// Saturation
		if (y > maxInt16) y = maxInt16;
		else if (y < -1.0f) y = -1.0f;
		*outS = (int16_t)(y * 32768.0f);

		inS++;
		outS++;
	}
}

