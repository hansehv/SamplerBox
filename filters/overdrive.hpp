/* written for samplerbox by: https://github.com/hansehv/SamplerBox
 * 
 * Softclip followed by a simplistic low-pass filter, giving an overdrive effect
 * 
   Inspired by:
   * https://ses.library.usyd.edu.au/bitstream/handle/2123/7624/DESC9115_DAS_Assign02_310106370.pdf;jsessionid=2685F64A8E26618DE4C66FCA7DBCCF72?sequence=2
   * https://www.musicdsp.org/en/latest/Effects/104-variable-hardness-clipping-function.html
   * https://dsp.stackexchange.com/questions/60277/is-the-typical-implementation-of-low-pass-filter-in-c-code-actually-not-a-typica
   * https://dsp.stackexchange.com/questions/1004/low-pass-filter-in-non-ee-software-api-contexts/1006#1006
*/

class overdrive {

public:
    overdrive();
    ~overdrive();

    void set_boost(float val);      //  15 - 65
    void set_drive(float val);      //  1 - 11
    void set_tone(float val);       //  0 - 0.95
    void set_wet(float val);        //  0 - 1
    void set_dry(float val);        //  0 - 1
    void process(float *inputstream, float *outputstream, int numsamples);

private:
    float wet;				/* percentage of effect mixed in, ....*/
    float dry;				/* .....coupled to level of original  */
    float boost; 			/* the gain of the input signal */
    float drive; 			/* the distortion level */
    float tone; 			/* the low-pass filter threshold of the distorted signal */
	float lastLeft;		    /* last computed left channel */
	float lastRight;		/* last computed right channel */
	float drinv;			/* inversed distortionlevel with range correction */
    
    float fastatan (float val);
    float softclip (float val);

};
