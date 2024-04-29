import os
import pandas as pd
from analyzer.detector.pattern_BN import detectBN
from analyzer.detector.pattern_DC import detectDC
from analyzer.detector.pattern_TS import detectDS
from analyzer.detector.pattern_OF import detectOF
from analyzer.detector.pattern_RE import detectRE
from analyzer.detector.pattern_UE import detectUE

data = []
# Number of Vulnerability Types
type_num = 6

# Check if it starts with a disabled word
def LineCheck(line):

    word = ''
    ban_word = ['for', 'import', 'function', 'return', 'while', '/']

    for char in line:
        word += char

        if word in ban_word:
            return True

        elif char == ' ':
            # Skip spaces
            if word == '':
                continue
            # The first word is not a disabled word
            else:
                return False
    return False

# Filter comments and low-probability sentences
def Filter(err):

    for item in err:

        # Subscript offset after removal
        offset = 0

        for num in range(len(item)):
            if '@' in item[num - offset] or LineCheck(item[num - offset]):
                item.remove(item[num - offset])
                offset += 1

    # Returns filtered vulnerability results
    return err

def Detect(Contract_Dir):

    Contract_List = os.listdir(Contract_Dir)
    total_err = []
    for contract in Contract_List:

        # Vulnerability sentences
        err = []
        # Vulnerability type
        bugs = []

        print(contract)

        err.append(detectBN(Contract_Dir + contract))
        err.append(detectDC(Contract_Dir + contract))
        err.append(detectDS(Contract_Dir + contract))
        err.append(detectOF(Contract_Dir + contract))
        err.append(detectRE(Contract_Dir + contract))
        err.append(detectUE(Contract_Dir + contract))

        # Filter vulnerability sentences
        err = Filter(err)

        for i in range(type_num):
            if err[i] != []:
                # Number of vulnerabilities
                num = 0
                for j in err[i]:
                    num += 1
                bugs.append(num)
            else:
                bugs.append(0)
        data.append((contract, bugs[0], bugs[1], bugs[2], bugs[3], bugs[4], bugs[5]))
        total_err.append(err)
    return total_err

def Primary(Contract_Dir):

    Contract_List = os.listdir(Contract_Dir)
    bugs_name = ['BlockNumber', 'DelegateCall', 'OverFlow', 'Reentrancy', 'TimeStamp', 'Unexpected Ether Balance']
    err = Detect(Contract_Dir)


    # Build detail data
    contract_num = 0
    for contract in err:
        contract_detail = ''
        bug_num = 0

        # Build single vulnerability details  
        for bug in contract:
            bug_detail = ''
            for line in bug:
                bug_detail += line + '\n'
            if bug_detail != '':
                contract_detail += bugs_name[bug_num] + '\n' + bug_detail + '\n'
            bug_num += 1

        if contract_detail != '':
            file = open('./analyzer/detector/detail/' + Contract_List[contract_num][:-4] + '.txt', 'w')
            file.write(contract_detail)
            file.close()

        contract_num += 1

    # Vector information construction
    header = ['Contract_Name', 'BN', 'DC', 'OF', 'RE', 'TS', 'UE']
    df = pd.DataFrame(data, columns=header)

    writer = pd.ExcelWriter('./data/ContractBugs.xls')
    df.to_excel(writer, sheet_name='Sheet1', index=False)
    writer.close()


    