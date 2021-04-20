# Equitable Retirement Optimization

Python implementation of the "TITLE" (multi-objective pathways to *more* equitable coal retirements in the Mid-Atlantic region) work by D. Smith, M. Craig, J. Florez, and I. Bromley-Dulfano. 

## Setup:

1. Create and activate a new conda environment:

        conda create --name equity python=3.8
        conda activate equity

2. Install dependencies:

        pip install pyomo
        pip install numpy
        pip install pandas
        conda install glpk --channel conda-forge

# List of tests
1. **Single weight tests**
    * Test only system cost weight: Run 1,2 
    * Test only health weight: Run 3,4
    * Test only jobs weight: Run 5
4. Other detail tests w/ 1 weight:
    * Test max sites implementation: Run 2,4 
    * Test multiple RE & coal plant operations: Run 1-5
6. **Test investment after 1 year (staggered retirement):** Run 6-9
    * Depends on system costs-changing CF:  Run 6
    * Depends on health damages: HD don't change overtime (did not test)
    * Depends on EF factors:
        * Only RE construction EF: Run 7
        * Only RE operation EF: Run 8
        * Combination of all three EFs: Run 9
11. **Two weight tests:**
    * System costs + health weight: Run 10
    * Systems costs + jobs weight: Run 11
    * Health + jobs weight:Run 12
12. **Three weight test:**
    * System cost + health + jobs weight: Run 13


# Test Run (1-5) Dataset

    years =  [2020,2021,2022]
    coalPlants = ["C1","C2"]
    rePlants = ["R1","R2"]

    declaring sets
    R = rePlants
    C = coalPlants
    Y = years

    HISTGEN = [[10,10,10],[10,10,10]] #Two 10 MW coal plants from 2020-2022
    MAXCAP = [20,20] #Two 20 MW RE plants
    CF = [[.25,.25,.25],[.5,.5,.5]] #25% CF for R1 and 50% CF for R2
    CAPEX = [1,2] #R1 cheaper than R2
    REOPEX = [1,2] #R1 cheaper than R2
    COALOPEX = [5,6] #Coal 1 cheaper than coal 2 (however both are more expensive then R1 and R2)
    MAXSITES = [1,2] #1 RE plant available for coal plant 1 and 2 RE plants for coal plant 2
    HD = [10,5] #C1 10 $/MWh while C2 5$/MWh (C1 worse health option then C2)
    RETEF = [1,1] #Constant retirement EFs (COAL 1 RET EFS =COAL 2 RET EFS)
    CONEF = [[1,1,1],[2,2,2]] #R1 lower construction EF then R2
    COALOMEF = [.25,.25] #Coal plant 1 and coal plant 2 have same O&M ratios
    REOMEF = [[.25,.25,.25],[.5,.5,.5]] #R1 lower O&M EF then R2
    
# Run 1 
### (Alpha = 1, Beta = 0, Gamma = 0)
    See dataset in run 1-5

# Run 2
### (Alpha = 1, Beta = 0, Gamma = 0)
All values same in run 1 except MAXSITES:

    MAXSITES = [2,1] #2 RE plant available for coal plant 1 and 1 RE plants for coal plant 2

# Run 3
### (Alpha = 0, Beta = 1, Gamma = 0)
All values same in run 1

# Run 4
### (Alpha = 0, Beta = 1, Gamma = 0)
All values same in run 1 except MAXSITES:

        MAXSITES = [2,2] #2 RE plant available for coal plant 1 and 2 RE plants for coal plant 2

# Run 5
### (Alpha = 0, Beta = 0, Gamma = 1)
All values same in run 1

# Run 6 Dataset
    years =  [2020,2021,2022]
    coalPlants = ["C1","C2"]
    rePlants = ["R1"]

    declaring sets
    R = rePlants
    C = coalPlants
    Y = years

    HISTGEN = [[10,10,10],[10,10,10]] #Two 10 MW coal plants from 2020-2022
    MAXCAP = [20] #One 20 MW RE plant
    CF = [[.4,.75,.75]]#Rising CF for R1
    CAPEX = [1] #R1 CAPEX costs
    REOPEX = [1] #R1 OPEX costs
    COALOPEX = [5,6] #Coal 1 cheaper than coal 2 (however both are more expensive then R1 and R2)
    MAXSITES = [1,2] #1 RE plant available for coal plant 1 and 2 RE plants for coal plant 2
    HD = [10,5] #C1 10 $/MWh while C2 5$/MWh (C1 worse health option then C2)
    RETEF = [1,1] #Constant retirement EFs (COAL 1 RET EFS =COAL 2 RET EFS)
    CONEF = [[1,1,1]] #R1 construction EF
    COALOMEF = [.5,.5] #Coal plant 1 and coal plant 2 have same O&M ratios
    REOMEF = [[.25,.25,.25]] #R1 O&M EFs

# Run 6
### (Alpha = 1, Beta = 0, Gamma = 0)
Dataset from run 6

# Run 7
### (Alpha = 0, Beta = 0, Gamma = 1)
Updated dataset:-should build plant on year 2 to take advantage of construction EF

    HISTGEN = [[10,10,10],[10,10,10]] #Two 10 MW coal plants from 2020-2022
    MAXCAP = [20] #One 20 MW RE plant
    CF = [[.4,.75,.75]]#Rising CF for R1
    CAPEX = [1] #R1 CAPEX costs
    REOPEX = [1] #R1 OPEX costs
    COALOPEX = [5,6] #Coal 1 cheaper than coal 2 (however both are more expensive then R1 and R2)
    MAXSITES = [1,2] #1 RE plant available for coal plant 1 and 2 RE plants for coal plant 2
    HD = [10,5] #C1 10 $/MWh while C2 5$/MWh (C1 worse health option then C2)
    RETEF = [0,0] #Constant retirement EFs (COAL 1 RET EFS =COAL 2 RET EFS)
    CONEF = [[.1,1,.1]] #R1 construction EF
    COALOMEF = [.5,.5] #Coal plant 1 and coal plant 2 have same O&M ratios
    REOMEF = [[0,0,0]] #R1 O&M EFs

# Run 8
### (Alpha = 0, Beta = 0, Gamma = 1)
Same dataset from run 7 up until bottom portion (see code below):

    CONEF = [[0,0,0]] #R1 construction EF
    COALOMEF = [.5,.5] #Coal plant 1 and coal plant 2 have same O&M ratios
    REOMEF = [[0,10,10]] #R1 O&M EFs

# Run 9
### (Alpha = 0, Beta = 0, Gamma = 1)
Same dataset from run 7 up until bottom portion (see code below):

    RETEF = [1,1] #Constant retirement EFs (COAL 1 RET EFS =COAL 2 RET EFS)
    CONEF = [[.1,.5,.1]] #R1 construction EF
    COALOMEF = [.5,.5] #Coal plant 1 and coal plant 2 have same O&M ratios
    REOMEF = [[.25,.2,.2]] #R1 O&M EFs

# Run 10
### (Alpha = 1, Beta = .5, Gamma = 0)
Same dataset from run 7 up

# Run 11
### (Alpha = 1, Beta = 0, Gamma = 0.5)
Same dataset from run 7

# Run 12
### (Alpha = 0, Beta = 1, Gamma = 0.5)
Same dataset from run 7

# Run 13
### (Alpha = .5, Beta = 1, Gamma = .5)
Same dataset from run 7
