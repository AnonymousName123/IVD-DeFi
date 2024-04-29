import os
import numpy as np
from analyzer.detector.libs import split_function

# Here is the method for extracting security patterns of reentrancy.

def detectRE(filepath):

    # split all functions of contracts
    allFunctionList = split_function(filepath)  
    callValueList = []
    contents = []
    content = []

    for i in range(len(allFunctionList)):
        for j in range(len(allFunctionList[i])):
            text = allFunctionList[i][j]
            if 'onlyOwner' in text or 'require(owner' in text:
                break
            elif 'call.value' in text:
                content.append(text)
    contents = list(set(content))
    return contents
