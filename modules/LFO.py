##################################################################################
# Poor man's Low Frequency Oscillator (LFO), for vibrato, tremolo etc
# Clock can be via (filter)call in AudioCallback, on PI3 approx once per 11msec's
# for a saw=(128 up) or triangle=(128 up+down) a stepsize of 14 gives ~10Hz/5Hz respectively
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
##################################################################################
LFOblock=0      # index values for readability, don't change
LFOsaw=1
LFOinvsaw=2
LFOtriangle=3
class plfo:
    def __init__(self, step=14, block=127, saw=127):
        self.step=step; 
        self.values=[0.0,0.0,0.0,0.0]
        if block<64:self.values[LFOblock]=-1
        else: self.values[LFOblock]=1
        self.values[LFOsaw]=saw
        self.values[LFOinvsaw]=127-self.values[LFOsaw]
        if self.values[LFOblock]>1: LFOself.values[LFOtriangle]=self.values[LFOsaw]
        else: self.values[LFOtriangle]=127-self.values[LFOsaw]
    def process(self):
        self.values[LFOsaw]+=self.step
        if self.values[LFOsaw]<-1: self.values[LFOsaw]=128 # stop infinite loop due to impossible values
        if self.values[LFOsaw]>127:
            self.values[LFOblock]*=-1
            self.values[LFOsaw]=0
        self.values[LFOinvsaw]=127-self.values[LFOsaw]
        if self.values[LFOblock]>0:
            self.values[LFOtriangle]=self.values[LFOsaw]
        else:
            self.values[LFOtriangle]=self.values[LFOinvsaw]
    def setstep(self,x):
        if x>0: self.step=x
    def setblock(self,x):
        if x<64: self.values[LFOblock]=-1
        else: self.values[LFOblock]=1
    def setsaw(self,x):
        self.values[LFOsaw]=x
    def setinvsaw(self,x):
        self.values[LFOsaw]=(127-x)
    def settriangle(self,x):     # -127 to 127, values below 0 mean the second=decreasing stage
        if x<0:
            self.values[LFOblock]=-1
            self.values[LFOsaw]=(127+x)
        else:
            self.values[LFOblock]=1
            self.values[LFOsaw]=x
    def getblock(self):
        return (self.values[LFOblock]+1)*64     # so return 0 or 127
    def getsaw(self):
        return self.values[LFOsaw]
    def getinvsaw(self):
        return self.values[LFOinvsaw]
    def gettriangle(self):
        return self.values[LFOtriangle]
