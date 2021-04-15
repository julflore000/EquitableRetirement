import pyomo.environ as pe
import pyomo.opt
import numpy as np 
import pandas as pd
from datetime import datetime
import csv


class EquitableRetirement:
    class Params:
        def __init__(self):
            # parameters
            self.HISTGEN = None 
            self.CF = None 
            self.CAPEX = None  
            self.REOPEX = None
            self.COALOPEX = None 
            self.MAXCAP = None 
            self.MAXSITES = None
            self.HD = None
            self.RETEF = None
            self.CONEF = None
            self.COALOMEF = None
            self.REOMEF = None

    class Output:
        def __init__(self):
            pass

    def __init__(self):
        # sets
        self.Y = None
        self.C = None
        self.R = None 

        self.Params = EquitableRetirement.Params()
        self.Output = EquitableRetirement.Output()
   
    def __buildModel(self,alpha,beta,gamma):
    
        ######### helper function ##########

        def a2d(data, *sets): 
            '''
            This function converts 1 or 2 dimension arrays into dictionaries compatible with pyomo set/param initializers
            '''
            if isinstance(data, pd.Series):
                data = data.values
            if isinstance(data, int):
                data = [data]
            if isinstance(data, list):
                data = np.array(data)

            assert(data.ndim <= 2)

            # direct indexing
            if len(sets) == 0:
                if data.ndim == 1:
                    return {i:data[i] for i in range(len(data))}
                else:
                    return {(i,j):data[i,j] for i in range(len(data[:,0])) for j in range(len(data[0,:]))}

            # otherwise use sets
            assert(len(sets) == data.ndim)

            if data.ndim == 1:
                return {sets[0][i]:data[i] for i in range(len(data))}

            if data.ndim == 2:
                return {(sets[0][i],sets[1][j]):data[i,j] for i in range(len(sets[0])) for j in range(len(sets[1]))} 
        
        ############ end helper ############

        self.NUM_RE = len(self.R)
        self.NUM_COAL = len(self.C)
        self.NUM_YEARS = len(self.Y)
        
        # fill model 
        model = pe.ConcreteModel()

        # sets 
        model.Y = pe.Set(initialize=self.Y, doc = "Years of program") 
        model.C = pe.Set(initialize=self.C, doc = "Coal Plant IDs")
        model.R = pe.Set(initialize=self.R, doc='Renewable plant locations with type of technology (wind or solar)')

        # parameters
        model.HISTGEN = pe.Param(model.C, model.Y, initialize=a2d(self.Params.HISTGEN,self.C,self.Y), doc = "Historical Generation of coal plants")
        model.CF = pe.Param(model.R, model.Y, initialize=a2d(self.Params.CF,self.R,self.Y),doc = "Hourly CF of each RE location")
        model.CAPEX = pe.Param(model.R, initialize=a2d(self.Params.CAPEX,self.R),doc = "RE plants CAPEX values ($/MW")
        model.REOPEX = pe.Param(model.R, initialize=a2d(self.Params.REOPEX,self.R),doc = "RE plants OPEX values ($/MWh")
        model.COALOPEX = pe.Param(model.C, initialize=a2d(self.Params.COALOPEX,self.C), doc = "Coal plants OPEX values $/MWh")
        model.MAXCAP = pe.Param(model.R,initialize=a2d(self.Params.MAXCAP,self.R), doc ='Maximum capacity for RE plant at the site')
        model.MAXSITES = pe.Param(model.C,initialize=a2d(self.Params.MAXSITES,self.C), doc = "Number of Sites allowable to replace coal plant")
        model.HD = pe.Param(model.C,initialize=a2d(self.Params.HD,self.C), doc="Health damages of each coal plant")
        model.RETEF = pe.Param(model.C,initialize=a2d(self.Params.RETEF,self.C), doc="Retirement EF for each coal plant (will most likely be a single static value)")
        model.CONEF = pe.Param(model.R,model.Y,initialize=a2d(self.Params.CONEF,self.R,self.Y),doc="Construction/installation EFs for RE plants")
        model.COALOMEF = pe.Param(model.C,initialize=a2d(self.Params.COALOMEF,self.C),doc="O&M EF for coal plants (will be most likely be a static value as well)")
        model.REOMEF = pe.Param(model.R,model.Y,initialize=a2d(self.Params.REOMEF,self.R,self.Y),doc="O&M EF for RE plants")

        # variables
        model.capInvest = pe.Var(model.R,model.C,model.Y,within=pe.NonNegativeReals, doc = "Capacity to be invested in that renewable plant to replace coal")
        model.capRetire = pe.Var(model.C,model.Y,within=pe.NonNegativeReals,doc = "amount of capacity to be retired for each coal plant")
        model.coalGen = pe.Var(model.C,model.Y,within=pe.NonNegativeReals, doc = "Coal generation for each plant")
        model.reGen = pe.Var(model.R,model.C,model.Y,within=pe.NonNegativeReals, doc = "RE generation at each plant")
        model.reCap = pe.Var(model.R,model.C,model.Y,within=pe.NonNegativeReals, doc = "Capacity size for each RE plant")
        model.reInvest = pe.Var(model.R,model.C,model.Y,within=pe.Binary, doc = "Binary variable to invest in RE to replace coal")
        model.coalRetire = pe.Var(model.C,model.Y,within=pe.Binary, doc = "Binary variable to retire coal plant")
        model.reOnline = pe.Var(model.R,model.C,model.Y,within=pe.Binary, doc = "Binary variable of whether the RE plant is on (1) or off (0)")
        model.coalOnline = pe.Var(model.C,model.Y,within=pe.Binary, doc = "Binary variable of whether the coal plant is on (1) or off (0)")

        # objective
        def SystemCosts(model):
            return sum(sum(sum(model.CAPEX[r] * model.capInvest[r,c,y] for c in model.C) for r in model.R)for y in model.Y) \
                + sum(sum(model.COALOPEX[c]*model.coalGen[c,y] for c in model.C) for y in model.Y)

        def HealthCosts(model):
            return sum(sum(model.HD[c]*model.coalGen[c,y] for c in model.C) for y in model.Y)

        def Jobs(model):
            #first is operation EFs dependent on coalGeneration and O&M EF
            #second is coal retirement factors 
            return sum(sum(model.RETEF[c]*model.capRetire[c,y] + model.COALOMEF[c]*model.coalGen[c,y] for c in model.C) for y in model.Y) \
                + sum(sum(sum(model.CONEF[r,y]*model.capInvest[r,c,y] + model.REOMEF[r,y]*model.reGen[r,c,y] for c in model.C) for r in model.R) for y in model.Y)

        def Z(model):
            return alpha*SystemCosts(model) + beta*HealthCosts(model) - gamma*Jobs(model)
        model.Z = pe.Objective(rule=Z, doc='Minimize system costs, health damages, while maximizing jobs')

        # constraints
        def coalGenRule(model,c,y):
            return model.coalGen[c,y] == model.HISTGEN[c,y]*model.coalOnline[c,y]
        model.coalGenRule = pe.Constraint(model.C,model.Y,rule=coalGenRule, doc='Coal generation must equal historical generation * whether that plant is online')

        def balanceGenRule(model,c,y):
            return sum(model.reGen[r,c,y] for r in model.R) == model.HISTGEN[c,y]-model.coalGen[c,y]
        model.balanceGenRule = pe.Constraint(model.C,model.Y,rule=balanceGenRule, doc = "RE generation for each coal location must equal retired capacity")

        def reGenRule(model,r,c,y):
            return model.reGen[r,c,y] <= model.CF[r,y]*model.reCap[r,c,y]
        model.reGenRule = pe.Constraint(model.R,model.C,model.Y,rule=reGenRule, doc='RE generation must be less than or equal to capacity factor* chosen capacity')

        def reCapRule(model,r,c,y):
            return model.reCap[r,c,y] <= model.MAXCAP[r]*model.reOnline[r,c,y]
        model.reCapRule = pe.Constraint(model.R,model.C,model.Y,rule=reCapRule, doc = "RE capacity decision variable should be less then or equal to max capacity* whether RE plant is online")

        def reCapLimit(model,r,y):
            return sum(model.reCap[r,c,y] for c in model.C) <= model.MAXCAP[r]
        model.reCapLimit = pe.Constraint(model.R,model.Y,rule=reCapLimit, doc = "RE plants can not overcount towards multiple coal generators (sum of RE plant contribution to each coal plant <= max cap of RE plant)")

        def capInvestRule(model,r,c,y):
            if y == model.Y[1]:
                return model.capInvest[r,c,y] == model.reCap[r,c,y]
            #else
            return model.capInvest[r,c,y] == model.reCap[r,c,y] - model.reCap[r,c,y-1]
        model.capInvestRule = pe.Constraint(model.R,model.C,model.Y,rule=capInvestRule, doc = "RE capacity to invest must be equal to difference in RE cap across years")

        def capInvestLimit(model,r,c,y): ## MAYBE DELETE
            return model.capInvest[r,c,y] <= model.MAXCAP[r]*model.reInvest[r,c,y]
        model.capInvestLimit = pe.Constraint(model.R,model.C,model.Y,rule=capInvestLimit, doc = "RE capacity to invest must be less than or equal to max cap * whether we invest or not")

        
        def reInvestRule(model,r,c,y):
            if y == model.Y[1]:
                return model.reInvest[r,c,y] == model.reOnline[r,c,y]
            #else
            return model.reInvest[r,c,y] == model.reOnline[r,c,y] - model.reOnline[r,c,y-1]
        model.reInvestRule = pe.Constraint(model.R,model.C,model.Y,rule=reInvestRule,doc= "Decision to invest in RE is current year - prior")

        def reInvestLimit(model,c,y):
            return sum( model.reInvest[r,c,y] for r in model.R) <= model.MAXSITES[c] * model.coalRetire[c,y]
        model.reInvestLimit = pe.Constraint(model.C,model.Y,rule=reInvestLimit,doc = "Number of new RE sites must be less than or equal to max RE sites for that coal plant * whether we retire")

        def coalRetireRule(model,c,y):
            if y == model.Y[1]:
                return model.coalRetire[c,y] == 1 - model.coalOnline[c,y]
            #else
            return model.coalRetire[c,y] == model.coalOnline[c,y-1] - model.coalOnline[c,y]
        model.coalRetireRule = pe.Constraint(model.C,model.Y,rule=coalRetireRule, doc = "Coal retire activation is current year must prior year")

        def coalRetireLimit(model,c):
            return sum(model.coalRetire[c,y] for y in model.Y) <= 1
        model.coalRetireLimit = pe.Constraint(model.C,rule=coalRetireLimit, doc = "Can only retire a coal plant once over time period")

        def coalCapRetire(model,c,y):
            if y == model.Y[1]:
                return model.capRetire[c,y] == sum(model.reGen[r,c,y] for r in model.R)
            #else
            return model.capRetire[c,y]  == sum(model.reGen[r,c,y-1]-model.reGen[r,c,y] for r in model.R)
        model.coalCapRetire = pe.Constraint(model.C,model.Y,rule=coalCapRetire, doc = "Coal capacity retired is equal to change in re generation at that coal plant")

        self.model = model

    def solve(self,alpha,beta,gamma):
        """Solve the equitable retirement optimization problem. 
        PRECONDITION: All sets and params have been initialized.
        Args:
            alpha ([float or int]): System costs weight
            beta ([float or int]): Health costs weight
            gamma ([float or int]): Job costs weight
        """
        #rebuild model
        self.__buildModel(alpha,beta,gamma)

        opt = pyomo.opt.SolverFactory('glpk')
        results = opt.solve(self.model)
        results.write()
        # extract
        self.__extractResults()
        self.saveResults(alpha,beta,gamma)

    def __extractResults(self):
        self.Output.Z = round(pe.value(self.model.Z),2)
        self.Output.capInvest = np.array([[[pe.value(self.model.capInvest[r,c,y]) for y in self.Y] for c in self.C] for r in self.R])
        self.Output.capRetire = np.array([[pe.value(self.model.capRetire[c,y]) for y in self.Y] for c in self.C])
        self.Output.reGen = np.array([[[pe.value(self.model.reGen[r,c,y]) for y in self.Y] for c in self.C] for r in self.R])
        self.Output.coalGen = np.array([[pe.value(self.model.coalGen[c,y]) for y in self.Y] for c in self.C])
        self.Output.reCap = np.array([[[pe.value(self.model.reCap[r,c,y]) for y in self.Y] for c in self.C] for r in self.R])
        self.Output.reInvest = np.array([[[pe.value(self.model.reInvest[r,c,y]) for y in self.Y] for c in self.C] for r in self.R])
        self.Output.coalRetire = np.array([[pe.value(self.model.coalRetire[c,y]) for y in self.Y] for c in self.C])
        self.Output.reOnline = np.array([[[pe.value(self.model.reOnline[r,c,y]) for y in self.Y] for c in self.C] for r in self.R])
        self.Output.coalOnline = np.array([[pe.value(self.model.coalOnline[c,y]) for y in self.Y] for c in self.C])
        pass
    def saveResults(self,alpha,beta,gamma):

        excelDict = dict()
        excelDict["Alpha (system costs weight)"] = alpha
        excelDict["Beta (health weight)"] = beta
        excelDict["Gamma (jobs weight)"] = gamma
        excelDict["Total objective costs:"] = self.Output.Z
        excelDict["Cap retire"] = self.Output.capRetire  
        excelDict["Cap Invest"] = self.Output.capInvest
        excelDict["RE Cap"] = self.Output.reCap
        excelDict["Re Gen"] = self.Output.reGen
        excelDict["Coal Gen"] = self.Output.coalGen
        excelDict["RE Invest"] = self.Output.reInvest
        excelDict["Coal Retire"] = self.Output.coalRetire
        excelDict["RE online"] = self.Output.reOnline
        excelDict["Coal online"] = self.Output.coalOnline
        
        df = pd.DataFrame(list(excelDict.items())) 
        fileName = f"alpha_{alpha}_beta_{beta}_gamma_{gamma}.xlsx"
        df.to_excel(fileName)
