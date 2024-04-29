import json
import jsonlines

# Find sequence vector maximum
def Detect(contract):
	m = 0
	for vec in contract.values():
		if m < sum(vec):
			m = sum(vec)
	return m

# Generate MCTS-input file
def Generate():
	"""
	# Train
	# Calculate the maximum
	with jsonlines.open('../data/aggre-info.json', 'r') as file:
		M = 0
		# Check each sequence
		for seq in file:
			# Check each Contract
			for contract in seq.values():
				Detect(contract)
				if M < Detect(contract):
					M = Detect(contract)

		print(M)
		file.close()
	
	ans = []
	# Build input data
	with jsonlines.open('../data/aggre-info.json', 'r') as file:
		for seq in file:
			for contract in seq.values():
				# Clear isolated contracts
				if len(contract) > 1:
					for name,vec in contract.items():
						score = sum(vec) / M
						# record = {name:vec, "score":score}
						record = {name: vec}
						ans.append(record)
		file.close()
	"""

	# Predict
	ans = []
	total = []
	# Build input data
	with jsonlines.open('./data/aggre-info.json', 'r') as file:
		for seq in file:
			tree = []
			for contract in seq.values():
				# Clear isolated contracts
				if len(contract) > 1:
					for name, vec in contract.items():
						record = {name: vec}
						tree.append(record)
						total.append(record)
			ans.append(tree)

		file.close()

	for n in range(len(ans)):
		if len(ans[n]) > 0:
			filename = ans[n][0].keys()
			with open('./MCFS/Input/' + str(filename)[12:-3], 'w') as f:
				json.dump(ans[n], f)
				f.close()
	with open('./data/MCFS-Input-Total', 'w') as f:
		json.dump(total, f)
		f.close()
