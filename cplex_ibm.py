
# coding=utf-8
# 很重要的教學網站  https://medium.com/opex-analytics/optimization-modeling-in-python-pulp-gurobi-and-cplex-83a62129807a
#程式碼主要參考網站  https://dataplatform.cloud.ibm.com/exchange/public/entry/view/a9df9c4e022991268fad26117f579b44
import pandas as pd
from pandas import DataFrame, Series

# make matplotlib plots appear inside the notebook
import matplotlib.pyplot as plt
#%matplotlib inline
from pylab import rcParams
rcParams['figure.figsize'] = 20, 10 ############################ <-Use this to change the plot
#from IPython.core.display import HTML
#HTML("<style>.container { width:100%; }</style>")


'''準備資料  有四種發電來源 利用pandas做成表格  不同發電來源排碳成本的表格 '''
energies = ["coal", "gas", "diesel", "wind"]
df_energy = DataFrame({"co2_cost": [30, 5, 15, 0]}, index=energies)



'''有很多部機組   不同的單位有不同的特性   variable_cost 不知道是什麼東西 
 變成表格 key 會變成row  直軸的index  每個機組的名稱 最後變成直軸是每個機組的名稱 橫軸是機組特性 (最大最小功率)
 '''
all_units = ["coal1", "coal2", 
             "gas1", "gas2", "gas3", "gas4", 
             "diesel1", "diesel2", "diesel3", "diesel4"]

ucp_raw_unit_data = {
        "energy": ["coal", "coal", "gas", "gas", "gas", "gas", "diesel", "diesel", "diesel", "diesel"],
        "initial" : [400, 350, 205, 52, 155, 150, 78, 76, 0, 0],
        "min_gen": [100, 140, 78, 52, 54.25, 39, 17.4, 15.2, 4, 2.4],
        "max_gen": [425, 365, 220, 210, 165, 158, 90, 87, 20, 12],
        "operating_max_gen": [400, 350, 205, 197, 155, 150, 78, 76, 20, 12],
        "min_uptime": [15, 15, 6, 5, 5, 4, 3, 3, 1, 1],
        "min_downtime":[9, 8, 7, 4, 3, 2, 2, 2, 1, 1],
        "ramp_up":   [212, 150, 101.2, 94.8, 58, 50, 40, 60, 20, 12],
        "ramp_down": [183, 198, 95.6, 101.7, 77.5, 60, 24, 45, 20, 12],
        "start_cost": [5000, 4550, 1320, 1291, 1280, 1105, 560, 554, 300, 250],
        "fixed_cost": [208.61, 117.37, 174.12, 172.75, 95.353, 144.52, 54.417, 54.551, 79.638, 16.259],
        "variable_cost": [22.536, 31.985, 70.5, 69, 32.146, 54.84, 40.222, 40.522, 116.33, 76.642],
        }
df_units = DataFrame(ucp_raw_unit_data, index=all_units)



print(df_units.index)
print(df_units["energy"]) #回傳名稱與直行



'''
根據clomn名稱("energy")合併兩個表格，保留右邊的index ，條列出前面5項 並且添加排碳成本 ，再額外設定Index名稱
然後顯示前5行資料  left_on right_index 還不知道做什麼的請參考  https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.merge.html
'''
df_up = pd.merge(df_units, df_energy, left_on="energy", right_index=True)
df_up.index.names=['units'] 

# Display first rows of new 'df_up' Data Frame
df_up.head()
''' 總共有168小時的負載，印出來他的長度，把它放入一維陣列Series，並且設定好index 然後畫出來  '''

raw_demand = [1196,1193,1191,1193,1207,1243,1293,1337,1383,1411,1430,1440,1433,1437,1437,1431,
              1414,1389,1363,1350,1357,1351,1329,1306,1289,1277,1264,1255,1257,1285,1328,1361,
              1394,1417,1436,1440,1432,1434,1432,1422,1407,1386,1364,1354,1362,1356,1334,1310,
              1289,1276,1264,1254,1256,1285,1327,1360,1394,1417,1436,1441,1433,1435,1433,1423,
              1408,1388,1365,1355,1363,1357,1335,1311,1289,1277,1265,1255,1258,1286,1329,1362,
              1396,1420,1439,1443,1435,1437,1435,1425,1410,1389,1367,1356,1364,1359,1336,1313,
              1295,1281,1269,1264,1269,1294,1338,1368,1402,1427,1446,1448,1437,1439,1434,1422,
              1411,1385,1358,1340,1345,1333,1307,1282,1259,1245,1231,1221,1216,1224,1236,1243,
              1262,1280,1294,1302,1300,1294,1287,1279,1275,1265,1255,1246,1244,1235,1219,1199,
              1184,1172,1163,1162,1158,1160,1164,1160,1174,1191,1205,1220,1227,1232,1235,1235,
              1233,1230,1217,1205,1207,1215,1211,1207]
nb_periods = len(raw_demand)
print("nb periods = {}".format(nb_periods))

demand = Series(raw_demand, index = range(1, nb_periods+1))

# plot demand
demand.plot(title="Demand")

'''  顯示目前環境 創建一個 model'''
import docplex
from docplex.mp.environment import Environment
env = Environment()
env.print_information()
from docplex.mp.model import Model

