import os
import pandas as pd
import openpyxl

data = []

def Primary(Contract_Dir):

	Contract_List = os.listdir(Contract_Dir)

	for contract in Contract_List:

		funcs = []
		funcs.append(contract)
		file = open(Contract_Dir + contract, 'r')
		lines = file.readlines()

		try:
			for line in lines:
				name = ''
				# Positioning function location
				if 'func' in line and 'external' not in line and '*' not in line and '/' not in line and 'is' not in line and '@' not in line:
					pos = line.find('func')
					pos += 5
					if 'function' in line:
						pos += 4
					# print(line[pos])
					while pos != len(line) and line[pos] != ' ' and line[pos] != '(':
						name += line[pos]
						pos += 1
					if name not in funcs:
						if name[0].isalpha() or name[0] == '_':
							funcs.append(name)
		except BaseException:
			print(contract + " appears line error!")
		data.append(funcs)
		# print(funcs)

	df = pd.DataFrame(data)

	writer = pd.ExcelWriter('./data/fun_name.xls')
	df.to_excel(writer, sheet_name='Sheet1', index=False, engine='openpyxl')
	writer.close()