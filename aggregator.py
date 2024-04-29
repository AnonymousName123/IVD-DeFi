import os
import json
import jsonlines
import openpyxl
import pandas as pd
from analyzer.detector.Interact import Interact
from analyzer.extractor.fin_info import FinanceInformation

data = {}
contract_name = []
features = []
keywords = []

# Get Keywords
def GetKeywords():
	data = pd.read_excel('./data/keyword.xls', sheet_name=[0], skiprows=0)

	# Build keyword library
	for sheet, df in data.items():
		for row in df.values:
			words = []
			for i in range(1, len(row)):
				words.append(row[i])
			keywords.append(words)

# Get contract name
def GetName(line):
	if '.' in line:
		pos = line.find('.')
	else:
		pos = line.find('(')
	name = ''
	for i in range(pos):
		name += line[i]
	return name

def AppendData(seq):
	seq_data = {}
	for name in seq:
		pos = contract_name.index(name)
		seq_data[name] = features[pos]
	data[len(data) + 1] = seq_data

def GetContractType(contract_name):
	if contract_name[0] == 'I' and contract_name[1].isupper():
		return 10

	for row in range(len(keywords)):
		for pos in range(len(keywords[row])):
			if pd.isna(keywords[row][pos]):
				break
			# The name is uniformly identified by lowercase
			if keywords[row][pos] in contract_name.lower():
				return row

	return 0

def aggregate():

	Contract_Dir = "./contracts/"
	Interact(Contract_Dir)
	FinanceInformation(Contract_Dir)

	bug_info = pd.read_excel('./data/ContractBugs.xls', sheet_name=[0], skiprows=0)
	finance_info = pd.read_excel('./data/func_type.xls', sheet_name=[0], skiprows=0)
	file = open('./data/aggre-info.json', 'w')
	file.close()

	GetKeywords()

	# Get contract vulnerability information
	for sheet, df in bug_info.items():
		for row in df.values:
			feature = []
			contract_name.append(GetName(row[0]))
			for i in range(1, len(row)):
				feature.append(row[i])
			features.append(feature)

	# Get contract financial information and contract type
	for sheet, df in finance_info.items():
		pos = 0
		for row in df.values:
			for i in range(1, len(row)):
				features[pos].append(row[i])

			# Get contract type
			features[pos].append(GetContractType(row[0]) + 1)
			pos += 1


	# print(contract_name)
	# print(features)

	seq = []
	level = 0
	name = ''
	# tree = open('./tools/data/Tree.txt', 'r')
	tree = open('./data/Tree.txt', 'r')
	lines = tree.readlines()
	for line in lines:

		# Root of recursion tree
		if 'Root' in line:
			seq = []
			name = GetName(line)
			seq.append(name)
			level = 0

		# Nodes of the recursive tree
		elif '(' in line:
			now_level = int(line[line.find('(') + 1])
			# print(now_level)
			gap = level - now_level + 1

			# print(gap)
			# print(seq)
			if gap > 0:
				AppendData(seq)
			for i in range(gap):
				if len(seq) > 0:
					seq.pop()
			seq.append(GetName(line))

			# print(seq)
			level = now_level

		# The traversal is complete and aggregate the information
		else:
			# print(data)
			AppendData(seq)
			with jsonlines.open('./data/aggre-info.json', 'a') as json_writer:
				json_writer.write(data)
			json_writer.close()
			data.clear()

	print("Aggregation information writing is complete!")
