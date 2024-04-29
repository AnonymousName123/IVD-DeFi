import pandas as pd
import os
import sys
from analyzer.detector.Bugs_Detect import Primary

getname_dir = "./contracts/"
# sys.setrecursionlimit(2000)

# Build tree recursively
def GetName(line, num, name_list):
	name = ''

	# Capture name position
	start = 0
	end = line.find('.sol')

	for i in range(len(line)):
		if line[i] == '/':
			start = i
	for i in range(start + 1, end):
		name += line[i]

	if name != '' and name not in name_list:
		name_list.append(name)
		file = open(getname_dir + name + '.sol', 'r')
		lines = file.readlines()
		file.close()

		name += '(' + str(num) + ')'+ '\n'
		for line in lines:
			if "import" in line:
				name += GetName(line, num + 1, name_list)
			elif '{' in line:
				name_list.pop()
				break
		return name
	else:
		return ''

# Calculate the sum of vulnerabilities according to the recursive tree
def CalculateBugs(data):
	ans = []
	file = open('./data/Tree.txt', 'r')
	lines = file.readlines()
	file.close()

	bugs = [0] * 6
	num = 0
	contract = ''
	for line in lines:
		if '.sol' in line:
			pos = line.find('.sol')
			for i in range(pos):
				contract += line[i]
			for sheet, df in data.items():
				bugs[0] += df.values[num][1]
				bugs[1] += df.values[num][2]
				bugs[2] += df.values[num][3]
				bugs[3] += df.values[num][4]
				bugs[4] += df.values[num][5]
				bugs[5] += df.values[num][6]

		elif '(' in line:
			name = ''
			pos = line.find('(')
			for i in range(pos):
				name += line[i]
			i = 0
			name += '.sol'
			for sheet, df in data.items():
				for row in df.values:
					if row[0] == name:
						bugs[0] += df.values[i][1]
						bugs[1] += df.values[i][2]
						bugs[2] += df.values[i][3]
						bugs[3] += df.values[i][4]
						bugs[4] += df.values[i][5]
						bugs[5] += df.values[i][6]
						break
					else:
						i += 1

		else:
			ans.append((contract, bugs[0], bugs[1], bugs[2], bugs[3], bugs[4], bugs[5]))
			contract = ''
			num += 1
			bugs = [0] * 6

	header = ['Contract_Name', 'BN', 'DC', 'DS', 'OF', 'RE', 'UE']
	df = pd.DataFrame(ans, columns=header)

	writer = pd.ExcelWriter('./data/ProtocolBugs.xls')
	df.to_excel(writer, sheet_name='Sheet1', index=False)
	writer.close()

def Interact(Contract_Dir):

	Primary(Contract_Dir)

	# print(Contract_List)

	data = pd.read_excel('./data/ContractBugs.xls', sheet_name=[0], skiprows=0)
	tree = ''
	for sheet, df in data.items():
		for row in df.values:
			try:
				tree += row[0] + '(Root)' + '\n'
				file = open(Contract_Dir + row[0], 'r')

				root_name = ''
				for c in range(row[0].find('.sol')):
					root_name += row[0][c]
				name_list = [root_name] # A certain path calls the contract list

				# print(row[0])
				lines = file.readlines()
				file.close()
				for line in lines:
					if "import" in line:
						# 递归
						name = GetName(line, 1, name_list)
						if name != '':
							tree += name
				tree += '-' * 30 + '\n'
			except BaseException:
			 	print(row[0] + ": Part of the contract is missing!")
	# print(tree)

	file = open('./data/Tree.txt', 'w')
	file.write(tree)
	file.close()

	CalculateBugs(data)
