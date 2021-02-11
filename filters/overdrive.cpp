#include "overdrive.hpp"

overdrive::overdrive()
{
	lastLeft = 0.0f;		/* last computed left channel */
	lastRight = 0.0f;		/* last computed right channel */
	drinv = 0.0f;			/* inversed distortionlevel with range correction */
	set_boost(70);
	set_drive(3);
	set_tone(0.3);
	set_wet(1.0);
	set_dry(0.0);
}

overdrive::~overdrive()
{
}

void overdrive::set_boost(float val)
{
	boost = val*100;
}

void overdrive::set_drive(float val)
{
	drive = val;
	drinv = 1 / fastatan( val );
}

void overdrive::set_tone(float val)
{
	tone = val;
}

void overdrive::set_wet(float val)
{
	wet = val;
}

void overdrive::set_dry(float val)
{
	dry = val;
}

inline float overdrive::fastatan( float x )
{
    return (x / (1.0 + 0.28 * (x * x)));
}

inline float overdrive::softclip( float in )
{
	return drinv * fastatan( in * drive/boost ) * boost;
}

// --------------- make basic filter(s) callable from from samplerbox ------------

void overdrive::process(float *inputstream, float *outputstream, int numsamples)
{
	float *inS,*outS;

	inS=inputstream;
	outS=outputstream;

	for (int l=0;l<numsamples;l++)
	{
	// Left
		lastLeft = tone * lastLeft + (1-tone) * softclip(*inS);
		*outS = *inS * dry + wet * lastLeft;
		inS++;
		outS++;

	// Right
		lastRight = tone * lastRight + (1-tone) * softclip(*inS);
		*outS = *inS * dry + wet * lastRight;
		inS++;
		outS++;

	}
}

