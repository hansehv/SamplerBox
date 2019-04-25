// originals by Gabriel Rivas:  https://www.dsprelated.com/showcode/58.php
//                              https://www.dsprelated.com/showcode/166.php
// rewritten for samplerbox by: https://github.com/hansehv/SamplerBox

/*****************************************************************************
*       Fractional delay line implementation in C:
*             ------------------>[d_mix]--------------------
*            |                                              |
*     xin -->|                                              |
*            |                                              v
*             ---->[+]--->[z^-M]--[interp.]-----[d_fw]---->[+]---> yout 
*                   ^                        |  
*                   |                        |
*                    ---------[d_fb]<--------   
*****************************************************************************/

#include "cmath"
#define MAX_BUF_SIZE 64000

class delay {
public:
	delay();
	~delay();

	void setfb(float val);
	void setfw(float val);
	void setmix(float val);
	void settype(int type);
	void mute();
	void DoDelay(float *inputstream, float *outputstream, int numsamples);
	/* echo specific */
	void setdelay(float val);
	/* flanger specific*/
	void setsweep(float steepness, float samples);
	void setrange(float min, float max);

private:
	float processchannel(float xin);
	void sweep(void); /* flanger specific*/

	float L_buffer[MAX_BUF_SIZE];
	float R_buffer[MAX_BUF_SIZE];
	float *buffer;

	float d_mix;		/*delay blend parameter*/
	int   d_samples;	/*delay duration in samples*/
	float d_fb;		/*feedback volume*/
	float d_fw;		/*delay tap mix volume*/
	float n_fract;		/*fractional part of the delay*/
	float *LwrtPtr;		/*left write pointer*/
	float *RwrtPtr;		/*right write pointer*/
	float *rdPtr;		/*task read pointer*/
	float *wrtPtr;		/*task write pointer*/
	/* flanger specific*/
	bool flanger;		/* either true or false :-) */
	float d_var;		/* variable delay */
	float d_min;		/* min value of var delay */
	float d_max;		/* max value of var delay */
	float d_step;		/* step number */
	float d_stepsize;	/* size of change to var delay per step */
	float d_stepsamples;	/* number of samples to take a step */
	float d_stepdir;	/* direction of steps */
};