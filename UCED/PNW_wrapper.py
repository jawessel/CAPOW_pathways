# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 19:25:54 2019

@author: Joy Hill
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Jun 28 12:03:41 2018

@author: Joy Hill
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Jun 20 22:14:07 2017

@author: YSu
"""

from pyomo.opt import SolverFactory
from PNW_dispatch import model as m1
from PNW_dispatchLP import model as m2
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
    D = 2
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
    battery_charge = []
    battery_discharge =[]
    battery_state = []
    wind_curtailment = []
    solar_curtailment = []
    wind_curtailment_daily = []
    solar_curtailment_daily = []

    df_generators = pd.read_csv('generators.csv',header=0)
    
    instance.ini_on["COLUMBIA_2"] = 1
    instance.ini_mwh_1["COLUMBIA_2"] = 300
        
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
            instance.HorizonPath3_imports[d] = instance.SimPath3_imports[day-1+d]
            instance.HorizonPath8_imports[d] = instance.SimPath8_imports[day-1+d]
            instance.HorizonPath14_imports[d] = instance.SimPath14_imports[day-1+d]
            instance.HorizonPath65_imports[d] = instance.SimPath65_imports[day-1+d]
            instance.HorizonPath66_imports[d] = instance.SimPath66_imports[day-1+d]
            instance.HorizonPNW_hydro[d] = instance.SimPNW_hydro[day-1+d]
            
        for i in K:
            instance.HorizonReserves[i] = instance.SimReserves[(day-1)*24+i] 
            instance.HorizonPath3_exports[i] = instance.SimPath3_exports[(day-1)*24+i] 
            instance.HorizonPath8_exports[i] = instance.SimPath8_exports[(day-1)*24+i] 
            instance.HorizonPath14_exports[i] = instance.SimPath14_exports[(day-1)*24+i]
            instance.HorizonPath65_exports[i] = instance.SimPath65_exports[(day-1)*24+i]             
            instance.HorizonPath66_exports[i] = instance.SimPath66_exports[(day-1)*24+i]  
            
            instance.HorizonPath3_minflow[i] = instance.SimPath3_imports_minflow[(day-1)*24+i]             
            instance.HorizonPath8_minflow[i] = instance.SimPath8_imports_minflow[(day-1)*24+i]             
            instance.HorizonPath14_minflow[i] = instance.SimPath14_imports_minflow[(day-1)*24+i]             
            instance.HorizonPath65_minflow[i] = instance.SimPath65_imports_minflow[(day-1)*24+i]  
            instance.HorizonPath66_minflow[i] = instance.SimPath66_imports_minflow[(day-1)*24+i]  
            instance.HorizonPNW_hydro_minflow[i] = instance.SimPNW_hydro_minflow[(day-1)*24+i]
    #            
        PNW_result = opt.solve(instance,tee=True,symbolic_solver_labels=True, load_solutions=False)
        instance.solutions.load_from(PNW_result)
        
        ##################
        # record objective function
        
        coal = 0
        nuclear = 0
        gas = 0
        oil = 0
        psh = 0
        slack = 0
        f_gas = 0
        f_oil = 0
        f_coal = 0
        st = 0
        
        for i in range(1,25):
            for j in instance.Coal:
                coal = coal + instance.mwh_1[j,i].value*(instance.seg1[j]*2 + instance.var_om[j]) + instance.mwh_2[j,i].value*(instance.seg2[j]*2 + instance.var_om[j]) + instance.mwh_3[j,i].value*(instance.seg3[j]*2 + instance.var_om[j])  
            for j in instance.Gas:
                gas = gas + instance.mwh_1[j,i].value*(instance.seg1[j]*instance.GasPrice['PNW'].value + instance.var_om[j]) + instance.mwh_2[j,i].value*(instance.seg2[j]*instance.GasPrice['PNW'].value + instance.var_om[j]) + instance.mwh_3[j,i].value*(instance.seg3[j]*instance.GasPrice['PNW'].value + instance.var_om[j])  
            for j in instance.Nuclear:
                nuclear = nuclear + instance.mwh_1[j,i].value*(instance.seg1[j]*1 + instance.var_om[j]) + instance.mwh_2[j,i].value*(instance.seg2[j]*1 + instance.var_om[j]) + instance.mwh_3[j,i].value*(instance.seg3[j]*1 + instance.var_om[j])  
            for j in instance.Oil:
                oil = oil + instance.mwh_1[j,i].value*(instance.seg1[j]*20 + instance.var_om[j]) + instance.mwh_2[j,i].value*(instance.seg2[j]*20 + instance.var_om[j]) + instance.mwh_3[j,i].value*(instance.seg3[j]*20 + instance.var_om[j])  
            for j in instance.PSH:
                psh = psh + instance.mwh_1[j,i].value*(instance.seg1[j]*10 + instance.var_om[j]) + instance.mwh_2[j,i].value*(instance.seg2[j]*10 + instance.var_om[j]) + instance.mwh_3[j,i].value*(instance.seg3[j]*10 + instance.var_om[j])  
            for j in instance.Slack:
                slack = slack + instance.mwh_1[j,i].value*(instance.seg1[j]*2000 + instance.var_om[j]) + instance.mwh_2[j,i].value*(instance.seg2[j]*2000 + instance.var_om[j]) + instance.mwh_3[j,i].value*(instance.seg3[j]*2000 + instance.var_om[j])  
            for j in instance.Gas:
                f_gas = f_gas + instance.no_load[j]*instance.on[j,i].value*2
            for j in instance.Coal:
                f_coal = f_coal + instance.no_load[j]*instance.on[j,i].value*2
            for j in instance.Oil:
                f_oil = f_oil + instance.no_load[j]*instance.on[j,i].value*2
            for j in instance.Generators:
                st = st + instance.st_cost[j]*instance.switch[j,i].value

        S = gas + oil + coal + slack + psh + nuclear + st + f_gas + f_oil + f_coal 
        System_cost.append(S)

        
        bat_ch = [] #Initializing empty charge and discharge arrays as a pre-processing step before LP
        bat_dis = []
        bat_state = []
        
        for v in instance.component_objects(Var, active=True):
            varobject = getattr(instance, str(v))
            a=str(v)
            if a == 'bat_discharge':
                
                for index in varobject:
                    if int(index[1]>0 and index[1]<49):
                        if index[0] in instance.Zone5Battery:
                            bat_dis.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW'))

            if a == 'bat_charge':
                for index in varobject:
                    if int(index[1]>0 and index[1]<49):
                        if index[0] in instance.Zone5Battery:
                            bat_ch.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW'))
                            
            if a == 'bat_SoC':
                
                for index in varobject:
                    if int(index[1]>0 and index[1]<25):
                        if index[0] in instance.Zone5Battery:
                            bat_state.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW'))
        
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
            instance2.HorizonPath3_imports[d] = instance2.SimPath3_imports[day-1+d]
            instance2.HorizonPath8_imports[d] = instance2.SimPath8_imports[day-1+d]
            instance2.HorizonPath14_imports[d] = instance2.SimPath14_imports[day-1+d]
            instance2.HorizonPath65_imports[d] = instance2.SimPath65_imports[day-1+d]
            instance2.HorizonPath66_imports[d] = instance2.SimPath66_imports[day-1+d]
            instance2.HorizonPNW_hydro[d] = instance2.SimPNW_hydro[day-1+d]
            
        for i in K:
            instance2.HorizonReserves[i] = instance2.SimReserves[(day-1)*24+i] 
            instance2.HorizonPath3_exports[i] = instance2.SimPath3_exports[(day-1)*24+i] 
            instance2.HorizonPath8_exports[i] = instance2.SimPath8_exports[(day-1)*24+i] 
            instance2.HorizonPath14_exports[i] = instance2.SimPath14_exports[(day-1)*24+i]
            instance2.HorizonPath65_exports[i] = instance2.SimPath65_exports[(day-1)*24+i]             
            instance2.HorizonPath66_exports[i] = instance2.SimPath66_exports[(day-1)*24+i]  
            
            instance2.HorizonPath3_minflow[i] = instance2.SimPath3_imports_minflow[(day-1)*24+i]             
            instance2.HorizonPath8_minflow[i] = instance2.SimPath8_imports_minflow[(day-1)*24+i]             
            instance2.HorizonPath14_minflow[i] = instance2.SimPath14_imports_minflow[(day-1)*24+i]             
            instance2.HorizonPath65_minflow[i] = instance2.SimPath65_imports_minflow[(day-1)*24+i]  
            instance2.HorizonPath66_minflow[i] = instance2.SimPath66_imports_minflow[(day-1)*24+i]  
            instance2.HorizonPNW_hydro_minflow[i] = instance2.SimPNW_hydro_minflow[(day-1)*24+i]
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
#        for j in instance.Zone5Battery:
#            for t in K:
#                if instance.bat_dis_on[j,t] == 1:
#                    instance2.bat_dis_on[j,t] = 1
#                    instance2.bat_dis_on[j,t].fixed = True                    
#                else:
#                    instance.bat_dis_on[j,t] = 0
#                    instance2.bat_dis_on[j,t] = 0
#                    instance2.bat_dis_on[j,t].fixed = True                    
#
#                if instance.bat_charge_on[j,t] == 1:
#                    instance2.bat_charge_on[j,t] = 1
#                    instance2.bat_charge_on[j,t].fixed = True                    
#                else:
#                    instance.bat_charge_on[j,t] = 0
#                    instance2.bat_charge_on[j,t] = 0
#                    instance2.bat_charge_on[j,t].fixed = True                      

        results = opt.solve(instance2,tee=True,symbolic_solver_labels=True, load_solutions=False)
        instance2.solutions.load_from(results)   
        
        
        print ("Duals")
        
        # Define curtailment as any time when wind dispatched by the model (e.g., the sum of model.wind for a given hour, zone)
        # is less than the amount of wind that could be dispatched, (i.e .the value of SimWind for the same zone, hour).
        # (reported on a daily basis)

        #append curtailment based on difference between amount dispatched and amount that could be dispatched
        for i in range(1,25):
            wind_cur = float(instance2.HorizonWind['PNW',i].value or 0) - float(instance2.wind['PNW',i].value or 0)
            solar_cur = float(instance2.HorizonSolar['PNW',i].value or 0) - float(instance2.solar['PNW',i].value or 0)
            wind_curtailment.append(wind_cur)
            solar_curtailment.append(solar_cur)
    
        for c in instance2.component_objects(Constraint, active=True):
    #        print ("   Constraint",c)
            cobject = getattr(instance2, str(c))
            if str(c) == 'Bal5Constraint':
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
                if index[0] in instance.Zone5Generators:
                    
                    gas_price = instance.GasPrice['PNW'].value
                    
                    
                    if index[0] in instance.Gas:
                        marginal_cost = seg1*gas_price
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','Gas',marginal_cost))                  
                    elif index[0] in instance.Coal:
                        marginal_cost = seg1*2
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','Coal',marginal_cost))
                    elif index[0] in instance.Oil:
                        marginal_cost = seg1*20
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','Oil',marginal_cost))
                    elif index[0] in instance.Nuclear:
                        marginal_cost = 10
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','Nuclear',marginal_cost))
                    elif index[0] in instance.PSH:
                        marginal_cost = 10
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','PSH',marginal_cost))
                    elif index[0] in instance.Slack:
                        marginal_cost = 700
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','Slack',marginal_cost))               
                    elif index[0] in instance.Hydro:
                        marginal_cost = 0
                        mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','Hydro',marginal_cost))                
                        
                
        
                elif index[0] in instance.WECCImports:
                    mwh_1.append((index[0],index[1]+((day-1)*24),varobject[index].value,'WECC','imports',0))
                      
    
            if a=='mwh_2':
           
             for index in varobject:
                 
               name = index[0]     
               g = df_generators[df_generators['name']==name]
               seg2 = g['seg2'].values
               seg2 = seg2[0]  
    
               if int(index[1]>0 and index[1]<25):
                if index[0] in instance.Zone5Generators:
                    
                    gas_price = instance.GasPrice['PNW'].value
                    
                    if index[0] in instance.Gas:
                        marginal_cost = seg2*gas_price
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','Gas',marginal_cost))                  
                    elif index[0] in instance.Coal:
                        marginal_cost = seg2*2
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','Coal',marginal_cost))
                    elif index[0] in instance.Oil:
                        marginal_cost = seg2*20
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','Oil',marginal_cost))
                    elif index[0] in instance.Nuclear:
                        marginal_cost = 10
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','Nuclear',marginal_cost))
                    elif index[0] in instance.PSH:
                        marginal_cost = 10
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','PSH',marginal_cost))
                    elif index[0] in instance.Slack:
                        marginal_cost = 700
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','Slack',marginal_cost))               
                    elif index[0] in instance.Hydro:
                        marginal_cost = 0
                        mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','Hydro',marginal_cost))         
                
                elif index[0] in instance.WECCImports:
                    mwh_2.append((index[0],index[1]+((day-1)*24),varobject[index].value,'WECC','imports',0))
     
            
            if a=='mwh_3':
               
             for index in varobject:
                 
               name = index[0]     
               g = df_generators[df_generators['name']==name]
               seg3 = g['seg3'].values
               seg3 = seg3[0]  
                 
               if int(index[1]>0 and index[1]<25):
                if index[0] in instance.Zone5Generators:
                    
                    gas_price = instance.GasPrice['PNW'].value
                    
                    if index[0] in instance.Gas:
                        marginal_cost = seg3*gas_price
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','Gas',marginal_cost))                  
                    elif index[0] in instance.Coal:
                        marginal_cost = seg3*2
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','Coal',marginal_cost))
                    elif index[0] in instance.Oil:
                        marginal_cost = seg3*20
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','Oil',marginal_cost))
                    elif index[0] in instance.Nuclear:
                        marginal_cost = 10
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','Nuclear',marginal_cost))
                    elif index[0] in instance.PSH:
                        marginal_cost = 10
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','PSH',marginal_cost))
                    elif index[0] in instance.Slack:
                        marginal_cost = 700
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','Slack',marginal_cost))               
                    elif index[0] in instance.Hydro:
                        marginal_cost = 0
                        mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW','Hydro',marginal_cost))         
                
                elif index[0] in instance.WECCImports:
                    mwh_3.append((index[0],index[1]+((day-1)*24),varobject[index].value,'WECC','imports',0))
        
       
            if a=='on':
                
             for index in varobject:
               if int(index[1]>0 and index[1]<25):
                if index[0] in instance.Zone5Generators:
                 on.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW'))
                 
            if a == 'bat_discharge':
                
                for index in varobject:
                    if int(index[1]>0 and index[1]<25):
                        if index[0] in instance.Zone5Battery:
                            battery_discharge.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW'))

            if a == 'bat_charge':
                
                for index in varobject:
                    if int(index[1]>0 and index[1]<25):
                        if index[0] in instance.Zone5Battery:
                            battery_charge.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW'))


            if a == 'bat_SoC':
                
                for index in varobject:
                    if int(index[1]>0 and index[1]<25):
                        if index[0] in instance.Zone5Battery:
                            battery_state.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW'))
             
            if a=='switch':
            
             for index in varobject:
               if int(index[1]>0 and index[1]<25):
                if index[0] in instance.Zone5Generators:
                 switch.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW'))
               
        
             
            if a=='srsv':
            
             for index in varobject:
               if int(index[1]>0 and index[1]<25):
                if index[0] in instance.Zone5Generators:
                 srsv.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW'))
              
        
             
            if a=='nrsv':
           
             for index in varobject:
               if int(index[1]>0 and index[1]<25):
                if index[0] in instance.Zone5Generators:
                 nrsv.append((index[0],index[1]+((day-1)*24),varobject[index].value,'PNW'))
               
             
             
            if a=='solar':
               
             for index in varobject:
               if int(index[1]>0 and index[1]<25):
                solar.append((index[0],index[1]+((day-1)*24),varobject[index].value))   
             
              
            if a=='wind':
               
             for index in varobject:
               if int(index[1]>0 and index[1]<25):
                wind.append((index[0],index[1]+((day-1)*24),varobject[index].value))  
                   
            for j in instance.Generators:
                if instance.on[j,H] == 1:
                    instance.on[j,0] = 1
                else: 
                    instance.on[j,0] = 0
                instance.on[j,0].fixed = True
                           
                if instance.mwh_1[j,H].value <=0 and instance.mwh_1[j,H].value>= -0.0001:
                    newval_1=0
                else:
                    newval_1=instance.mwh_1[j,H].value
                instance.mwh_1[j,0] = newval_1
                instance.mwh_1[j,0].fixed = True
                              
                if instance.mwh_2[j,H].value <=0 and instance.mwh_2[j,H].value>= -0.0001:
                    newval=0
                else:
                    newval=instance.mwh_2[j,H].value
                                         
                if instance.mwh_3[j,H].value <=0 and instance.mwh_3[j,H].value>= -0.0001:
                    newval2=0
                else:
                    newval2=instance.mwh_3[j,H].value
                                          
                                          
                instance.mwh_2[j,0] = newval
                instance.mwh_2[j,0].fixed = True
                instance.mwh_3[j,0] = newval2
                instance.mwh_3[j,0].fixed = True 
                if instance.switch[j,H] == 1:
                    instance.switch[j,0] = 1
                else:
                    instance.switch[j,0] = 0
                instance.switch[j,0].fixed = True
              
                if instance.srsv[j,H].value <=0 and instance.srsv[j,H].value>= -0.0001:
                    newval_srsv=0
                else:
                    newval_srsv=instance.srsv[j,H].value
                instance.srsv[j,0] = newval_srsv 
                instance.srsv[j,0].fixed = True        
        
                if instance.nrsv[j,H].value <=0 and instance.nrsv[j,H].value>= -0.0001:
                    newval_nrsv=0
                else:
                    newval_nrsv=instance.nrsv[j,H].value
                instance.nrsv[j,0] = newval_nrsv 
                instance.nrsv[j,0].fixed = True        
                   
            for j in instance.Zone5Battery:
                              
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
    shadow_price=pd.DataFrame(Duals,columns=('Constraint','Time','Value'))
    objective = pd.DataFrame(System_cost)
    
    #sum curtailment every 24 hours to get a daily value
    for i in range(365):
        wind_curtailment_daily.append(sum(wind_curtailment[i*24:24*(1+i)]))
        solar_curtailment_daily.append(sum(solar_curtailment[i*24:24*(1+i)]))
    
    #output curtailment to dataframe and then csv
    wind_curtailment_pd = pd.DataFrame(wind_curtailment_daily)
    solar_curtailment_pd = pd.DataFrame(solar_curtailment_daily)
    wind_curtailment_pd.to_csv('wind_curtailment_daily.csv')
    solar_curtailment_pd.to_csv('solar_curtailment_daily.csv')
        
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
