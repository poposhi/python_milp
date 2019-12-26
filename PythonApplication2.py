import pandas as pd



import random
n = 10
m = 5
set_I = range(1, n+1) #1-11
set_J = range(1, m+1) #1-6
c = {(i,j): random.normalvariate(0,1) for i in set_I for j in set_J}
a = {(i,j): random.normalvariate(0,5) for i in set_I for j in set_J}
l = {(i,j): random.randint(0,10) for i in set_I for j in set_J}
u = {(i,j): random.randint(10,20) for i in set_I for j in set_J}
b = {j: random.randint(0,30) for j in set_J}

print(c)
print(c[1,1])
print(type(c))
print("000")


#data = pd.DataFrame({"name":["a","b"] ,"money":[100,91]})
#print(data)
#print("\n")
#print(data.iloc[0])
#print("\n\r")
#print(data["name"])
