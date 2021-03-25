import pyomo.environ as pe
import pyomo.opt
import numpy as np 
import pandas as pd

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
        model.Y = pe.Set(initialize=self.Y) 
        model.C = pe.Set(initialize=self.C)
        model.R = pe.Set(initialize=self.R)

        # parameters
        model.HISTGEN = pe.Param(model.C, model.Y, initialize=a2d(self.Params.HISTGEN,self.C,self.Y))
        model.CF = pe.Param(model.R, model.Y, initialize=a2d(self.Params.CF,self.R,self.Y))
        model.CAPEX = pe.Param(model.R, initialize=a2d(self.Params.CAPEX,self.R))
        model.REOPEX = pe.Param(model.R, initialize=a2d(self.Params.REOPEX,self.R))
        model.COALOPEX = pe.Param(model.C, initialize=a2d(self.Params.COALOPEX,self.C))
        model.MAXCAP = pe.Param(model.R,initialize=a2d(self.Params.MAXCAP,self.R))
        model.MAXSITES = pe.Param(model.C,initialize=a2d(self.Params.MAXSITES,self.C))
        model.HD = pe.Param(model.C,initialize=a2d(self.Params.HD,self.C))
        model.RETEF = pe.Param(model.C,initialize=a2d(self.Params.RETEF,self.C))
        model.CONEF = pe.Param(model.R,initialize=a2d(self.Params.CONEF,self.R))
        model.COALOMEF = pe.Param(model.C,initialize=a2d(self.Params.COALOMEF,self.C))
        model.REOMEF = pe.Param(model.R,initialize=a2d(self.Params.REOMEF,self.R))

        # variables
        model.capInvest = pe.Var(model.R,model.C,model.Y,within=pe.NonNegativeReals)
        model.capRetire = pe.Var(model.C,model.Y,within=pe.NonNegativeReals)
        model.coalGen = pe.Var(model.C,model.Y,within=pe.NonNegativeReals)
        model.reGen = pe.Var(model.R,model.C,model.Y,within=pe.NonNegativeReals)
        model.reCap = pe.Var(model.R,model.C,model.Y,within=pe.NonNegativeReals)
        model.reInvest = pe.Var(model.R,model.C,model.Y,within=pe.Binary)
        model.coalRetire = pe.Var(model.C,model.Y,within=pe.Binary)
        model.reOnline = pe.Var(model.R,model.C,model.Y,within=pe.Binary)
        model.coalOnline = pe.Var(model.C,model.Y,within=pe.Binary)

        # objective 
        def SystemCosts(model):
            return sum(sum(sum(model.CAPEX[r] * model.capInvest[r,c,y] for c in model.C) for r in model.R)for y in model.Y) \
                + sum(sum(model.COALOPEX[c]*model.coalGen[c,y] for c in model.C) for y in model.Y)

        def HealthCosts(model):
            return sum(sum(model.HD[c]*model.coalGen[c,y] for c in model.C) for y in model.Y)

        def Jobs(model):
            return sum(sum(model.RETEF[c]*model.capRetire[c,y] + model.COALOMEF[c]*model.coalGen[c,y] for c in model.C) for y in model.Y) \
                + sum(sum(sum(model.CONEF[r]*model.capInvest[r,c,y] + model.REOMEF[r]*model.reGen[r,c,y] for c in model.C) for r in model.R) for y in model.Y)

        def Z(model):
            return alpha*SystemCosts(model) + beta*HealthCosts(model) - gamma*Jobs(model)
        model.Z = pe.Objective(rule=Z)

        # constraints
        def coalGenRule(model,c,y):
            return model.coalGen[c,y] == model.HISTGEN[c,y]*model.coalOnline[c,y]
        model.coalGenRule = pe.Constraint(model.C,model.Y,rule=coalGenRule)

        def balanceGenRule(model,c,y):
            return sum(model.reGen[r,c,y] for r in model.R) == model.HISTGEN[c,y]-model.coalGen[c,y]
        model.balanceGenRule = pe.Constraint(model.C,model.Y,rule=balanceGenRule)

        def reGenRule(model,r,c,y):
            return model.reGen[r,c,y] <= model.CF[r,y]*model.reCap[r,c,y]
        model.reGenRule = pe.Constraint(model.R,model.C,model.Y,rule=reGenRule)

        def reCapRule(model,r,c,y):
            return model.reCap[r,c,y] <= model.MAXCAP[r]*model.reOnline[r,c,y]
        model.reCapRule = pe.Constraint(model.R,model.C,model.Y,rule=reCapRule)

        def reCapLimit(model,r,y):
            return sum(model.reCap[r,c,y] for c in model.C) <= model.MAXCAP[r]
        model.reCapLimit = pe.Constraint(model.R,model.Y,rule=reCapLimit)

        def capInvestRule(model,r,c,y):
            if y == model.Y[1]:
                return model.capInvest[r,c,y] == model.reCap[r,c,y]
            #else
            return model.capInvest[r,c,y] == model.reCap[r,c,y] - model.reCap[r,c,y-1]
        model.capInvestRule = pe.Constraint(model.R,model.C,model.Y,rule=capInvestRule)

        def capInvestLimit(model,r,c,y): ## MAYBE DELETE
            return model.capInvest[r,c,y] <= model.MAXCAP[r]*model.reInvest[r,c,y]
        model.capInvestLimit = pe.Constraint(model.R,model.C,model.Y,rule=capInvestLimit)

        def reInvestRule(model,r,c,y):
            if y == model.Y[1]:
                return model.reInvest[r,c,y] == model.reOnline[r,c,y]
            #else
            return model.reInvest[r,c,y] == model.reOnline[r,c,y] - model.reOnline[r,c,y-1]
        model.reInvestRule = pe.Constraint(model.R,model.C,model.Y,rule=reInvestRule)

        def reInvestLimit(model,c,y):
            return sum( model.reInvest[r,c,y] for r in model.R) <= model.MAXSITES[c] * model.coalRetire[c,y]
        model.reInvestLimit = pe.Constraint(model.C,model.Y,rule=reInvestLimit)

        def coalRetireRule(model,c,y):
            if y == model.Y[1]:
                return model.coalRetire[c,y] == 1 - model.coalOnline[c,y]
            #else
            return model.coalRetire[c,y] == model.coalOnline[c,y-1] - model.coalOnline[c,y]
        model.coalRetireRule = pe.Constraint(model.C,model.Y,rule=coalRetireRule)

        def coalRetireLimit(model,c):
            return sum(model.coalRetire[c,y] for y in model.Y) <= 1
        model.coalRetireLimit = pe.Constraint(model.C,rule=coalRetireLimit)

        self.model = model

    def solve(self,alpha,beta,gamma):
        '''solve(self,alpha,beta,gamma):
        Solve the equitable retirement optimization problem. PRECONDITION: All sets and params have been initialized.
        '''
        #rebuild model
        self.__buildModel(alpha,beta,gamma)

        opt = pyomo.opt.SolverFactory('glpk')
        opt.solve(self.model)

        # extract
        self.__extractResults()

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
    COALOPEX = np.arange(numCoal)
    MAXCAP = np.ones(numRE)*10
    MAXSITES = np.ones(numCoal) *10
    HD = numCoal-np.arange(numCoal)
    RETEF = np.arange(numCoal)*20
    CONEF = np.arange(numRE)
    COALOMEF = numCoal-np.arange(numCoal)
    REOMEF = numRE-np.arange(numRE)
    
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

def main():
    pass

if __name__ == '__main__':
    test()
