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


# Test Run

    years =  [2020,2021,2022]
    coalPlants = ["C1","C2"]
    rePlants = ["R1","R2"]

    declaring sets
    R = rePlants
    C = coalPlants
    Y = years
    
# Run 1 
### (Alpha = 1, Beta = 0, Gamma = 0)
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