ucpm = Model("ucp") #模型選擇經濟調度優化問題 The Unit Commitment Problem (UCP)


'''  模型選擇經濟調度優化問題 '''
units = all_units
# 時間長度  range from 1 to nb_periods included
periods = range(1, nb_periods+1) 

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

# 把整個優化變數的 屬性 列印出來
ucpm.print_information()


'''整理優化變數''' 
# 把所有的優化變數在整合成一個表格，增加兩個index，機組名稱 與時間 每個基礎每個時間的優化變數  
df_decision_vars = DataFrame({'in_use': in_use, 'turn_on': turn_on, 'turn_off': turn_off, 'production': production})
# Set index names
df_decision_vars.index.names=['units', 'periods']

# 顯示“ df_decision_vars”數據框的前幾行
df_decision_vars.head()
'''把df_up裡面的最大發電量最小發電量 合併過來 ，使用的方法是 join，利用共同的index  units '''
# Create a join between 'df_decision_vars' and 'df_up' Data Frames based on common index id (ie: 'units')
# In 'df_up', one keeps only relevant columns: 'min_gen' and 'max_gen'
df_join_decision_vars_up = df_decision_vars.join(df_up[['min_gen', 'max_gen']], how='inner')

# Display first few rows of joined Data Frames
df_join_decision_vars_up.head()

''' 限制通常有三個部分 ，左邊是優化變數的線性組合 右邊是數值 中間是等式不等式 '''
# 功率要在最大到最小之間  疊代每個行 INDEX If True 會回傳每行的第一個 疊代每一個機組的每一個小時  
for item in df_join_decision_vars_up.itertuples(index=False):
    ucpm += (item.production <= item.max_gen * item.in_use)
    ucpm += (item.production >= item.min_gen * item.in_use)
        #這應該是限制式才對但是為什麼沒有 
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
ucpm.print_information()

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

ucpm.print_information()


# Enforcing demand 電力供需平衡 
# use a >= here to be more robust, 
# objective will ensure efficient production
for period, r in df_decision_vars.groupby(level='periods'):
    total_demand = demand[period]
    ctname = "ct_meet_demand_%d" % period
    ucpm.add_constraint(ucpm.sum(r.production) >= total_demand, ctname)

'''創建了一個新的表格 包含了成本特性  設定目標函數 最小化全部的成本加在一起 
'''
# Create a join between 'df_decision_vars' and 'df_up' Data Frames based on common index ids (ie: 'units')
# In 'df_up', one keeps only relevant columns: 'fixed_cost', 'variable_cost', 'start_cost' and 'co2_cost'
df_join_obj = df_decision_vars.join(
    df_up[['fixed_cost', 'variable_cost', 'start_cost', 'co2_cost']], how='inner')

# Display first few rows of joined Data Frame
df_join_obj.head()

# objective
total_fixed_cost = ucpm.sum(df_join_obj.in_use * df_join_obj.fixed_cost) # 有在使用就會產生固定成本 
total_variable_cost = ucpm.sum(df_join_obj.production * df_join_obj.variable_cost) #功率大小會影響變動成本 
total_startup_cost = ucpm.sum(df_join_obj.turn_on * df_join_obj.start_cost) #啟動成本會跟啟動次數有關係 
total_co2_cost = ucpm.sum(df_join_obj.production * df_join_obj.co2_cost) #
total_economic_cost = total_fixed_cost + total_variable_cost + total_startup_cost

total_nb_used = ucpm.sum(df_decision_vars.in_use) #總共使用時間 
total_nb_starts = ucpm.sum(df_decision_vars.turn_on) #總共開啟次數 

# store expression kpis to retrieve them later.
ucpm.add_kpi(total_fixed_cost   , "Total Fixed Cost")
ucpm.add_kpi(total_variable_cost, "Total Variable Cost")
ucpm.add_kpi(total_startup_cost , "Total Startup Cost")
ucpm.add_kpi(total_economic_cost, "Total Economic Cost")
ucpm.add_kpi(total_co2_cost     , "Total CO2 Cost")
ucpm.add_kpi(total_nb_used, "Total #used")
ucpm.add_kpi(total_nb_starts, "Total #starts")

# minimize sum of all costs
ucpm.minimize(total_fixed_cost + total_variable_cost + total_startup_cost + total_co2_cost)


ucpm.print_information()
assert ucpm.solve(), "!!! Solve of the model fails" #斷定解答一定存在不然就回傳字串 
ucpm.report()

'''
不需要的程式嗎 
優化變數有三種 連續，二元，整數 ，通常會跟字典或pandas搭配 
這邊利用雙重迴圈 來定義二維變數 
lb=l[i,j], ub= u[i,j]每一個的上下限制 
# if x is Continuous
x_vars  = 
{(i,j): opt_model.continuous_var(lb=l[i,j], ub= u[i,j],
                                 name="x_{0}_{1}".format(i,j)) 
for i in set_I for j in set_J}
# if x is Binary
x_vars  = 
{(i,j): opt_model.binary_var(name="x_{0}_{1}".format(i,j)) 
for i in set_I for j in set_J}
# if x is Integer
x_vars  = 
{(i,j): opt_model.integer_var(lb=l[i,j], ub= u[i,j],
                              name="x_{0}_{1}".format(i,j)) 
for i in set_I for j in set_J}

 '''