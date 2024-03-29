#region  import
# coding=utf-8
import pandas as pd
from pandas import DataFrame, Series
import matplotlib.pyplot as plt
from pylab import rcParams
rcParams['figure.figsize'] = 20, 10 
import numpy as np

'''  顯示目前環境 創建一個 model'''
import docplex
from docplex.mp.environment import Environment
env = Environment()
# env.print_information()
from docplex.mp.model import Model
#endregion 
#region 設定負載與變數 參數
ucpm = Model("ucp") #模型選擇經濟調度優化問題 The Unit Commitment Problem (UCP)

loadprofile=[30,39,37,37,37,39,50,77,100,125,125,125,125,125,110,100,93,109,92,85,78,66,53,42]
load_small=[30,39,37,37,37,39,50,77,100,125,125,125,125,125,110,100,93,109,60,20,30,10,10,15]
pv_power_sun=[0,0,0,0,10,30,50,65,80,90,100,95,90,80,65,40,30,8,0,0,0,0,0,0]#晴天
pv_power_cloud=[0,0,0,0,10,30,30,50,30,20,80,20,40,50,30,20,10,0,0,0,0,0,0,0] #陰天
pv_power = pv_power_cloud
pv_power=Series(pv_power)
loadprofile= Series(loadprofile)
net_loadprofile=loadprofile-pv_power
#region 儲能系統參數

NOMb = 100 #標稱電池容量,單位為kWh
NOMbInit = 30 #初始標稱電池容量,單位為kWh
SOC_init =0.5
SOCmin = 0.1 #電池充電狀態(最小)
SOCmax =0.9
SOC_final =0.8
ESS_Ch_max = 100 #Battery max允許以MW為單位的充電功率
ESS_Disch_max = 100 #Battery max允許以MW為單位的放電功率，放電功率是正的 
efficiency=0.9#充放電效率都假設一樣 
ESS_disch_cost=15#磨損成本係數 每MWh需要多少錢 

#endregion 
#endregion 

nb_periods = len(net_loadprofile)



# print("nb periods = {}".format(nb_periods))
# print("pv_power_sun = {}".format(len(pv_power_sun) ))
demand = Series(net_loadprofile, index = range(0, nb_periods))
# print(demand)
energies = ["coal", "gas", "diesel", "wind"]
df_energy = DataFrame({"co2_cost": [30, 5, 15, 0]}, index=energies)


# plot demand
#demand.plot(title="Demand")
# 先用一台來滿足
'''有很多部機組   不同的單位有不同的特性   variable_cost 不知道是什麼東西 
 變成表格 key 會變成row  直軸的index  每個機組的名稱 最後變成直軸是每個機組的名稱 橫軸是機組特性 (最大最小功率)
 '''
all_units = ["diesel1"]
ess_index = ["ess1"]
ucp_raw_unit_data = {
        "energy": ["diesel"],
        "initial" : [35],
        "min_gen": [35],
        "max_gen": [125],
        "operating_max_gen": [120],
        "min_uptime": [24],
        "min_downtime":[24],
        "ramp_up":   [120],
        "ramp_down": [120],
        "start_cost": [9990],
        "fixed_cost": [0],
        "variable_cost": [20],
        }
ucp_raw_ess_data = {
        "energy": ["ess"],
        "initial" : [0],
        "max_ch": [100],
        "max_disch": [100],
        "operating_max_gen": [100],
        "min_uptime": [0],
        "min_downtime":[0],
        "ramp_up":   [9999],
        "ramp_down": [9999],
        "start_cost": [0],
        "fixed_cost": [0],
        "variable_cost": [15],
        }
df_units = DataFrame(ucp_raw_unit_data, index=all_units)
ess_unit = DataFrame(ucp_raw_ess_data, index=ess_index)
# print(df_units.index)
# print(df_units["energy"]) #回傳名稱與直行

