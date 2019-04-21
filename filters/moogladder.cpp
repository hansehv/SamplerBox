/*
Copyright 2012 Stefano D'Angelo <zanga.mail@gmail.com>

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THIS SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
*/

#include "moogladder.hpp"
#include <cstring>
//#include <cmath>
#define MOOG_PI        3.14159265358979323846264338327950288

/*
This model is based on a reference implementation of an algorithm developed by
Stefano D'Angelo and Vesa Valimaki, presented in a paper published at ICASSP in 2013.
This improved model is based on a circuit analysis and compared against a reference
Ngspice simulation. In the paper, it is noted that this particular model is
more accurate in preserving the self-oscillating nature of the real filter.

References: "An Improved Virtual Analog Model of the Moog Ladder Filter"
Original Implementation: D'Angelo, Valimaki

Code obtained via Dimitri Diakopoulos, https://github.com/ddiakopoulos/MoogLadders
Adapted for samplerbox by HansEhv, https://github.com/hansehv/SamplerBox
*/

	
LadderFilter::LadderFilter()
{
	SetsampleRate(44100);
	Mute();
	drive = 1.0f;
	dry = 0.0f;
	wet = 1.0f;
	gain = 4.0f;
		
	//SetCutoff(1000.0f); // normalized cutoff frequency
	//SetResonance(0.1f); // [0, 4]
	SetCutoff(10000.0f); // normalized cutoff frequency
	SetResonance(0.0f); // [0, 4]
	Normalize();
}
	
LadderFilter::~LadderFilter() { }
	
void LadderFilter::SetsampleRate(float s)
{
	sampleRate = s;
	sampleRate2 = 2 * s;
}
	
void LadderFilter::SetResonance(float r)
{
	resonance = r;
}
	
void LadderFilter::Mute()
{
	memset(L_V, 0, sizeof(L_V)); 
	memset(L_dV, 0, sizeof(L_dV));
	memset(L_tV, 0, sizeof(L_tV));	
	memset(R_V, 0, sizeof(R_V));
	memset(R_dV, 0, sizeof(R_dV));
	memset(R_tV, 0, sizeof(R_tV));
}
	
void LadderFilter::SetCutoff(float c)
{
	cutoff = c;
	x = (MOOG_PI * cutoff) / sampleRate;
	g = 4.0 * MOOG_PI * VT * cutoff * (1.0 - x) / (1.0 + x);
}
	
void LadderFilter::SetDrive(float d)
{
	drive = d;
	Normalize();
}
void LadderFilter::SetDry(float o)
{
	dry = o;
}
	
void LadderFilter::SetWet(float w)
{
	wet = w;
	Normalize();
}
	
void LadderFilter::SetGain(float n)
{
	gain = n;
	Normalize();
}
	
void LadderFilter::Normalize()
{
	wetnorm = wet * gain / drive;
}


// --------------- make basic filter callable from from samplerbox ------------

void LadderFilter::MoogLadder(float *inputstream, float *outputstream, int numsamples)
{
	float *inS,*outS,in;
	double dV0, dV1, dV2, dV3;

	inS=inputstream;
	outS=outputstream;

	for (int l=0;l<numsamples;l++)	// direct code to help performance
	{
	// Left
		in = *inS;
		dV0 = -g * (fast_tanh((drive * *inS + resonance * L_V[3]) / VT2) + L_tV[0]);
		L_V[0] += (dV0 + L_dV[0]) / sampleRate2;
		L_dV[0] = dV0;
		L_tV[0] = fast_tanh(L_V[0] / VT2);
		dV1 = g * (L_tV[0] - L_tV[1]);
		L_V[1] += (dV1 + L_dV[1]) / sampleRate2;
		L_dV[1] = dV1;
		L_tV[1] = fast_tanh(L_V[1] / VT2);
		dV2 = g * (L_tV[1] - L_tV[2]);
		L_V[2] += (dV2 + L_dV[2]) / sampleRate2;
		L_dV[2] = dV2;	
		L_tV[2] = fast_tanh(L_V[2] / VT2);
		dV3 = g * (L_tV[2] - L_tV[3]);
		L_V[3] += (dV3 + L_dV[3]) / sampleRate2;
		L_dV[3] = dV3;
		L_tV[3] = fast_tanh(L_V[3] / VT2);
		*outS = L_V[3]*wetnorm + in*dry;
		inS++;
		outS++;

	// Right
		in = *inS;
		dV0 = -g * (fast_tanh((drive * *inS + resonance * R_V[3]) / VT2) + R_tV[0]);
		R_V[0] += (dV0 + R_dV[0]) / sampleRate2;
		R_dV[0] = dV0;
		R_tV[0] = fast_tanh(R_V[0] / VT2);
		dV1 = g * (R_tV[0] - R_tV[1]);
		R_V[1] += (dV1 + R_dV[1]) / sampleRate2;
		R_dV[1] = dV1;
		R_tV[1] = fast_tanh(R_V[1] / VT2);
		dV2 = g * (R_tV[1] - R_tV[2]);
		R_V[2] += (dV2 + R_dV[2]) / sampleRate2;
		R_dV[2] = dV2;	
		R_tV[2] = fast_tanh(R_V[2] / VT2);
		dV3 = g * (R_tV[2] - R_tV[3]);
		R_V[3] += (dV3 + R_dV[3]) / sampleRate2;
		R_dV[3] = dV3;
		R_tV[3] = fast_tanh(R_V[3] / VT2);
		*outS = R_V[3]*wetnorm + in*dry;
		inS++;
		outS++;
	}
}
