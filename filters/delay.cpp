#include "delay.hpp"

delay::delay()
{
	setdelay(10000.0f);
	setfb(0.7f);
	setfw(0.7f);
	setmix(1.0f);
	settype(1);
	setsweep(1.0f,1000.0f);
	d_step=80.0;
	setrange(10.0f,d_step);	
	//setsweep(1.0f,10000.0f);
	//d_step=10.0;
	//setrange(5.0f,d_step);	
	LwrtPtr = &L_buffer[MAX_BUF_SIZE-1];
	RwrtPtr = &R_buffer[MAX_BUF_SIZE-1];
	mute();
}
delay::~delay()
{
}

void delay::setfb(float val)
{
	d_fb = val;
}

void delay::setfw(float val)
{
	d_fw = val;
}

void delay::setmix(float val)
{
	d_mix = val;
}

void delay::setdelay(float n_delay)
{
	/*Protect against overflow = segmentation faults*/
	if (n_delay > MAX_BUF_SIZE-1) {
		n_delay = MAX_BUF_SIZE-1;
	}

	/*Get the integer part of the delay*/
	d_samples = floor(n_delay);

	/*gets the fractional part of the delay*/
	n_fract = (n_delay - d_samples);	
}

void delay::settype(int type){
	switch(type) {
		case 1:
		      flanger=false;
		      break;
		case 2:
		      flanger=true;
		      break;
	}
}

void delay::setsweep(float steepness, float samples) {
	d_stepsize = steepness;
	d_stepsamples = samples;
}

void delay::setrange(float min, float max) {
	d_min = min;
	d_max = max;
}

/*
This sweep function creates a slow frequency
ramp that will go up and down changing the
delay value at the same time. The counter
variable is a counter of amount of samples that 
the function waits before it can change the delay.
*/
void delay::sweep(void) {
	if (!--d_step) {			
		d_var += d_stepdir*d_stepsize;
  
		if (d_var > d_max) {
			d_stepdir = -1;
		} 

		if (d_var < d_min) {
			d_stepdir = 1;
		}

		setdelay(d_var);
		d_step = d_stepsamples;
	}
}

float delay::processchannel(float xin) {
	float yout;
	float * y0; 
	float * y1;
	float x1;
	float x_est;
	
	/*Calculates current read pointer position*/
	rdPtr = wrtPtr - d_samples;
	if (rdPtr < buffer) {
		rdPtr += MAX_BUF_SIZE-1;
	}
	
	/*Linear interpolation to estimate the delay + the fractional part*/
	y0 = rdPtr-1;
	y1 = rdPtr;

	if (y0 < buffer) {
		y0 += MAX_BUF_SIZE-1;
	}

	x_est = (*(y0) - *(y1))*n_fract + *(y1);

	/*Calculate next value to store in buffer*/
	x1 = xin + x_est*d_fb;

	/*Store value in buffer*/
	*(wrtPtr) = x1;
 
	/*Output value calculation*/
	// original: yout = x1*d_mix + x_est*d_fw;
	yout = xin*d_mix + x_est*d_fw;

	/*Increment delay write pointer*/
	wrtPtr++;
	if ((wrtPtr-buffer) > MAX_BUF_SIZE-1) {
		wrtPtr = buffer;
	}

	return yout;
}

void delay::mute()
{
	for (int i = 0; i < MAX_BUF_SIZE; ++i){
		L_buffer[i] = 0.0f;
		R_buffer[i] = 0.0f;
	}
}

// --------------- make basic filter callable from from samplerbox ------------

void delay::DoDelay(float *inputstream, float *outputstream, int numsamples)
{
	float *inS,*outS;

	inS=inputstream;
	outS=outputstream;

	for (int l=0;l<numsamples;l++)
	{
	// Left
		wrtPtr=LwrtPtr;
		buffer=L_buffer;
		*outS = processchannel(*inS);
		LwrtPtr=wrtPtr;
		inS++;
		outS++;

	// Right
		wrtPtr=RwrtPtr;
		buffer=R_buffer;
		*outS = processchannel(*inS);
		RwrtPtr=wrtPtr;
		inS++;
		outS++;

	// Flanger
		if (flanger) {
			sweep();
		}
	}
}