'''
根據clomn名稱("energy")合併兩個表格，保留右邊的index ，條列出前面5項 並且添加排碳成本 ，再額外設定Index名稱
然後顯示前5行資料  left_on right_index 還不知道做什麼的請參考  https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.merge.html
'''
df_up = pd.merge(df_units, df_energy, left_on="energy", right_index=True)
df_up.index.names=['units'] 
ess_unit.index.names=['ess_unit'] 


units = all_units
ess = ["ess1"]
# 時間長度  range from 1 to nb_periods included
periods = range(0, nb_periods) 
#region 定義優化變數 
# in use[u,t] is true iff unit u is in production at period t
#定義2元(0或1)變數矩陣，輸入兩個index
in_use = ucpm.binary_var_matrix(keys1=units, keys2=periods, name="in_use")

#是否開啟  true if unit u is turned on at period t
turn_on = ucpm.binary_var_matrix(keys1=units, keys2=periods, name="turn_on")

# 宣告是否關閉的優化變數 輸入兩個指標 機組 /時間 上下限制 名稱 
# modeled as a continuous 0-1 variable, more on this later
turn_off = ucpm.continuous_var_matrix(keys1=units, keys2=periods, lb=0, ub=1, name="turn_off")

# 每個機組的產量是一個連續變數 
production = ucpm.continuous_var_matrix(keys1=units, keys2=periods, name="p")

#region 儲能係統優化變數 
    #同一個時間只能充電或是放電 
charge_var = ucpm.binary_var_matrix(keys1=ess, keys2=periods, name="charge_var")
discharge_var = ucpm.binary_var_matrix(keys1=ess, keys2=periods, name="discharge_var")
    #儲能系統功率 
ess_ch_production = ucpm.continuous_var_matrix(keys1=ess, keys2=periods, name="ess_ch_production")
ess_disch_production = ucpm.continuous_var_matrix(keys1=ess, keys2=periods, name="ess_disch_production")
    #soc
ess_soc = ucpm.continuous_var_matrix(keys1=ess, keys2=periods, name="ess_soc")
#endregion 
# 把整個優化變數的 屬性 列印出來
# ucpm.print_information()

#endregion 

#region 把所有的優化變數在整合成一個表格，增加兩個index，機組名稱 與時間 每個基礎每個時間的優化變數  
df_decision_vars = DataFrame({'in_use': in_use, 'turn_on': turn_on, 'turn_off': turn_off, 'production': production})
df_decision_vars_ess =DataFrame({'charge_var': charge_var,'discharge_var' : discharge_var,'ess_ch_production' : ess_ch_production ,'ess_disch_production' : ess_disch_production,'ess_soc':ess_soc})
# Set index names
df_decision_vars.index.names=['units', 'periods']
df_decision_vars_ess.index.names=['ess_unit', 'periods']
#endregion 
df_decision_vars_ess.head()

#region  最大發電量最小發電量限制
'''把df_up裡面的最大發電量最小發電量 合併過來 ，使用的方法是 join，利用共同的index  units '''
# Create a join between 'df_decision_vars' and 'df_up' Data Frames based on common index id (ie: 'units')
# In 'df_up', one keeps only relevant columns: 'min_gen' and 'm_gen'
df_join_decision_vars_up = df_decision_vars.join(df_up[['min_gen', 'max_gen']], how='inner')
df_join_decision_vars_up.head()
#把電池上下功率限制 黏貼過來 
df_join_decision_vars_ess_minmax = df_decision_vars_ess.join(ess_unit[['max_ch', 'max_disch']], how='inner')
df_join_decision_vars_ess_minmax.head()

# 功率要在最大到最小之間  疊代每個行 INDEX If True 會回傳每行的第一個 疊代每一個機組的每一個小時  
for item in df_join_decision_vars_up.itertuples(index=False):
    ucpm += (item.production <= item.max_gen * item.in_use)
    ucpm += (item.production >= item.min_gen * item.in_use)
    #這應該是限制式才對但是為什麼沒有
