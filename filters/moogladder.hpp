/*
  Original Implementation: D'Angelo, Valimaki
  Code obtained via Dimitri Diakopoulos, https://github.com/ddiakopoulos/MoogLadders
  adapted for samplerbox by HansEhv, https://github.com/hansehv/SamplerBox
*/

#pragma once

#ifndef LADDER_FILTER_H
#define LADDER_FILTER_H

class LadderFilter
{

// Thermal voltage (26 milliwats at room temperature)
#define VT 0.312
#define VT2 0.624

public:
	
	LadderFilter();
	~LadderFilter();
	
	void MoogLadder(float *inputstream, float *outputstream, int numsamples);
	void SetsampleRate(float s);
	void Mute();
	void SetResonance(float r);
	void SetCutoff(float c);
	void SetDrive(float d);
	void SetDry(float o);
	void SetWet(float w);
	void SetGain(float w);
	
private:
	
	//float Process(float sample);

	float cutoff;
	float resonance;
	float sampleRate;
	float sampleRate2;
	
	double L_V[4];
	double L_dV[4];
	double L_tV[4];
	double R_V[4];
	double R_dV[4];
	double R_tV[4];
	
	double x;
	double g;
	double drive;
	float dry;
	float wet;
	float wetnorm;
	float gain;

	void Normalize();

	inline double fast_tanh(double x) 
	{
		double x2 = x * x;
		return x * (27.0 + x2) / (27.0 + 9.0 * x2);
	}

};

#endif
