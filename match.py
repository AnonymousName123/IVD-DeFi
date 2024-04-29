import os
import json
import jsonlines
import pandas as pd
from scipy import spatial
from backtrack import locate

pma = []
total_sequences = ['ERC20', 'demo', 'Math', 'StdMath', 'AggregatorV3Interface', 'BoringERC20', 'SignedMath', 'WETH'] # openzeppelin

# Verify that it is a zero vector
def Verify(feature):
	pos = 0
	# Throw off call properties
	for pos in range(len(feature)):
		if feature[pos] != 0:
			break
	if pos + 1 == len(feature):
		return False
	else:
		return True

# Find similar keywords in a sequence
def FindKeywords(seq_features, attack_features):

	title = ['BN', 'DC', 'OF', 'RE', 'TS', 'UE', 'Ct', 'Hash', 'Lq', 'Math', 'Oc', 'Op', 'Sv', 'Tk', 'Tx', 'Call']
	keyword = []
	length = len(seq_features)

	for x in range(length):
		for y in range(len(seq_features[x])):

			# Corresponds to the maximum value of the relative element
			M = max(seq_features[x][y], attack_features[x][y])
			m = min(seq_features[x][y], attack_features[x][y])

			# If there is no zero value and the similarity conform to the threshold
			if m >= M * 0.5 and title[y] not in keyword and attack_features[x][y] != 0 and title[y] != 'Call':
				keyword.append(title[y])
	return keyword

def FindSim(seq_features, attack_features):
	segment = []
	keywords = []

	for pos_s in range(len(seq_features)):
		for pos_a in range(len(attack_features)):

			# Verify that zero vectors exist
			if Verify(attack_features[pos_a]) and Verify(seq_features[pos_s]):
				offset = 0
				while spatial.distance.cosine(attack_features[pos_a + offset], seq_features[pos_s + offset]) < 0.01:
					# print(seq_features[pos_s + offset])
					# print(attack_features[pos_a + offset])
					offset += 1
					if pos_a + offset == len(attack_features) or pos_s + offset == len(seq_features):
						break

				if offset != 0:
					segment.append([pos_s, offset])
					keywords.append(FindKeywords(seq_features[pos_s : pos_s + offset], attack_features[pos_a : pos_a + offset]))


				# cos_sim = 1 - spatial.distance.cosine(attack_features[pos_a], seq_features[pos_s])
				# Not enough similarity
				# if cos_sim > 0.99:
			# else:
				# print('There is a zero vector!')
			# 	break

			# The two sequences are similar
			# if offset == len(seq_features) - 1:
			# 	segment.append([pos, len(seq_features)])
			# 	keywords.append(FindKeywords(seq_features, attack_features[pos:len(attack_features)]))
	return segment, keywords

# Match against protocol tree sequence and attack pattern library
def Match(seq, mode):
	
	fragment = []
	seq_features = []
	seq_names = []

	# Build name and character sequence
	for contract in seq.values():
		for feature in contract.values():
			seq_features.append(feature)
		for name in contract.keys():
			seq_names.append(name)

	attack_features = []
	"""
	with open('./lib/' + mode + '.json', 'r') as file:
		data = json.loads(file.read())
		print(type(data))
	"""
	data = [json.loads(line) for line in open('./lib/' + mode + '.json', 'r', encoding='utf-8')]

	# Build Attack feature Sequences
	for line in data:
		for features in line.values():
			for feature in list(features.values()):
				attack_features.append(feature)

	segment, keywords = FindSim(seq_features, attack_features)

	# item[0] - initial position，item[1] - length
	for item in segment:
		pos = item[0]
		record = []

		# Ensure that the interface contract does not serve as the root node
		if seq_names[pos][0] == 'I':
			continue

		for offset in range(item[1]):
			record.append(seq_names[pos + offset])

		if record not in fragment:
			fragment.append(record)

	return fragment, keywords

def get_report():

	report = ''
	attack_mode = ['dta', 'fra', 'pla', 'pma', 'vmd']
	attack_mode_name = {'dta': 'Deflationary Token Attack', 'fra': 'Flashloan Reentrancy Attack', 'pla': 'Privilege Leakage Attack', 'pma': 'Price Manipulation Attack', 'vmd': 'Verification Mechanism Defects'}
	# attack_mode = ['frt', 'pla', 'pma', 'vmd']
	# attack_mode_name = {'frt': 'Front Running Transaction', 'pla': 'Privilege Leakage Attack', 'pma': 'Price Manipulation Attack', 'vmd': 'Verification Mechanism Defects'}

	# title_name = ['BlockNumber', 'DelegateCall', 'OverFlow', 'Reentrancy', 'TimeStamp', 'Unexpected Ether Balance', 'Permission', 'Hash', 'Liquidity Pool', 'Math and Variable', 'Oracle', 'Operate', 'Service', 'Token', 'Transaction']

	with jsonlines.open('./data/aggre-info-opt.json', 'r') as file:

		num = 1

		# Check each sequence
		for seq in file:
			# Each attack mode
			for mode in attack_mode:


				# Check if the output is empty
				sequence, keywords = Match(seq, mode)

				for pos in range(len(sequence)):
					attack_sequence = sequence[pos]
					if attack_sequence not in total_sequences:
						print("Add: " + str(attack_sequence))
						# print("Total: " + str(total_sequences))
						total_sequences.append(attack_sequence)

						# for num in range(len(sequence)):
						report += 'Sequence ' + str(num) + ':'

						for n in range(len(attack_sequence)):
							if n != 0:
								report += '-'
							report += attack_sequence[n]

						report += '\n'
						report += 'Attack Mode: ' + attack_mode_name[mode] + '\n'
						report += locate(attack_sequence, keywords[pos])
						report += 'Total Keywords: '
					
						for n in range(len(keywords[pos])):
							if n != 0:
								report += ', '
							report += keywords[pos][n]
						report += '\n'
						report += '\n'


	# print(report)
	file = open('./report.txt', 'w')
	file.write(report)
	file.close()