def test():
    ##### SAMPLE DATA #####
    numYears = 3
    numCoal = 4
    numRE = 6

    
    R = np.arange(numRE)
    C = np.arange(numCoal)*11 + 11
    Y = np.arange(numYears) + 2020
    
    HISTGEN = np.ones((numCoal,numYears))*100
    CF = np.ones((numRE,numYears))*.5
    CAPEX = np.arange(numRE)
    REOPEX = numRE - np.arange(numRE)
    COALOPEX = np.arange(numCoal)*100
    MAXCAP = np.ones(numRE)*1000
    MAXSITES = np.ones(numCoal) *10
    HD = numCoal-np.arange(numCoal)
    RETEF = np.arange(numCoal)*.5
    CONEF = np.ones((numRE,numYears))*.5
    COALOMEF = numCoal-np.arange(numCoal)
    REOMEF = numRE-np.ones((numRE,numYears))*.5
    
    ######################

    m = EquitableRetirement()
    m.R = R
    m.Y = Y
    m.C = C
    m.Params.HISTGEN = HISTGEN
    m.Params.CF = CF
    m.Params.CAPEX = CAPEX
    m.Params.REOPEX = REOPEX
    m.Params.COALOPEX = COALOPEX
    m.Params.MAXCAP = MAXCAP
    m.Params.MAXSITES = MAXSITES 
    m.Params.HD = HD
    m.Params.RETEF = RETEF
    m.Params.CONEF = CONEF
    m.Params.COALOMEF = COALOMEF 
    m.Params.REOMEF = REOMEF 

    m.solve(1,1,0)
def runTests():
    years =  [2020,2021,2022]
    coalPlants = ["C1","C2"]
    rePlants = ["R1","R2"]
    ##### SAMPLE DATA Run #####
    numYears = len(years)
    numCoal = len(coalPlants)
    numRE = len(rePlants)
    
    #weights
    alpha = 0 #system costs weight
    beta = 0 #health weight
    gamma = 1 #jobs weight
    
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
    
    ######################

    m = EquitableRetirement()
    m.R = R
    m.Y = Y
    m.C = C
    m.Params.HISTGEN = HISTGEN
    m.Params.CF = CF
    m.Params.CAPEX = CAPEX
    m.Params.REOPEX = REOPEX
    m.Params.COALOPEX = COALOPEX
    m.Params.MAXCAP = MAXCAP
    m.Params.MAXSITES = MAXSITES 
    m.Params.HD = HD
    m.Params.RETEF = RETEF
    m.Params.CONEF = CONEF
    m.Params.COALOMEF = COALOMEF 
    m.Params.REOMEF = REOMEF 

    m.solve(alpha,beta,gamma)
def main():
    pass

if __name__ == '__main__':
    runTests()
    print("done with program!")
