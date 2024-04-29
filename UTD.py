import os
import json
import jsonlines
import pandas as pd
from scipy import spatial
from backtrack import locate

pma = []
total_sequences = ['ERC20', 'demo', 'Math', 'StdMath']
attack_mode = ['dta', 'fra', 'pla', 'pma', 'vmd']
attack_mode_name = {'dta': 'Deflationary Token Attack', 'fra': 'Flashloan Reentrancy Attack',
                     'pla': 'Privilege Leakage Attack', 'pma': 'Price Manipulation Attack', 
                     'vmd': 'Verification Mechanism Defects'}


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
                    keywords.append(FindKeywords(seq_features[pos_s: pos_s + offset], attack_features[pos_a: pos_a + offset]))

    return segment, keywords


# Match against protocol tree sequence and attack pattern library
def Match(seq, mode_a):
    fragment = []
    keywords = []
    seq_features = []
    seq_names = []
    mode_b = ''

    # Build name and character sequence
    for contract in seq.values():
        for feature in contract.values():
            seq_features.append(feature)
        for name in contract.keys():
            seq_names.append(name)

    if len(seq_names) >= 2:

        attack_features = []

        data = [json.loads(line) for line in open('./lib/' + mode_a + '.json', 'r', encoding='utf-8')]

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

            if pos + item[1] < len(seq_features):
                seq_features_b = seq_features[pos + item[1]]
                for mode in attack_mode:
                    if mode != mode_a:
                        attack_features_tmp = []

                        data = [json.loads(line) for line in open('./lib/' + mode + '.json', 'r', encoding='utf-8')]

                        # Build Attack feature Sequences
                        for line in data:
                            for features in line.values():
                                for feature in list(features.values()):
                                    attack_features_tmp.append(feature)

                        for pos_a in range(len(attack_features_tmp)):

                            # Verify that zero vectors exist
                            if Verify(attack_features_tmp[pos_a]) and Verify(seq_features_b):
                                if spatial.distance.cosine(attack_features_tmp[pos_a], seq_features_b) < 0.01:
                                    mode_b = mode
                                    item[1] += 1
                                    keywords.append(FindKeywords([seq_features_b], [attack_features_tmp[pos_a]]))

            for offset in range(item[1]):
                if pos + offset < len(seq_names):
                    record.append(seq_names[pos + offset])

            if record not in fragment:
                fragment.append(record)

    return fragment, keywords, mode_b


def UTD():
    report = ''

    with jsonlines.open('./data/aggre-info-opt.json', 'r') as file:

        num = 1

        # Check each sequence
        for seq in file:
            # Each attack mode
            for mode_a in attack_mode:

                # Check if the output is empty
                sequence, keywords, mode_b = Match(seq, mode_a)

                if mode_b != '':

                    for pos in range(len(sequence)):
                        attack_sequence = sequence[pos]
                        if attack_sequence not in total_sequences:
                            # print("Add: " + str(attack_sequence))
                            # print("Total: " + str(total_sequences))
                            total_sequences.append(attack_sequence)

                            # for num in range(len(sequence)):
                            report += 'Sequence ' + str(num) + ':'

                            for n in range(len(attack_sequence)):
                                if n != 0:
                                    report += '-'
                                report += attack_sequence[n]

                            report += '\n'
                            report += 'Attack Mode: ' + attack_mode_name[mode_a] + ' + ' + attack_mode_name[mode_b] + '\n'
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
