import os
import json
import jsonlines

ans = []

def RepeatabilityCheck(seq):
    for i in range(len(seq) - 1):
        for j in range(i + 1, len(seq)):
            if seq[i] == seq[j]:
                return False
    return True

def SequenceCheck(seq, label):

    sequence = {}

    for pos in range(len(label) - len(seq) + 1):
        flag = False
        for num in range(len(seq)):
            name = str(label[pos + num].keys())[12:-3]
            # vec = label[pos + num].values()
            # name, vec = label[pos + num].items()
            if seq[num][:-4] != name:
                break

            if num == len(seq) - 1 and seq not in ans:
                flag = True
                ans.append(seq)

        if flag:
            for num in range(len(seq)):
                contract_name = str(label[pos + num].keys())[12:-3]
                contract_vec = list(label[pos + num].values())[0]

                sequence[contract_name] = contract_vec
            with jsonlines.open('./data/aggre-info-opt.json', 'a') as json_writer:
                json_writer.write({"1":sequence})
            json_writer.close()

def Output(data):

    with open('./data/MCFS-Input-Total', 'r') as json_data:
        label = json.load(json_data)
    # print(label)

    for seq in data:
        if RepeatabilityCheck(seq):
            SequenceCheck(seq, label)

   #  print(ans)
