# -*- coding: utf-8 -*-
"""
Created on Tue Jun 20 22:14:07 2017

@author: YSu
"""

from pyomo.opt import SolverFactory
from CA_dispatch import model as m1
from CA_dispatchLP import model as m2
from pyomo.core import Var
from pyomo.core import Constraint
from pyomo.core import Param
from operator import itemgetter
import pandas as pd
import numpy as np
from datetime import datetime
import pyomo.environ as pyo

Solvername = 'gurobi'
Timelimit = 1800 # for the simulation of one day in seconds
# Threadlimit = 8 # maximum number of threads to use

def sim(days):


    instance = m1.create_instance('data.dat')
    instance2 = m2.create_instance('dataLP.dat')


    instance2.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    opt = SolverFactory("gurobi")
    
    if Solvername == 'cplex':
        opt.options['timelimit'] = Timelimit
    elif Solvername == 'gurobi':           
        opt.options['TimeLimit'] = Timelimit
    # opt.options['threads'] = Threadlimit
    
    H = instance.HorizonHours
    D = int(H/24)
    K=range(1,H+1)


    #Space to store results
    mwh_1=[]
    mwh_2=[]
    mwh_3=[]
    on=[]
    switch=[]
    srsv=[]
    nrsv=[]
    solar=[]
    wind=[]
    flow=[]
    Generator=[]
    Duals=[]
    System_cost = []
    battery_discharge = []
    battery_charge = []
    battery_state = []
    wind_curtailment_PGE_Valley, wind_curtailment_PGE_Bay, wind_curtailment_SCE, wind_curtailment_SDGE = [], [], [], []
    solar_curtailment_PGE_Valley, solar_curtailment_PGE_Bay, solar_curtailment_SCE, solar_curtailment_SDGE = [], [], [], []
    wind_curtailment_daily_PGE_Valley, wind_curtailment_daily_PGE_Bay, wind_curtailment_daily_SCE, wind_curtailment_daily_SDGE = [], [], [], []
    solar_curtailment_daily_PGE_Valley, solar_curtailment_daily_PGE_Bay, solar_curtailment_daily_SCE, solar_curtailment_daily_SDGE = [], [], [], []
    df_generators = pd.read_csv('generators.csv',header=0)

    #max here can be (1,365)
    for day in range(1,days):

         #load time series data
        for z in instance.zones:

            instance.GasPrice[z] = instance.SimGasPrice[z,day]

            for i in K:
                instance.HorizonDemand[z,i] = instance.SimDemand[z,(day-1)*24+i]
                instance.HorizonWind[z,i] = instance.SimWind[z,(day-1)*24+i]
                instance.HorizonSolar[z,i] = instance.SimSolar[z,(day-1)*24+i]
                instance.HorizonMustRun[z,i] = instance.SimMustRun[z,(day-1)*24+i]

        for d in range(1,D+1):
            instance.HorizonPath66_imports[d] = instance.SimPath66_imports[day-1+d]
            instance.HorizonPath46_SCE_imports[d] = instance.SimPath46_SCE_imports[day-1+d]
            instance.HorizonPath61_imports[d] = instance.SimPath61_imports[day-1+d]
            instance.HorizonPath42_imports[d] = instance.SimPath42_imports[day-1+d]
            instance.HorizonPath24_imports[d] = instance.SimPath24_imports[day-1+d]
            instance.HorizonPath45_imports[d] = instance.SimPath45_imports[day-1+d]
            instance.HorizonPGE_valley_hydro[d] = instance.SimPGE_valley_hydro[day-1+d]
            instance.HorizonSCE_hydro[d] = instance.SimSCE_hydro[day-1+d]

        for i in K:
            instance.HorizonReserves[i] = instance.SimReserves[(day-1)*24+i]
            instance.HorizonPath42_exports[i] = instance.SimPath42_exports[(day-1)*24+i]
            instance.HorizonPath24_exports[i] = instance.SimPath24_exports[(day-1)*24+i]
            instance.HorizonPath45_exports[i] = instance.SimPath45_exports[(day-1)*24+i]
            instance.HorizonPath66_exports[i] = instance.SimPath66_exports[(day-1)*24+i]

            instance.HorizonPath46_SCE_minflow[i] = instance.SimPath46_SCE_imports_minflow[(day-1)*24+i]
            instance.HorizonPath66_minflow[i] = instance.SimPath66_imports_minflow[(day-1)*24+i]
            instance.HorizonPath42_minflow[i] = instance.SimPath42_imports_minflow[(day-1)*24+i]
            instance.HorizonPath61_minflow[i] = instance.SimPath61_imports_minflow[(day-1)*24+i]
            instance.HorizonPGE_valley_hydro_minflow[i] = instance.SimPGE_valley_hydro_minflow[(day-1)*24+i]
            instance.HorizonSCE_hydro_minflow[i] = instance.SimSCE_hydro_minflow[(day-1)*24+i]
    #
        CAISO_result = opt.solve(instance,tee=True,symbolic_solver_labels=True, load_solutions=False)
        instance.solutions.load_from(CAISO_result)
        
        ########### 
        # record objective function value
        
        coal = 0
        gas11 = 0
        gas21 = 0
        gas31 = 0
        gas12 = 0
        gas22 = 0
        gas32 = 0
        gas13 = 0
        gas23 = 0
        gas33 = 0
        gas14 = 0
        gas24 = 0
        gas34 = 0
        oil = 0
        psh = 0
        slack = 0
        f_gas1 = 0
        f_gas2 = 0
        f_gas3 = 0
        f_oil = 0
        f_coal = 0
        st = 0
        sdgei = 0
        scei = 0
        pgei = 0
        f = 0
        
        for i in range(1,25):
            for j in instance.Coal:
                coal = coal + instance.mwh_1[j,i].value*(instance.seg1[j]*2 + instance.var_om[j]) + instance.mwh_2[j,i].value*(instance.seg2[j]*2 + instance.var_om[j]) + instance.mwh_3[j,i].value*(instance.seg3[j]*2 + instance.var_om[j])  
            for j in instance.Zone1Gas:
                gas11 = gas11 + instance.mwh_1[j,i].value*(instance.seg1[j]*instance.GasPrice['PGE_valley'].value + instance.var_om[j]) 
                gas21 = gas21 + instance.mwh_2[j,i].value*(instance.seg2[j]*instance.GasPrice['PGE_valley'].value + instance.var_om[j]) 
                gas31 = gas31 + instance.mwh_3[j,i].value*(instance.seg3[j]*instance.GasPrice['PGE_valley'].value + instance.var_om[j]) 
            for j in instance.Zone2Gas:
                gas12 = gas12 + instance.mwh_1[j,i].value*(instance.seg1[j]*instance.GasPrice['PGE_bay'].value + instance.var_om[j]) 
                gas22 = gas22 + instance.mwh_2[j,i].value*(instance.seg2[j]*instance.GasPrice['PGE_bay'].value + instance.var_om[j]) 
                gas32 = gas32 + instance.mwh_3[j,i].value*(instance.seg3[j]*instance.GasPrice['PGE_bay'].value + instance.var_om[j]) 
            for j in instance.Zone3Gas:
                gas13 = gas13 + instance.mwh_1[j,i].value*(instance.seg1[j]*instance.GasPrice['SCE'].value + instance.var_om[j]) 
                gas23 = gas23 + instance.mwh_2[j,i].value*(instance.seg2[j]*instance.GasPrice['SCE'].value + instance.var_om[j]) 
                gas33 = gas33 + instance.mwh_3[j,i].value*(instance.seg3[j]*instance.GasPrice['SCE'].value + instance.var_om[j]) 
            for j in instance.Zone4Gas:
                gas14 = gas14 + instance.mwh_1[j,i].value*(instance.seg1[j]*instance.GasPrice['SDGE'].value + instance.var_om[j]) 
                gas24 = gas24 + instance.mwh_2[j,i].value*(instance.seg2[j]*instance.GasPrice['SDGE'].value + instance.var_om[j]) 
                gas34 = gas34 + instance.mwh_3[j,i].value*(instance.seg3[j]*instance.GasPrice['SDGE'].value + instance.var_om[j])                        
            for j in instance.Oil:
                oil = oil + instance.mwh_1[j,i].value*(instance.seg1[j]*20 + instance.var_om[j]) + instance.mwh_2[j,i].value*(instance.seg2[j]*20 + instance.var_om[j]) + instance.mwh_3[j,i].value*(instance.seg3[j]*20 + instance.var_om[j])  
            for j in instance.PSH:
                psh = psh + instance.mwh_1[j,i].value*(instance.seg1[j]*10 + instance.var_om[j]) + instance.mwh_2[j,i].value*(instance.seg2[j]*10 + instance.var_om[j]) + instance.mwh_3[j,i].value*(instance.seg3[j]*10 + instance.var_om[j])  
            for j in instance.Slack:
                slack = slack + instance.mwh_1[j,i].value*(instance.seg1[j]*2000 + instance.var_om[j]) + instance.mwh_2[j,i].value*(instance.seg2[j]*2000 + instance.var_om[j]) + instance.mwh_3[j,i].value*(instance.seg3[j]*2000 + instance.var_om[j])  
            for j in instance.Zone1Gas:
                f_gas1 = f_gas1 + instance.no_load[j]*instance.on[j,i].value*2
            for j in instance.Zone2Gas:
                f_gas2 = f_gas2 + instance.no_load[j]*instance.on[j,i].value*2
            for j in instance.Zone3Gas:
                f_gas3 = f_gas3 + instance.no_load[j]*instance.on[j,i].value*2
            for j in instance.Coal:
                f_coal = f_coal + instance.no_load[j]*instance.on[j,i].value*2
            for j in instance.Oil:
                f_oil = f_oil + instance.no_load[j]*instance.on[j,i].value*2
            for j in instance.Generators:
                st = st + instance.st_cost[j]*instance.switch[j,i].value
            for j in instance.WECCImportsSDGE:
                sdgei =sdgei + instance.mwh_1[j,i].value*(14.5 + 2.76*instance.GasPrice['SDGE'].value) + instance.mwh_2[j,i].value*(14.5 + 2.76*instance.GasPrice['SDGE'].value) + instance.mwh_3[j,i].value*(14.5 + 2.76*instance.GasPrice['SDGE'].value)
            for j in instance.WECCImportsSCE:
                scei =scei + instance.mwh_1[j,i].value*(14.5 + 2.76*instance.GasPrice['SCE'].value) + instance.mwh_2[j,i].value*(14.5 + 2.76*instance.GasPrice['SCE'].value) + instance.mwh_3[j,i].value*(14.5 + 2.76*instance.GasPrice['SCE'].value)
            for j in instance.WECCImportsPGEV:
                pgei =pgei + instance.mwh_1[j,i].value*5 + instance.mwh_2[j,i].value*5 + instance.mwh_3[j,i].value*5
            for s in instance.sources:
                for k in instance.sinks:
                    f = f + instance.flow[s,k,i].value*instance.hurdle[s,k] 

        S = f + oil + coal + slack + psh + st + sdgei + scei + pgei + f_gas1 + f_gas2 + f_gas3 + f_oil + gas11 + gas21 + gas31 + gas12 + gas22 + gas32 + gas13 + gas23 + gas33 + gas14 + gas24 + gas34 
        System_cost.append(S)

        bat_ch = []
        bat_dis = []
        bat_state = []
        
        for v in instance.component_objects(Var, active=True):
            varobject = getattr(instance, str(v))
            a=str(v)
        
            if a == 'bat_discharge':
            
                for index in varobject:
                    if int(index[1]>0 and index[1]<49):
                        if index[0] in instance.Zone1Battery:
                            bat_dis.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley'))
                        elif index[0] in instance.Zone2Battery:
                            bat_dis.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay'))
                        elif index[0] in instance.Zone3Battery:
                            bat_dis.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE'))
                        elif index[0] in instance.Zone4Battery:
                            bat_dis.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE'))

            if a == 'bat_charge':
                
                for index in varobject:
                    if int(index[1]>0 and index[1]<49):
                        if index[0] in instance.Zone1Battery:
                            bat_ch.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley'))
                        elif index[0] in instance.Zone2Battery:
                            bat_ch.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay'))
                        elif index[0] in instance.Zone3Battery:
                            bat_ch.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE'))
                        elif index[0] in instance.Zone4Battery:
                            bat_ch.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE'))

            if a == 'bat_SoC':
                
                for index in varobject:
                    if int(index[1]>0 and index[1]<25):
                        if index[0] in instance.Zone1Battery:
                            bat_state.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley'))
                        elif index[0] in instance.Zone2Battery:
                            bat_state.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay'))
                        elif index[0] in instance.Zone3Battery:
                            bat_state.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE'))
                        elif index[0] in instance.Zone4Battery:
                            bat_state.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE'))

        charge = pd.DataFrame(bat_ch,columns=['Name','Hour','Value','Zone'])
        charge.set_index(['Hour','Zone'])
        discharge = pd.DataFrame(bat_dis,columns=['Name','Hour','Value','Zone'])
        discharge.set_index(['Hour','Zone'])

        for z in instance2.zones:
            
            instance2.GasPrice[z] = instance2.SimGasPrice[z,day]

            for i in K:
                
                c = charge[(charge['Hour'] == (day-1)*24+i) & (charge['Zone']==z)]
                c = np.float(c['Value'].values)
                d = discharge[(discharge['Hour'] == (day-1)*24+i) & (discharge['Zone']==z)]
                d = np.float(d['Value'].values)
            
                instance2.HorizonDemand[z,i] = max(instance2.SimDemand[z,(day-1)*24+i] + c - d,0) #make sure it stays non-negative using max(x,0)
                instance2.HorizonWind[z,i] = instance2.SimWind[z,(day-1)*24+i]
                instance2.HorizonSolar[z,i] = instance2.SimSolar[z,(day-1)*24+i]
                instance2.HorizonMustRun[z,i] = instance2.SimMustRun[z,(day-1)*24+i]

        for d in range(1,D+1):
            instance2.HorizonPath66_imports[d] = instance2.SimPath66_imports[day-1+d]
            instance2.HorizonPath46_SCE_imports[d] = instance2.SimPath46_SCE_imports[day-1+d]
            instance2.HorizonPath61_imports[d] = instance2.SimPath61_imports[day-1+d]
            instance2.HorizonPath42_imports[d] = instance2.SimPath42_imports[day-1+d]
            instance2.HorizonPath24_imports[d] = instance2.SimPath24_imports[day-1+d]
            instance2.HorizonPath45_imports[d] = instance2.SimPath45_imports[day-1+d]
            instance2.HorizonPGE_valley_hydro[d] = instance2.SimPGE_valley_hydro[day-1+d]
            instance2.HorizonSCE_hydro[d] = instance2.SimSCE_hydro[day-1+d]

        for i in K:
            instance2.HorizonReserves[i] = instance2.SimReserves[(day-1)*24+i]
            instance2.HorizonPath42_exports[i] = instance2.SimPath42_exports[(day-1)*24+i]
            instance2.HorizonPath24_exports[i] = instance2.SimPath24_exports[(day-1)*24+i]
            instance2.HorizonPath45_exports[i] = instance2.SimPath45_exports[(day-1)*24+i]
            instance2.HorizonPath66_exports[i] = instance2.SimPath66_exports[(day-1)*24+i]

            instance2.HorizonPath46_SCE_minflow[i] = instance2.SimPath46_SCE_imports_minflow[(day-1)*24+i]
            instance2.HorizonPath66_minflow[i] = instance2.SimPath66_imports_minflow[(day-1)*24+i]
            instance2.HorizonPath42_minflow[i] = instance2.SimPath42_imports_minflow[(day-1)*24+i]
            instance2.HorizonPath61_minflow[i] = instance2.SimPath61_imports_minflow[(day-1)*24+i]
            instance2.HorizonPGE_valley_hydro_minflow[i] = instance2.SimPGE_valley_hydro_minflow[(day-1)*24+i]
            instance2.HorizonSCE_hydro_minflow[i] = instance2.SimSCE_hydro_minflow[(day-1)*24+i]
  
        for j in instance.Generators:
            for t in K:
                if instance.on[j,t] == 1:
                    instance2.on[j,t] = 1
                    instance2.on[j,t].fixed = True
                else:
                    instance.on[j,t] = 0
                    instance2.on[j,t] = 0
                    instance2.on[j,t].fixed = True

                if instance.switch[j,t] == 1:
                    instance2.switch[j,t] = 1
                    instance2.switch[j,t].fixed = True
                else:
                    instance2.switch[j,t] = 0
                    instance2.switch[j,t] = 0
                    instance2.switch[j,t].fixed = True
                   
                    
        results = opt.solve(instance2,tee=True,symbolic_solver_labels=True, load_solutions=False)
        instance2.solutions.load_from(results)



        print ("Duals")

        # Define curtailment as any time when wind dispatched by the model (e.g., the sum of model.wind for a given hour, zone)
        # is less than the amount of wind that could be dispatched, (i.e .the value of SimWind for the same zone, hour).
        # (reported on a daily basis)
        
        #append curtailment based on difference between amount dispatched and amount that could be dispatched
        for i in range(1,25):
            wind_cur_PGE_Valley = float(instance2.HorizonWind['PGE_valley',i].value or 0) - float(instance2.wind['PGE_valley',i].value or 0)
            solar_cur_PGE_Valley = float(instance2.HorizonSolar['PGE_valley',i].value or 0) - float(instance2.solar['PGE_valley',i].value or 0)
            wind_cur_PGE_Bay = float(instance2.HorizonWind['PGE_bay',i].value or 0) - float(instance2.wind['PGE_bay',i].value or 0)
            solar_cur_PGE_Bay = float(instance2.HorizonSolar['PGE_bay',i].value or 0) - float(instance2.solar['PGE_bay',i].value or 0)
            wind_cur_SCE = float(instance2.HorizonWind['SCE',i].value or 0) - float(instance2.wind['SCE',i].value or 0)
            solar_cur_SCE = float(instance2.HorizonSolar['SCE',i].value or 0) - float(instance2.solar['SCE',i].value or 0)
            wind_cur_SDGE = float(instance2.HorizonWind['SDGE',i].value or 0) - float(instance2.wind['SDGE',i].value or 0)
            solar_cur_SDGE = float(instance2.HorizonSolar['SDGE',i].value or 0) - float(instance2.solar['SDGE',i].value or 0)          
            wind_curtailment_PGE_Valley.append(wind_cur_PGE_Valley)
            solar_curtailment_PGE_Valley.append(solar_cur_PGE_Valley)
            wind_curtailment_PGE_Bay.append(wind_cur_PGE_Bay)
            solar_curtailment_PGE_Bay.append(solar_cur_PGE_Bay)
            wind_curtailment_SCE.append(wind_cur_SCE)
            solar_curtailment_SCE.append(solar_cur_SCE)
            wind_curtailment_SDGE.append(wind_cur_SDGE)
            solar_curtailment_SDGE.append(solar_cur_SDGE)

        for c in instance2.component_objects(Constraint, active=True):
    #        print ("   Constraint",c)
            cobject = getattr(instance2, str(c))
            if str(c) in ['Bal1Constraint','Bal2Constraint','Bal3Constraint','Bal4Constraint']:
                for index in cobject:
                     if int(index>0 and index<25):
    #                print ("   Constraint",c)
                         try:
                             Duals.append((str(c),index+((day-1)*24), instance2.dual[cobject[index]]))
                         except KeyError:
                             Duals.append((str(c),index+((day-1)*24),-999))
    #            print ("      ", index, instance2.dual[cobject[index]])
        #The following section is for storing and sorting results
        for v in instance.component_objects(Var, active=True):
            varobject = getattr(instance, str(v))
            a=str(v)
            if a=='mwh_1':

             for index in varobject:

               name = index[0]

               g = df_generators[df_generators['name']==name]
               seg1 = g['seg1'].values
               seg1 = seg1[0]

               if int(index[1]>0 and index[1]<25):
                if index[0] in instance.Zone1Generators:

                    gas_price = instance.GasPrice['PGE_valley'].value

                    if index[0] in instance.Gas:
                        marginal_cost = seg1*gas_price
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','Gas',marginal_cost))
                    elif index[0] in instance.Coal:
                        marginal_cost = seg1*2
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','Coal',marginal_cost))
                    elif index[0] in instance.Oil:
                        marginal_cost = seg1*20
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','Oil',marginal_cost))
                    elif index[0] in instance.PSH:
                        marginal_cost = 10
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','PSH',marginal_cost))
                    elif index[0] in instance.Slack:
                        marginal_cost = 700
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','Slack',marginal_cost))
                    elif index[0] in instance.Hydro:
                        marginal_cost = 0
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','Hydro',marginal_cost))


                elif index[0] in instance.Zone2Generators:

                    gas_price = instance.GasPrice['PGE_bay'].value

                    if index[0] in instance.Gas:
                        marginal_cost = seg1*gas_price
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay','Gas',marginal_cost))
                    elif index[0] in instance.Coal:
                        marginal_cost = seg1*2
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay','Coal',marginal_cost))
                    elif index[0] in instance.Oil:
                        marginal_cost = seg1*20
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay','Oil',marginal_cost))
                    elif index[0] in instance.PSH:
                        marginal_cost = 10
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay','PSH',marginal_cost))
                    elif index[0] in instance.Slack:
                        marginal_cost = 700
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay','Slack',marginal_cost))

                elif index[0] in instance.Zone3Generators:

                    gas_price = instance.GasPrice['SCE'].value

                    if index[0] in instance.Gas:
                        marginal_cost = seg1*gas_price
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','Gas',marginal_cost))
                    elif index[0] in instance.Coal:
                        marginal_cost = seg1*2
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','Coal',marginal_cost))
                    elif index[0] in instance.Oil:
                        marginal_cost = seg1*20
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','Oil',marginal_cost))
                    elif index[0] in instance.PSH:
                        marginal_cost = 10
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','PSH',marginal_cost))
                    elif index[0] in instance.Slack:
                        marginal_cost = 700
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','Slack',marginal_cost))
                    elif index[0] in instance.Hydro:
                        marginal_cost = 0
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','Hydro',marginal_cost))

                elif index[0] in instance.Zone4Generators:

                    gas_price = instance.GasPrice['SDGE'].value

                    if index[0] in instance.Gas:
                        marginal_cost = seg1*gas_price
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE','Gas',marginal_cost))
                    elif index[0] in instance.Coal:
                        marginal_cost = seg1*2
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE','Coal',marginal_cost))
                    elif index[0] in instance.Oil:
                        marginal_cost = seg1*20
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE','Oil',marginal_cost))
                    elif index[0] in instance.PSH:
                        marginal_cost = 10
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE','PSH',marginal_cost))
                    elif index[0] in instance.Slack:
                        marginal_cost = 700
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE','Slack',marginal_cost))


                elif index[0] in instance.WECCImportsSDGE:

                    gas_price = instance.GasPrice['SDGE'].value
                    marginal_cost = 14.5+2.76*gas_price
                    mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE','imports',marginal_cost))


                elif index[0] in instance.WECCImportsSCE:

                    gas_price = instance.GasPrice['SCE'].value
                    marginal_cost = 14.5+2.76*gas_price
                    mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','imports',marginal_cost))


                elif index[0] in instance.WECCImportsPGEV:

                    marginal_cost = 5
                    mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','imports',marginal_cost))


            if a=='mwh_2':

             for index in varobject:

               name = index[0]
               g = df_generators[df_generators['name']==name]
               seg2 = g['seg2'].values
               seg2 = seg2[0]

               if int(index[1]>0 and index[1]<25):
                if index[0] in instance.Zone1Generators:

                    gas_price = instance.GasPrice['PGE_valley'].value

                    if index[0] in instance.Gas:
                        marginal_cost = seg2*gas_price
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','Gas',marginal_cost))
                    elif index[0] in instance.Coal:
                        marginal_cost = seg2*2
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','Coal',marginal_cost))
                    elif index[0] in instance.Oil:
                        marginal_cost = seg2*20
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','Oil',marginal_cost))
                    elif index[0] in instance.PSH:
                        marginal_cost = 10
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','PSH',marginal_cost))
                    elif index[0] in instance.Slack:
                        marginal_cost = 700
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','Slack',marginal_cost))
                    elif index[0] in instance.Hydro:
                        marginal_cost = 0
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','Hydro',marginal_cost))


                elif index[0] in instance.Zone2Generators:

                    gas_price = instance.GasPrice['PGE_bay'].value

                    if index[0] in instance.Gas:
                        marginal_cost = seg2*gas_price
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay','Gas',marginal_cost))
                    elif index[0] in instance.Coal:
                        marginal_cost = seg2*2
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay','Coal',marginal_cost))
                    elif index[0] in instance.Oil:
                        marginal_cost = seg2*20
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay','Oil',marginal_cost))
                    elif index[0] in instance.PSH:
                        marginal_cost = 10
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay','PSH',marginal_cost))
                    elif index[0] in instance.Slack:
                        marginal_cost = 700
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay','Slack',marginal_cost))

                elif index[0] in instance.Zone3Generators:

                    gas_price = instance.GasPrice['SCE'].value

                    if index[0] in instance.Gas:
                        marginal_cost = seg2*gas_price
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','Gas',marginal_cost))
                    elif index[0] in instance.Coal:
                        marginal_cost = seg2*2
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','Coal',marginal_cost))
                    elif index[0] in instance.Oil:
                        marginal_cost = seg2*20
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','Oil',marginal_cost))
                    elif index[0] in instance.PSH:
                        marginal_cost = 10
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','PSH',marginal_cost))
                    elif index[0] in instance.Slack:
                        marginal_cost = 700
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','Slack',marginal_cost))
                    elif index[0] in instance.Hydro:
                        marginal_cost = 0
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','Hydro',marginal_cost))

                elif index[0] in instance.Zone4Generators:

                    gas_price = instance.GasPrice['SDGE'].value

                    if index[0] in instance.Gas:
                        marginal_cost = seg2*gas_price
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE','Gas',marginal_cost))
                    elif index[0] in instance.Coal:
                        marginal_cost = seg2*2
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE','Coal',marginal_cost))
                    elif index[0] in instance.Oil:
                        marginal_cost = seg2*20
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE','Oil',marginal_cost))
                    elif index[0] in instance.PSH:
                        marginal_cost = 10
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE','PSH',marginal_cost))
                    elif index[0] in instance.Slack:
                        marginal_cost = 700
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE','Slack',marginal_cost))


                elif index[0] in instance.WECCImportsSDGE:

                    gas_price = instance.GasPrice['SDGE'].value
                    marginal_cost = 14.5+2.76*gas_price
                    mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE','imports',marginal_cost))


                elif index[0] in instance.WECCImportsSCE:

                    gas_price = instance.GasPrice['SCE'].value
                    marginal_cost = 14.5+2.76*gas_price
                    mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','imports',marginal_cost))


                elif index[0] in instance.WECCImportsPGEV:

                    marginal_cost = 5
                    mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','imports',marginal_cost))


            if a=='mwh_3':

             for index in varobject:

               name = index[0]
               g = df_generators[df_generators['name']==name]
               seg3 = g['seg3'].values
               seg3 = seg3[0]

               if int(index[1]>0 and index[1]<25):
                if index[0] in instance.Zone1Generators:

                    gas_price = instance.GasPrice['PGE_valley'].value

                    if index[0] in instance.Gas:
                        marginal_cost = seg3*gas_price
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','Gas',marginal_cost))
                    elif index[0] in instance.Coal:
                        marginal_cost = seg3*2
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','Coal',marginal_cost))
                    elif index[0] in instance.Oil:
                        marginal_cost = seg3*20
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','Oil',marginal_cost))
                    elif index[0] in instance.PSH:
                        marginal_cost = 10
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','PSH',marginal_cost))
                    elif index[0] in instance.Slack:
                        marginal_cost = 700
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','Slack',marginal_cost))
                    elif index[0] in instance.Hydro:
                        marginal_cost = 0
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','Hydro',marginal_cost))


                elif index[0] in instance.Zone2Generators:

                    gas_price = instance.GasPrice['PGE_bay'].value

                    if index[0] in instance.Gas:
                        marginal_cost = seg3*gas_price
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay','Gas',marginal_cost))
                    elif index[0] in instance.Coal:
                        marginal_cost = seg3*2
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay','Coal',marginal_cost))
                    elif index[0] in instance.Oil:
                        marginal_cost = seg3*20
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay','Oil',marginal_cost))
                    elif index[0] in instance.PSH:
                        marginal_cost = 10
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay','PSH',marginal_cost))
                    elif index[0] in instance.Slack:
                        marginal_cost = 700
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay','Slack',marginal_cost))

                elif index[0] in instance.Zone3Generators:

                    gas_price = instance.GasPrice['SCE'].value

                    if index[0] in instance.Gas:
                        marginal_cost = seg3*gas_price
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','Gas',marginal_cost))
                    elif index[0] in instance.Coal:
                        marginal_cost = seg3*2
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','Coal',marginal_cost))
                    elif index[0] in instance.Oil:
                        marginal_cost = seg3*20
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','Oil',marginal_cost))
                    elif index[0] in instance.PSH:
                        marginal_cost = 10
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','PSH',marginal_cost))
                    elif index[0] in instance.Slack:
                        marginal_cost = 700
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','Slack',marginal_cost))
                    elif index[0] in instance.Hydro:
                        marginal_cost = 0
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','Hydro',marginal_cost))

                elif index[0] in instance.Zone4Generators:

                    gas_price = instance.GasPrice['SDGE'].value

                    if index[0] in instance.Gas:
                        marginal_cost = seg3*gas_price
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE','Gas',marginal_cost))
                    elif index[0] in instance.Coal:
                        marginal_cost = seg3*2
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE','Coal',marginal_cost))
                    elif index[0] in instance.Oil:
                        marginal_cost = seg3*20
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE','Oil',marginal_cost))
                    elif index[0] in instance.PSH:
                        marginal_cost = 10
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE','PSH',marginal_cost))
                    elif index[0] in instance.Slack:
                        marginal_cost = 700
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE','Slack',marginal_cost))


                elif index[0] in instance.WECCImportsSDGE:

                    gas_price = instance.GasPrice['SDGE'].value
                    marginal_cost = 14.5+2.76*gas_price
                    mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE','imports',marginal_cost))


                elif index[0] in instance.WECCImportsSCE:

                    gas_price = instance.GasPrice['SCE'].value
                    marginal_cost = 14.5+2.76*gas_price
                    mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE','imports',marginal_cost))


                elif index[0] in instance.WECCImportsPGEV:

                    marginal_cost = 5
                    mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley','imports',marginal_cost))


            if a=='on':

             for index in varobject:
               if int(index[1]>0 and index[1]<25):
                if index[0] in instance.Zone1Generators:
                 on.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley'))
                elif index[0] in instance.Zone2Generators:
                 on.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay'))
                elif index[0] in instance.Zone3Generators:
                 on.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE'))
                elif index[0] in instance.Zone4Generators:
                 on.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE'))
                 
                 
            if a == 'bat_discharge':
                
                for index in varobject:
                    if int(index[1]>0 and index[1]<25):
                        if index[0] in instance.Zone1Battery:
                            battery_discharge.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley'))
                        elif index[0] in instance.Zone2Battery:
                            battery_discharge.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay'))
                        elif index[0] in instance.Zone3Battery:
                            battery_discharge.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE'))
                        elif index[0] in instance.Zone4Battery:
                            battery_discharge.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE'))

            if a == 'bat_charge':
                
                for index in varobject:
                    if int(index[1]>0 and index[1]<25):
                        if index[0] in instance.Zone1Battery:
                            battery_charge.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley'))
                        elif index[0] in instance.Zone2Battery:
                            battery_charge.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay'))
                        elif index[0] in instance.Zone3Battery:
                            battery_charge.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE'))
                        elif index[0] in instance.Zone4Battery:
                            battery_charge.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE'))


            if a == 'bat_SoC':
                
                for index in varobject:
                    if int(index[1]>0 and index[1]<25):
                        if index[0] in instance.Zone1Battery:
                            battery_state.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley'))
                        elif index[0] in instance.Zone2Battery:
                            battery_state.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay'))
                        elif index[0] in instance.Zone3Battery:
                            battery_state.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE'))
                        elif index[0] in instance.Zone4Battery:
                            battery_state.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE'))

            if a=='switch':

             for index in varobject:
               if int(index[1]>0 and index[1]<25):
                if index[0] in instance.Zone1Generators:
                 switch.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley'))
                elif index[0] in instance.Zone2Generators:
                 switch.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay'))
                elif index[0] in instance.Zone3Generators:
                 switch.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE'))
                elif index[0] in instance.Zone4Generators:
                 switch.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE'))


            if a=='srsv':

             for index in varobject:
               if int(index[1]>0 and index[1]<25):
                if index[0] in instance.Zone1Generators:
                 srsv.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley'))
                elif index[0] in instance.Zone2Generators:
                 srsv.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay'))
                elif index[0] in instance.Zone3Generators:
                 srsv.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE'))
                elif index[0] in instance.Zone4Generators:
                 srsv.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE'))


            if a=='nrsv':

             for index in varobject:
               if int(index[1]>0 and index[1]<25):
                if index[0] in instance.Zone1Generators:
                 nrsv.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_valley'))
                elif index[0] in instance.Zone2Generators:
                 nrsv.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PGE_bay'))
                elif index[0] in instance.Zone3Generators:
                 nrsv.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SCE'))
                elif index[0] in instance.Zone4Generators:
                 nrsv.append((index[0],index[1]+((day-1)*24),varobject[index].value,'SDGE'))


            if a=='solar':

             for index in varobject:
               if int(index[1]>0 and index[1]<25):
                solar.append((index[0],index[1]+((day-1)*24),varobject[index].value))


            if a=='wind':

             for index in varobject:
               if int(index[1]>0 and index[1]<25):
                wind.append((index[0],index[1]+((day-1)*24),varobject[index].value))

            if a=='flow':

             for index in varobject:
               if int(index[2]>0 and index[2]<25):
                flow.append((index[0],index[1],index[2]+((day-1)*24),varobject[index].value))


            for j in instance.Generators:
                if instance.on[j,24] == 1:
                    instance.on[j,0] = 1
                else:
                    instance.on[j,0] = 0
                

                if instance.mwh_1[j,24].value <=0 and instance.mwh_1[j,24].value>= -0.0001:
                    newval_1=0
                else:
                    newval_1=instance.mwh_1[j,24].value

                if instance.mwh_2[j,24].value <=0 and instance.mwh_2[j,24].value>= -0.0001:
                    newval=0
                else:
                    newval=instance.mwh_2[j,24].value

                if instance.mwh_3[j,24].value <=0 and instance.mwh_3[j,24].value>= -0.0001:
                    newval2=0
                else:
                    newval2=instance.mwh_3[j,24].value

                instance.on[j,0].fixed = True
                instance.mwh_1[j,0] = newval_1
                instance.mwh_1[j,0].fixed = True
                instance.mwh_2[j,0] = newval
                instance.mwh_2[j,0].fixed = True
                instance.mwh_3[j,0] = newval2
                instance.mwh_3[j,0].fixed = True
                
                
                if instance.switch[j,24] == 1:
                    instance.switch[j,0] = 1
                else:
                    instance.switch[j,0] = 0
                instance.switch[j,0].fixed = True

                if instance.srsv[j,24].value <=0 and instance.srsv[j,24].value>= -0.0001:
                    newval_srsv=0
                else:
                    newval_srsv=instance.srsv[j,24].value
                instance.srsv[j,0] = newval_srsv
                instance.srsv[j,0].fixed = True

                if instance.nrsv[j,24].value <=0 and instance.nrsv[j,24].value>= -0.0001:
                    newval_nrsv=0
                else:
                    newval_nrsv=instance.nrsv[j,24].value
                instance.nrsv[j,0] = newval_nrsv
                instance.nrsv[j,0].fixed = True

            for j in instance.Batteries:
                              
                if instance.bat_SoC[j,24].value <=0 and instance.bat_SoC[j,24].value>= -0.0001:
                    newval_1=0
                else:
                    newval_1=instance.bat_SoC[j,24].value

                instance.bat_SoC[j,0] = newval_1
                instance.bat_SoC[j,0].fixed = True




        print(day)

    mwh_1_pd=pd.DataFrame(mwh_1,columns=('Generator','Time','Value','Zones','Type','$/MWh'))
    mwh_2_pd=pd.DataFrame(mwh_2,columns=('Generator','Time','Value','Zones','Type','$/MWh'))
    mwh_3_pd=pd.DataFrame(mwh_3,columns=('Generator','Time','Value','Zones','Type','$/MWh'))
    on_pd=pd.DataFrame(on,columns=('Generator','Time','Value','Zones'))
    battery_charge_pd = pd.DataFrame(battery_charge, columns=('Generator','Time','Value','Zones'))
    battery_discharge_pd = pd.DataFrame(battery_discharge, columns=('Generator','Time','Value','Zones'))
    battery_state_pd = pd.DataFrame(battery_state, columns=('Generator','Time','Value','Zones'))    
    switch_pd=pd.DataFrame(switch,columns=('Generator','Time','Value','Zones'))
    srsv_pd=pd.DataFrame(srsv,columns=('Generator','Time','Value','Zones'))
    nrsv_pd=pd.DataFrame(nrsv,columns=('Generator','Time','Value','Zones'))
    solar_pd=pd.DataFrame(solar,columns=('Zone','Time','Value'))
    wind_pd=pd.DataFrame(wind,columns=('Zone','Time','Value'))
    flow_pd=pd.DataFrame(flow,columns=('Source','Sink','Time','Value'))
    shadow_price=pd.DataFrame(Duals,columns=('Constraint','Time','Value'))
    objective = pd.DataFrame(System_cost)

    #sum curtailment every 24 hours to get a daily value
    for i in range(365):
        wind_curtailment_daily_PGE_Valley.append(sum(wind_curtailment_PGE_Valley[i*24:24*(1+i)]))
        solar_curtailment_daily_PGE_Valley.append(sum(solar_curtailment_PGE_Valley[i*24:24*(1+i)]))
        wind_curtailment_daily_PGE_Bay.append(sum(wind_curtailment_PGE_Bay[i*24:24*(1+i)]))
        solar_curtailment_daily_PGE_Bay.append(sum(solar_curtailment_PGE_Bay[i*24:24*(1+i)]))
        wind_curtailment_daily_SCE.append(sum(wind_curtailment_SCE[i*24:24*(1+i)]))
        solar_curtailment_daily_SCE.append(sum(solar_curtailment_SCE[i*24:24*(1+i)]))
        wind_curtailment_daily_SDGE.append(sum(wind_curtailment_SDGE[i*24:24*(1+i)]))
        solar_curtailment_daily_SDGE.append(sum(solar_curtailment_SDGE[i*24:24*(1+i)]))
    
    #output curtailment to dataframe and then csv\
    wind_curtailment_daily = {'PGE_Valley':wind_curtailment_daily_PGE_Valley,\
                              'PGE_Bay':wind_curtailment_daily_PGE_Bay,\
                              'SCE':wind_curtailment_daily_SCE,\
                              'SDGE':wind_curtailment_daily_SDGE}
    solar_curtailment_daily = {'PGE_Valley':solar_curtailment_daily_PGE_Valley,\
                              'PGE_Bay':solar_curtailment_daily_PGE_Bay,\
                              'SCE':solar_curtailment_daily_SCE,\
                              'SDGE':solar_curtailment_daily_SDGE}
    wind_curtailment_pd = pd.DataFrame(wind_curtailment_daily,columns=('PGE_Valley','PGE_Bay','SCE','SDGE'))
    solar_curtailment_pd = pd.DataFrame(solar_curtailment_daily,columns=('PGE_Valley','PGE_Bay','SCE','SDGE'))
    wind_curtailment_pd.to_csv('wind_curtailment_daily.csv')
    solar_curtailment_pd.to_csv('solar_curtailment_daily.csv')

    flow_pd.to_csv('flow.csv')
    mwh_1_pd.to_csv('mwh_1.csv')
    mwh_2_pd.to_csv('mwh_2.csv')
    mwh_3_pd.to_csv('mwh_3.csv')
    on_pd.to_csv('on.csv')
    battery_charge_pd.to_csv('battery_charge.csv')
    battery_discharge_pd.to_csv('battery_discharge.csv')
    battery_state_pd.to_csv('battery_state.csv')
    switch_pd.to_csv('switch.csv')
    srsv_pd.to_csv('srsv.csv')
    nrsv_pd.to_csv('nrsv.csv')
    solar_pd.to_csv('solar_out.csv')
    wind_pd.to_csv('wind_out.csv')
    shadow_price.to_csv('shadow_price.csv')
    objective.to_csv('obj_function.csv')

    return None
