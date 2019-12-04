import numpy as np
import matplotlib.pyplot as plt
import os

def rateFunction(r0,totTime):
    lst=[[0,0.2,-1.65],[0.2,0.4,-1.44],[0.4,0.6,-1.34],[0.6,0.8,-1.15],[0.8,1.0,-0.9],[1.0,1.2,-0.85],[1.2,1.7,-0.85],[1.7,2.5,-0.62],[2.5,3.5,-0.86],[3.5,4.5,-1.37]]
    '''
    Define the change of rate with time
    -r0 is the present rate in events/Myr
    -rAvg is the average rate in events/Myr
    -totTime is the total simulation time in Myr before present
    '''
    def rate(t):
        
            
        z=(((28000/(14000-totTime+t))-1)**0.5)-1
        for i in lst:
            if i[0]<=z and i[1]>=z:
                return 10**i[2]*r0/10**(-1.65)
    
    return rate

class SimulationObj():
    '''
    The instantiation values for this class should be:

    -alpha: the mixing lenght parameter
    -vt: the turbulent velocity (in km/s)
    -hscale: the height scale (in kpc)
    -circumf: the total circle length considered (in kpc)
    -width: the circle width (in kpc)
    -time: the total time of the simulation (in Myr)
    '''

    def __init__(self, alpha, vt, hscale, circumf, width, time):
        '''Initialization function'''
        
        # Calculate diffusion coefficient in kpc^2/Myr
        self.diff = alpha*vt/7*hscale/0.2*1e-3
        
        # Keep everything else the same
        self.hscale = hscale
        self.circumf = circumf
        self.width = width
        self.timeMyr = time
    
    def runSimulation(self, tau, rateFunc, sampleDt):
        
        '''Generate the events according to the parameters
        introduced by the user and the rate function'''
        
        # Get the simulation timepoints
        simulTime = np.arange(0, self.timeMyr + sampleDt, sampleDt)
        lenSimulTime = len(simulTime)
        simulOutpt = np.zeros(lenSimulTime)
        
        # Get the random events
        
        # For each Myr, produce R events randomly distributed in
        # said Myr:
        tt = 0; times = []; distances = []
        tempSampleDt = sampleDt
        while tt < self.timeMyr:
            nEvents = int(np.round(rateFunc(tt)*tempSampleDt))
            
            # Check that the number of events changes meaningfully
            tempSampleDt = sampleDt
            while tt + tempSampleDt < self.timeMyr:
                nEvents = int(np.round(rateFunc(tt)*tempSampleDt))
                futureNEvents = int(np.round(rateFunc(tt +
                                                 tempSampleDt)*tempSampleDt))
                if nEvents != futureNEvents:
                    break
                tempSampleDt *= 10
            
            # Limit maximum time of events
            if tt + tempSampleDt > self.timeMyr:
                tempSampleDt = self.timeMyr - tt
                nEvents = int(np.round(rateFunc(tt)*tempSampleDt))
            
            # Get the times
            times = np.append(times,
                    np.sort(tempSampleDt*np.random.random(nEvents)) + tt)
            
            # Get positions
            xx = self.circumf*np.random.random(nEvents) - 0.5*self.circumf
            yy = self.width*np.random.random(nEvents) - 0.5*self.width
            zz = np.random.laplace(0, self.hscale, nEvents)
            
            # Calculate the distances from origin
            distances = np.append(distances, np.sqrt(xx**2 + yy**2 + zz**2))
            
            tt += tempSampleDt
        
        jj = 0
        # Update all values
        for ii in range(len(times)):
            if times[ii] > simulTime[jj]:
                jj += 1
                if jj > lenSimulTime - 1:
                    break
            
            dt = simulTime[jj:] - times[ii]
            r2 = self.diff*dt
            
            dilution = np.exp(-distances[ii]**2/(4*r2) - dt/tau)
            dilution /= np.minimum((4*np.pi*r2)**1.5, 8*np.pi*self.hscale*r2)
            
            simulOutpt[jj:] += dilution
        
        return simulTime, simulOutpt
    
def main():
    '''Toy simulation from Hotokezaka2015'''
    
    # Check that input file exists
    inFile = "inputToy.in"
    inExample = "inputToy.example"
    if not os.path.isfile(inFile):
        s = 'File "{}" not found, '.format(inFile)
        s += 'please use "{}" as a template'.format(inExample)
        print(s)
        return 1
    
    # Read input file
    inputArgs = {}
    with open(inFile, "r") as fread:
        for line in fread:
            lnlst = line.split()
            
            # Ignore comments and empty lines
            if len(lnlst) == 0 or lnlst[0] == "#":
                continue
            
            # Fill all the arguments
            val = float(lnlst[0]); key = lnlst[1]
            inputArgs[key] = val
    
    # Check at least correct number of arguments
    if len(inputArgs) < 10:
        s = 'File "{}" has an incorrect number of entries, '.format(inFile)
        s += 'please use "{}" as a template'.format(inExample)
        print(s)
        return 1
    
    # Calculate the solar circumference
    circumf = inputArgs["rSun"]*2*np.pi
    
    # Calculate the simulation fractional mass by approximating:
    # dM = dr*rsun*exp(-rsun/rd)/(rd*rd)
    rScaleSun = inputArgs["rSun"]/inputArgs["rd"]
    
    fraction = np.exp(-rScaleSun)*rScaleSun
    fraction *= inputArgs["width"]/inputArgs["rd"]
    
    # Get the rate
    r0 = inputArgs["r0"]*fraction
    rate = rateFunction(r0,inputArgs["time"])
    # Set tau (in Myr)
    tau = inputArgs["tau"]
    
    # Set sample Dt (in Myr)
    sampleDt = inputArgs["sampleDt"]
    
    # Initialize and run simulation
    simul = SimulationObj(alpha = inputArgs["alpha"],
                          vt = inputArgs["vt"],
                          hscale = inputArgs["hscale"],
                          circumf = circumf,
                          width = inputArgs["width"],
                          time = inputArgs["time"])
    
    simulTime, simulOutpt = simul.runSimulation(tau, rate, sampleDt)

    # Plot results
    lowTime = 2000
    for ii in range(len(simulTime)):
        if simulTime[ii] >= lowTime:
            break
    
    plt.plot(simulTime[ii:], simulOutpt[ii:])
    plt.yscale("log")
    
    plt.xlabel("Time (Myr)")
    plt.ylabel("Mass (Normalized)")
    plt.show()

if __name__ == "__main__":
    main()
