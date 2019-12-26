# coding=utf-8
import pandas as pd
from pandas import DataFrame, Series

#我要做一個表格 呼叫 Index key

ii =['a','b','c','d']
dd=DataFrame({'key1':[1,2,3,4],'key2':[2,2,3,4],'key3':[3,2,3,4]},index=ii)

print( dd.head())

# print(dd.key1) #假如呼叫 key 會回傳一個小表格 
# print(dd.key1[1:]) #r.production[1:] 回傳一個表格 從第二個到最後一個 
print(dd.loc['a'])