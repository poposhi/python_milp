# coding=utf-8
import numpy as np
import pandas as pd
from pandas import DataFrame, Series
import matplotlib.pyplot as plt
#我要做一個表格 呼叫 Index key

ii =['a','b','c','d']
dd=DataFrame({'key1':[1,2,3,4],'key2':[2,2,3,4],'key3':[3,2,3,4]},index=ii)

# print( dd.head())

# print(dd.key1) #假如呼叫 key 會回傳一個小表格 
# print(dd.key1[1:]) #r.production[1:] 回傳一個表格 從第二個到最後一個 
# print(dd.loc['a'])

ar=np.array(range(24))
print(ar.shape)


ar=np.array([range(24)]).T
print(ar.shape)



'''
{
	// Place your snippets for python here. Each snippet is defined under a snippet name and has a prefix, body and 
	// description. The prefix is what is used to trigger the snippet and the body will be expanded and inserted. Possible variables are:
	// $1, $2 for tab stops, $0 for the final cursor position, and ${1:label}, ${2:another} for placeholders. Placeholders with the 
	// same ids are connected.
	// Example:
	// "Print to console": {
	// 	"prefix": "log",
	// 	"body": [
	// 		"console.log('$1');",
	// 		"$2"
	// 	],
	// 	"description": "Log output to console"
	// }
	"folding code": {
	"prefix": "rrr",
	 	"body": "#region $1",
		 "description": "region"
	},
	"folding code2":{
		"prefix": "eee",
			 "body": "#endregion $1",
			 "description": "endregion"
		},
	"print1":{
		"prefix": "ppp",
		"body": "print($1)",
		"description": "print1"
		},
	"type":{
		"prefix": "ptt",
		"body": "print(type($1))",
		"description": "type1"
		},
}
'''