for item in df_join_decision_vars_ess_minmax.itertuples(index=False):
    ucpm += (item.ess_disch_production <= item.max_disch * item.discharge_var)
    ucpm += (item.ess_disch_production >= 0)
    ucpm += (item.ess_ch_production <= item.max_ch * item.charge_var)
    ucpm += (item.ess_ch_production >= 0)
    ucpm += (item.ess_soc >= SOCmin)
    ucpm += (item.ess_soc <= SOCmax)
    ucpm += (item.charge_var + item.discharge_var <= 1 ) #同時間只會充電或是放電 
#endregion 
#region  Turn_on, turn_off 使用(In use)跟開關的關聯 
# Use groupby operation to process each unit
for unit, r in df_decision_vars.groupby(level='units'):
    for (in_use_curr, in_use_next, turn_on_next, turn_off_next) in zip(r.in_use, r.in_use[1:], r.turn_on[1:], r.turn_off[1:]):
        # if unit is off at time t and on at time t+1, then it was turned on at time t+1
        ucpm.add_constraint(in_use_next - in_use_curr <= turn_on_next)

        # if unit is on at time t and time t+1, then it was not turned on at time t+1
        # mdl.add_constraint(in_use_next + in_use_curr + turn_on_next <= 2)

        # if unit is on at time t and off at time t+1, then it was turned off at time t+1
        ucpm.add_constraint(in_use_curr - in_use_next + turn_on_next == turn_off_next)
ucpm.print_information()

#endregion 
#region 初始狀態
'''
初始狀態   假如剛開始有功率 turn_on in_use =1
If initial production is nonzero, then period #1 is not a turn_on
else turn_on equals in_use
Dual logic is implemented for turn_off 
疊代每個機組  
假如剛開始有發電就不需要打開 ，關掉 跟 使用中只有一個會等於1 
假如剛開始沒有發電 假如要使用就會打開 ，因為已經關掉了所以就不需要再關掉 
'''

for u in units:
    if df_up.initial[u] > 0: 
        #假如剛開始有發電就不需要 turn_on ，turn_off ，in_use為什麼兩個相加要等於1  
        # 假如剛開始有發電這個設備第一小時的turn_on =0  if u is already running, not starting up
        ucpm.add_constraint(turn_on[u, 1] == 0) #
        # turnoff iff not in use 假如沒有要繼續用就把它關掉 
        ucpm.add_constraint(turn_off[u, 1] + in_use[u, 1] == 1)
    else: 
        #假如剛開始沒有發電 turn on at 1 iff in use at 1
        ucpm.add_constraint(turn_on[u, 1] == in_use[u, 1])
        # 已經關掉了所以就不需要關掉 
        ucpm.add_constraint(turn_off[u, 1] == 0)
#ucpm.print_information()
#endregion 
#region 升降載限制
'''用groupby 對於每個機組每個小時  分組 並且取出這個機組的升降載限制 初始
還有他們的輸出功率 
'''

for unit, r in df_decision_vars.groupby(level='units'): #對於不同的幾組設定不同的限制 
    u_ramp_up = df_up.ramp_up[unit]
    u_ramp_down = df_up.ramp_down[unit]
    u_initial = df_up.initial[unit]
    # Initial ramp up/down
    # Note that r.production is a Series that can be indexed as an array (ie: first item index = 0)
    ucpm.add_constraint(r.production[0] - u_initial <= u_ramp_up) #第一小時的功率必須要有 升載限制
    ucpm.add_constraint(u_initial - r.production[0] <= u_ramp_down)#降載限制
    for (p_curr, p_next) in zip(r.production, r.production[1:]): #從第二個到最後一個 
        ucpm.add_constraint(p_next - p_curr <= u_ramp_up) #每1個小時的 升載限制
        ucpm.add_constraint(p_curr - p_next <= u_ramp_down) #每1個小時的 降載限制

