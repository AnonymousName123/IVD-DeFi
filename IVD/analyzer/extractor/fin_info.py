import os
import pandas as pd
import openpyxl
from analyzer.extractor.get_fun_name import Primary

keywords = []

# Capture keywords
def FunctionTypeDetect(name):

	func = []
	for row in range(len(keywords)):
		flag = False
		for pos in range(len(keywords[row])):
			if pd.isna(keywords[row][pos]):
				break
			# The name is uniformly identified by lowercase
			if keywords[row][pos] in name.lower():
				flag = True
				break
		if flag:
			func.append(1)
		else:
			func.append(0)
	return func

def FinanceInformation(Contract_Dir):

	Primary(Contract_Dir)

	data = pd.read_excel('./data/keyword.xls', sheet_name=[0], skiprows=0)

	# Build keyword library
	for sheet, df in data.items():
	    for row in df.values:
	    	# print(row[0])
	    	words = []
	    	for i in range(1, len(row)):
	    		words.append(row[i])
	    	# print(words)
	    	keywords.append(words)
	
	# Query function keyword
	ans = []
	data = pd.read_excel('./data/fun_name.xls', sheet_name=[0], skiprows=0)
	for sheet, df in data.items():
	    for row in df.values:
	    	func_type = [0] * len(keywords)
	    	for i in range(1, len(row)):

	    		# Exclude NAN
	    		if pd.isna(row[i]):
	    			break

	    		tmp_func_type = FunctionTypeDetect(row[i])
	    		func_type = [sum(element) for element in zip(func_type, tmp_func_type)]

	    	ans.append((row[0], func_type[0], func_type[1], func_type[2], func_type[3], func_type[4], func_type[5], func_type[6], func_type[7], func_type[8]))

	header = ['Contract_Name', 'Ct', 'Hash', 'Lq', 'Math', 'Oc', 'Op', 'Sv', 'Tk', 'Tx']
	df = pd.DataFrame(ans, columns=header)

	writer = pd.ExcelWriter('./data/func_type.xls')
	df.to_excel(writer, sheet_name='Sheet1', index=False)
	writer.close()

if __name__ == '__main__':
	main()