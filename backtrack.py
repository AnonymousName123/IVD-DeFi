import os
import pandas as pd

keywords = []
filter_words = ['msg', '"', 'menory', 'mantissa', 'REJECTION', 'emit', 'fail', 'mul_ScalarTruncateAddUInt']

# Check if it starts with a disabled word
def LineCheck(line):
    word = ''
    ban_word = ['for', 'import', 'return', 'while']
    for char in line:
        word += char
        if word in ban_word:
            return True
        elif char == ' ':
            if word == '':
                continue
            else:
                return False
    return False

# Capture function name
def GetFunctionName(line):
	name = ''
	start_pos = line.find('function') + 9
	end_pos = line.find('(')
	for pos in range(start_pos, end_pos):
		name += line[pos]
	return name

# Check if the function name contains keywords
def NameDetect(name):
	for type_words in keywords:
		for word in type_words:
			if pd.isna(word) == False and word in name.lower():
				return True
	return False

# Locate the position of the function and return a 2-tuple: function name, function start position
def FunctionLocate(contract):
	function_name = []
	strat_line = []

	for line_num in range(len(contract)):
		# filter irrelevant lines
		if '@' in contract[line_num] or LineCheck(contract[line_num]):
			continue

		if 'function' in contract[line_num]:
			name = GetFunctionName(contract[line_num])
			if NameDetect(name):
				function_name.append(name)
				strat_line.append(line_num + 1)
	return function_name, strat_line

# Detect if there is an external call
def InteractDetect(line, contract_name, sequence):
	for name in sequence:
		if name == contract_name:
			continue
		word = name + '.'
		if word.lower() in line.lower():
			return True
	return False

# Detect line information and return a triplet: whether there is interaction, keyword and pseudo-stack number
def LineDetect(line, contract_name, sequence):

	flag = InteractDetect(line, contract_name, sequence)
	words = []
	stack_num = 0

	# Use the pseudo-stack to determine whether the end of the function is reached
	for char in line:
		if char == '{':
			stack_num += 1
		elif char == '}':
			stack_num -= 1

	# Determine whether it is a valid row
	if (';' in line or 'if' in line) and '*' not in line:
		for type_words in keywords:
			for word in type_words:
				if pd.isna(word) == False and word in line.lower() and word not in filter_words:
					words.append(word)
	else:
		return flag, [], stack_num
	return flag, words, stack_num


def FunctionDetect(contract, function_name, strat_line, contract_name, sequence):

	answer = ''
	for function_num in range(len(function_name)):

		stack = 0
		is_interact = False
		line_num = strat_line[function_num] - 1
		nums = [] # Line number
		lines = [] # Line content
		words = [] # Line keywords

		while line_num - strat_line[function_num] < 1 or stack != 0:
			# "flag" indicates whether the row has interaction
			flag, word, stack_num = LineDetect(contract[line_num], contract_name, sequence)
			if flag == True:
				is_interact = True

			# If the function have associated keywords
			if len(word) != 0:
				nums.append(line_num)
				lines.append(contract[line_num])
				words.append(word)
			stack += stack_num
			line_num += 1

			# print(line_num)
			# print(contract[line_num])
			# print(stack)

			# To the end of the contract
			if line_num == len(function_name) or line_num == len(contract):
				break

		# print(function_name[function_num])
		# If there is an interaction, it is logged in a bug report
		if is_interact == True:
			answer += '    Function:' + function_name[function_num] + '\n'
			for num in range(len(words)):
				answer += ' ' * 8 + 'Line ' + str(nums[num] + 1) + ':' + lines[num]
				answer += ' ' * 8 + 'keywords:' + str(words[num]) + '\n' + '\n'

	return answer

# Backtracking to locate the vulnerability location
def locate(sequence, words):
	
	report = ''
	title = [['BlockNumber', 'DelegateCall', 'OverFlow', 'Reentrancy', 'TimeStamp', 'Unexpected Ether Balance', 'Permission', 'Hash', 'Liquidity Pool', 'Math and Variable', 'Oracle', 'Operate', 'Service', 'Token', 'Transaction'],
	['BN', 'DC', 'OF', 'RE', 'TS', 'UE', 'Ct', 'Hash', 'Lq', 'Math', 'Oc', 'Op', 'Sv', 'Tk', 'Tx']]
	# print(sequence)
	# print(words)

	data = pd.read_excel('./data/keyword.xls', sheet_name=[0], skiprows=0)

	# Build a related keyword library
	for sheet, df in data.items():
	    for row in df.values:
	    	if row[0] in words:
	    		# print(row[0])
		    	keyword = []
		    	for i in range(1, len(row)):
		    		keyword.append(row[i])
		    	keywords.append(keyword)

	# print(keywords)

	for contract_name in sequence:
		report += 'Contract: ' + contract_name + '\n'
		file = open('./contracts/' + contract_name + '.sol', 'r')
		contract = file.readlines()
		file.close()

		function_name, strat_line = FunctionLocate(contract)
		# print(function_name)
		# print(strat_line)
		report += FunctionDetect(contract, function_name, strat_line, contract_name, sequence)
		# print(report)
		
	return report