#ucpm.print_information()
#endregion 
#region Minimum uptime, downtime
for unit, r in df_decision_vars.groupby(level='units'):
    min_uptime   = df_up.min_uptime[unit]
    min_downtime = df_up.min_downtime[unit]
    # Note that r.turn_on and r.in_use are Series that can be indexed as arrays (ie: first item index = 0)
    for t in range(min_uptime, nb_periods):
        ctname = "min_up_{0!s}_{1}".format(*r.index[t])
        ucpm.add_constraint(ucpm.sum(r.turn_on[(t - min_uptime) + 1:t + 1]) <= r.in_use[t], ctname)

    for t in range(min_downtime, nb_periods):
        ctname = "min_down_{0!s}_{1}".format(*r.index[t])
        ucpm.add_constraint(ucpm.sum(r.turn_off[(t - min_downtime) + 1:t + 1]) <= 1 - r.in_use[t], ctname)
#endregion

#region soc變動限制，現在的電量會等於上個時刻的電量，加上功率流動
'''  先把優化變數表格依照幾組分組 ，取出各個機組的規格 ，迭代相鄰的小時功率，設定限制條件 '''
for ess_unit, r in df_decision_vars_ess.groupby(level='ess_unit'): #對於不同的幾組設定不同的限制
    ucpm.add_constraint(NOMbInit - NOMb* r.ess_soc[1]  - r.ess_ch_production[0] * efficiency - r.ess_disch_production[0]/efficiency == 0) #初始化 
    for (p_ch_curr, p_disch_curr, soc_curr, soc_next) in zip(r.ess_ch_production,r.ess_disch_production,r.ess_soc, r.ess_soc[1:]): #從第二個到最後一個 
        ucpm.add_constraint(NOMb*soc_curr - NOMb*soc_next + p_ch_curr*efficiency - p_disch_curr/efficiency == 0)
        #效率只能假設一個  
        
#endregion 
#region 電力供需平衡 
# Enforcing demand 電力供需平衡 
# use a >= here to be more robust, 
# objective will ensure efficient production
for period, r in df_decision_vars.groupby(level='periods'):

    total_demand = demand[period] #period 1 與load 1 相同
    ctname = "ct_meet_demand_%d" % period
    #ucpm.add_constraint(ucpm.sum(r.production)+df_decision_vars_ess.loc['ess1',period].ess_production >= total_demand, ctname)
    ucpm.add_constraint(ucpm.sum(r.production) + 
    df_decision_vars_ess.loc['ess1',period].ess_disch_production*efficiency -
    df_decision_vars_ess.loc['ess1',period].ess_ch_production/efficiency  >= total_demand, ctname)
    # 所有機組的發電再加上儲能系統功率>= 負載功率
#endregion

#region 成本特性  設定目標函數 求解
'''創建了一個新的表格 包含了成本特性  設定目標函數 最小化全部的成本加在一起 
'''
# Create a join between 'df_decision_vars' and 'df_up' Data Frames based on common index ids (ie: 'units')
# In 'df_up', one keeps only relevant columns: 'fixed_cost', 'variable_cost', 'start_cost' and 'co2_cost'
df_join_obj = df_decision_vars.join(
    df_up[['fixed_cost', 'variable_cost', 'start_cost', 'co2_cost']], how='inner')
ess_unit = DataFrame(ucp_raw_ess_data, index=ess_index)
ess_unit.index.names=['ess_unit'] 
df_join_obj_ess = df_decision_vars_ess.join(
    ess_unit[['variable_cost']], how='inner')

# Display first few rows of joined Data Frame
df_join_obj.head()
df_join_obj_ess.head()

# objective
total_fixed_cost = ucpm.sum(df_join_obj.in_use * df_join_obj.fixed_cost) # 有在使用就會產生固定成本 
total_variable_cost = ucpm.sum(df_join_obj.production * df_join_obj.variable_cost) #功率大小會影響變動成本 
total_startup_cost = ucpm.sum(df_join_obj.turn_on * df_join_obj.start_cost) #啟動成本會跟啟動次數有關係 
total_co2_cost = ucpm.sum(df_join_obj.production * df_join_obj.co2_cost) #

total_ess_cost = ucpm.sum(df_join_obj_ess.ess_disch_production * df_join_obj_ess.variable_cost) #
total_economic_cost = total_fixed_cost + total_variable_cost + total_startup_cost + total_ess_cost

total_nb_used = ucpm.sum(df_decision_vars.in_use) #總共使用時間 
total_nb_starts = ucpm.sum(df_decision_vars.turn_on) #總共開啟次數 

# store expression kpis to retrieve them later.
ucpm.add_kpi(total_ess_cost   , "total ess cost")
ucpm.add_kpi(total_fixed_cost   , "Total Fixed Cost")
ucpm.add_kpi(total_variable_cost, "Total Variable Cost")
ucpm.add_kpi(total_startup_cost , "Total Startup Cost")
ucpm.add_kpi(total_economic_cost, "Total Economic Cost")
ucpm.add_kpi(total_co2_cost     , "Total CO2 Cost")
# ucpm.add_kpi(total_nb_used, "Total #used")
ucpm.add_kpi(total_nb_starts, "Total #starts")

# minimize sum of all costs
ucpm.minimize(total_economic_cost)


ucpm.print_information()
#ucpm.parameters.optimalitytarget = 3
assert ucpm.solve(), "!!! Solve of the model fails" #斷定解答一定存在不然就回傳字串 
ucpm.report()
#endregion


df_prods = df_decision_vars.production.apply(lambda v: max(0, v.solution_value)).unstack(level='units')
df_used = df_decision_vars.in_use.apply(lambda v: max(0, v.solution_value)).unstack(level='units')
df_started = df_decision_vars.turn_on.apply(lambda v: max(0, v.solution_value)).unstack(level='units')
df_ess_disch_p =df_decision_vars_ess.ess_disch_production.apply(lambda v: max(0, v.solution_value)).unstack(level='ess_unit')
df_ess_ch_p =df_decision_vars_ess.ess_ch_production.apply(lambda v: max(0, v.solution_value)).unstack(level='ess_unit')
df_ess_soc =df_decision_vars_ess.ess_soc.apply(lambda v: max(0, v.solution_value)).unstack(level='ess_unit')
# print(type(ucpm.objective_value))

print(str(ucpm.objective_value))
# print(type(df_ess_soc))
#region 畫圖區域 
fig, ax = plt.subplots(figsize=(10,10))
ar=np.array([range(24)]).T
ax.set_xticks(range(0, nb_periods))
ax.set_yticks(range(-25,150,20))
# print(len(nb_periods))
# print(len(range(1, nb_periods+1)))
# print(len(df_prods))
# xx=range(nb_periods)
ess_power = df_ess_disch_p- df_ess_ch_p
print(type(demand))
print(type(df_prods))
print(type(df_prods['diesel1']))
print(type(ess_power))

ax.plot(demand,label='net_load')
ax.plot(loadprofile,label='origin_load')
ax.bar(np.arange(24),df_prods['diesel1'],0.2,color='orange',label='diesel1')

ax.bar(np.arange(24)+0.2,ess_power['ess1'],0.2,color='blue',label='ess_power')
ax.bar(np.arange(24)+0.4,pv_power_sun,0.2,color='red',label='pv_power')
ax.plot(df_ess_soc['ess1']*100,label='soc')

ax.set_title('milp total_cost '+str(int (ucpm.objective_value)))

ax.legend()
plt.show()

# ax.plot(df_ess_disch_p,label='ess_disch_p')
# ax.plot(-df_ess_ch_p,label='ess_ch_p')
#endregion 

